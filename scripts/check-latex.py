#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check-latex.py — 扫描 K12 skill 所有 .md 文件，检测 LaTeX 残留

用途：防止 G10（LaTeX 输出过度）复发
触发：每次修改 SKILL.md 或 references/ 后跑一次
用法：python check-latex.py [--dir PATH]

规则：
  - 扫描所有 .md 文件中的反斜杠命令
  - 白名单：markdown 语法
  - 报警：任何 \\command{...} 模式 -> [HIGH]
  - 报警：单独的 \\times \\div \\frac \\quad \\text \\left \\right -> [HIGH]
  - 允许：代码块内的 LaTeX（标记 [INFO]）
  - 允许：文档文件中的 LaTeX 引用（标记 [INFO]）
  - 允许：反引号内的 LaTeX 命令引用（标记 [INFO]）

退出码（C4 契约，供 CI/提交前门禁消费）：
  - 0 = 无 HIGH 级残留（PASS）
  - 1 = 发现 HIGH 级 LaTeX 残留
"""

import os
import re
import sys
import argparse

from _compat import setup_console
setup_console()

import json
from pathlib import Path


def _load_latex_commands():
    """LaTeX 命令黑名单（微信不渲染的）——数据源 references/latex-commands.json，
    与 diff-case.py 同源引用（D4 数据代码分离）。加载即校验，缺失即报错，
    不做静默兜底——守门工具的清单必须显式可追溯。"""
    path = Path(__file__).resolve().parent.parent / "references" / "latex-commands.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["commands"]


LATEX_COMMANDS = _load_latex_commands()

# 允许的反斜杠用法（markdown 语法，不是 LaTeX）
def _load_whitelist():
    """白名单配置（数据代码分离）——references/latex-whitelist.json。
    whitelist_patterns=允许的 markdown 转义（非 LaTeX）；docs_whitelist=讨论
    LaTeX 的文档（其中命令是教学内容）。加载即校验，缺失即报错。"""
    path = Path(__file__).resolve().parent.parent / "references" / "latex-whitelist.json"
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg["whitelist_patterns"], set(cfg["docs_whitelist"])


WHITELIST_PATTERNS, DOCS_WHITELIST = _load_whitelist()

# 命令匹配正则（C6 词边界 + C5 模块级预编译）：\div 不命中 \divide
COMMAND_RES = [(cmd, re.compile(re.escape(cmd) + r'(?![a-zA-Z])'))
               for cmd in LATEX_COMMANDS]
# 反引号 span（C5：每行只算一次，替代旧版每命令重扫整行）
BACKTICK_RE = re.compile(r'`[^`]*`')
# 围栏（C6：``` 与 ~~~ 均识别）
FENCE_RE = re.compile(r'^\s*(```|~~~)')

def scan_file(filepath):
    """扫描单个文件，返回告警列表"""
    alerts = []
    filename = os.path.basename(filepath)
    is_docs_file = filename in DOCS_WHITELIST
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return [(0, 'ERROR', f'无法读取文件: {e}')]

    in_code_block = False
    for i, line in enumerate(lines, 1):
        # 检测围栏边界（C6：``` 与 ~~~）
        if FENCE_RE.match(line):
            in_code_block = not in_code_block
            continue
        # C5：无反斜杠行快速跳过（40 个命令全以 \ 开头）
        if '\\' not in line:
            continue

        # C5：反引号 span 每行只算一次（供 is_in_backticks 复用）
        bt_spans = [m.span() for m in BACKTICK_RE.finditer(line)]

        for cmd, cmd_re in COMMAND_RES:
            for m in cmd_re.finditer(line):
                # 白名单命令级精确匹配（见 C1 修复注释）
                if cmd in WHITELIST_PATTERNS:
                    continue
                # 代码块内、文档文件内、反引号 span 内 → INFO（非实际残留）
                if (in_code_block or is_docs_file
                        or any(s <= m.start() < e for s, e in bt_spans)):
                    level = 'INFO'
                else:
                    level = 'HIGH'
                alerts.append((i, level, f'发现 LaTeX 命令 "{cmd}": {line.strip()[:80]}'))

    return alerts

def main():
    parser = argparse.ArgumentParser(description='检测 K12 skill 中的 LaTeX 残留')
    parser.add_argument('--dir', default='.', help='扫描目录（默认当前目录）')
    args = parser.parse_args()

    skill_dir = os.path.abspath(args.dir)
    md_files = []

    for root, dirs, files in os.walk(skill_dir):
        # C3：原地剪枝替代 root 子串判断——旧版 `if '.git' in root` 会误跳过
        # .github/ 等合法目录，且不剪枝导致 .git 内部成百上千文件被完整遍历
        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__'}]
        for f in files:
            if f.endswith('.md'):
                md_files.append(os.path.join(root, f))

    if not md_files:
        print(f'[WARN] 未找到 .md 文件: {skill_dir}')
        return

    total_alerts = 0
    high_alerts = 0
    info_count = 0

    for filepath in sorted(md_files):
        rel_path = os.path.relpath(filepath, skill_dir)
        alerts = scan_file(filepath)
        if alerts:
            print(f'\n{"="*60}')
            print(f'文件: {rel_path}')
            print(f'{"="*60}')
            for line_num, level, msg in alerts:
                icon = '[!]' if level == 'HIGH' else '[i]'
                print(f'  {icon} 行 {line_num} [{level}] {msg}')
                total_alerts += 1
                if level == 'HIGH':
                    high_alerts += 1
                else:
                    info_count += 1

    print(f'\n{"="*60}')
    print(f'扫描完成: {len(md_files)} 个文件, {total_alerts} 个告警')
    print(f'  [HIGH]: {high_alerts}  (需要修复)')
    print(f'  [INFO]: {info_count}  (代码块内, 可忽略)')
    if high_alerts == 0:
        print('\n[PASS] 无 LaTeX 残留，G10 防线通过！')
    else:
        print(f'\n[WARN] 发现 {high_alerts} 个 HIGH 级别 LaTeX 残留，请手动替换为 Unicode 符号')
        print('   替换表: \\times -> x  \\div -> /  \\leq -> <=  \\geq -> >=  \\neq -> !=  \\frac{a}{b} -> a/b')

    # 退出码契约（C4）：让 CI/提交前门禁能感知失败——旧版 HIGH>0 也 exit 0
    sys.exit(1 if high_alerts else 0)

if __name__ == '__main__':
    main()
