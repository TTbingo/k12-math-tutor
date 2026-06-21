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
"""

import os
import re
import sys
import argparse

# Windows GBK 终端兼容
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# LaTeX 命令黑名单（微信不渲染的）
LATEX_COMMANDS = [
    r'\frac', r'\times', r'\div', r'\quad', r'\text', r'\left', r'\right',
    r'\sqrt', r'\pi', r'\alpha', r'\beta', r'\theta', r'\sum', r'\prod',
    r'\leq', r'\geq', r'\neq', r'\approx', r'\equiv', r'\pm', r'\mp',
    r'\cdot', r'\cdots', r'\ldots', r'\infty', r'\partial', r'\nabla',
    r'\angle', r'\triangle', r'\circ', r'\perp', r'\parallel',
    r'\begin', r'\end', r'\matrix', r'\vec', r'\overline', r'\underline',
    r'\hat', r'\bar', r'\dot', r'\ddot',
]

# 允许的反斜杠用法（markdown 语法，不是 LaTeX）
WHITELIST_PATTERNS = [
    r'\\n',  # 换行（代码中）
    r'\\t',
    r'\\r',
    r'\\\|',  # 表格管道转义
]

def scan_file(filepath):
    """扫描单个文件，返回告警列表"""
    alerts = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return [(0, 'ERROR', f'无法读取文件: {e}')]

    in_code_block = False
    for i, line in enumerate(lines, 1):
        # 检测代码块边界
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue

        for cmd in LATEX_COMMANDS:
            if cmd in line:
                # 代码块内只标记 INFO
                level = 'INFO' if in_code_block else 'HIGH'
                # 检查是否在白名单中
                is_whitelisted = any(w in line for w in WHITELIST_PATTERNS)
                if not is_whitelisted or cmd not in [r'\n', r'\t']:
                    alerts.append((i, level, f'发现 LaTeX 命令 "{cmd}": {line.strip()[:80]}'))

    return alerts

def main():
    parser = argparse.ArgumentParser(description='检测 K12 skill 中的 LaTeX 残留')
    parser.add_argument('--dir', default='.', help='扫描目录（默认当前目录）')
    args = parser.parse_args()

    skill_dir = os.path.abspath(args.dir)
    md_files = []

    for root, dirs, files in os.walk(skill_dir):
        # 跳过 .git 目录
        if '.git' in root:
            continue
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

if __name__ == '__main__':
    main()
