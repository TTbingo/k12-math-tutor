#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diff-case.py — 对比两次同类型题的辅导输出，标出方法论偏离

用途：辅助飞轮——发现"同一类题两次辅导走了不同方法论"的情况
触发：月度回顾 / P3 定期回顾时
用法：python diff-case.py <file1> <file2>
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

from _compat import setup_console
setup_console()

def _load_keywords():
    """方法论/六合一/情绪关键词表（数据代码分离）——references/diff-case-keywords.json。
    methodology 按"命中种数"统计（非引用频次，见 D2 注释）；加载即校验，缺失即报错。"""
    path = Path(__file__).resolve().parent.parent / "references" / "diff-case-keywords.json"
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg["methodology"], cfg["six_in_one"], cfg["emotion"]


METHODOLOGY_KEYWORDS, SIX_IN_ONE, EMOTION_KEYWORDS = _load_keywords()


def _load_latex_pattern():
    """D4：LaTeX 命令黑名单与 check-latex.py 同源（references/latex-commands.json），
    消除两份清单的逻辑分叉。加载即校验，缺失即报错——不做静默兜底，
    兜底会让清单分叉在 JSON 丢失时悄悄复活。"""
    path = Path(__file__).resolve().parent.parent / "references" / "latex-commands.json"
    with open(path, encoding="utf-8") as f:
        cmds = json.load(f)["commands"]
    return re.compile("|".join(re.escape(c) for c in cmds))


_LATEX_RE = _load_latex_pattern()

def parse_file(filepath):
    """读取文件内容（D6：utf-8 失败回退 gb18030，再失败返回 None）"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='gb18030') as f:
                return f.read()
        except Exception as e:
            print(f'[ERROR] 读取文件失败: {filepath} - {e}')
            return None
    except Exception as e:
        print(f'[ERROR] 读取文件失败: {filepath} - {e}')
        return None

def analyze_content(text):
    """分析单个辅导内容"""
    result = {
        '方法论引用': {},
        '六合一覆盖': [],
        '情绪预判关键词': [],
        '知识脉络学段': [],
        '字数': len(text),
        '有LaTeX': bool(_LATEX_RE.search(text)),
        # D3：仅文本启发式——任何提到"HTML/精简版"字样的文本（含讨论规则的记录）
        # 都会命中，不代表真实送达行为。真实合规需查附件清单/发送日志等证据源
        '有双发': '精简版' in text or '完整版' in text or 'HTML' in text,
    }

    # D2：统计"命中关键词种数"（旧字段名"方法论引用"暗示引用频次，语义不符）
    for method, keywords in METHODOLOGY_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text)
        if count > 0:
            result['方法论引用'][method] = count

    # 六合一覆盖
    for item in SIX_IN_ONE:
        if item in text:
            result['六合一覆盖'].append(item)

    # 情绪预判
    for kw in EMOTION_KEYWORDS:
        if kw in text:
            result['情绪预判关键词'].append(kw)

    # 知识脉络学段（启发式匹配，三级模式）
    #  1) 明确锚点：三年级上 / 四年级下册 —— 零歧义
    #  2) 裸缩写（三上/五下）：排除动词/成语语境，旧版 r'一[上下]' 会把"看一下/统一上面"
    #     "低三下四/三下五除二/四下张望"全部计入学段，几乎每篇辅导文本都被污染
    #  3) 初/高中：初一二三、高一二三（旧版漏初三、高二、高三）
    grade_patterns = [
        r'[一二三四五六]年级[上下](?:册|学期)?',
        r'(?<![看想试统点碰算数讲说听读写问答查搜比量称估猜验记画圈改做在低练习固顾论流来去])[一二三四五六][上下](?!张望|五除二)',
        r'初[一二三]|高[一二三]',
    ]
    for pattern in grade_patterns:
        matches = re.findall(pattern, text)
        if matches:
            result['知识脉络学段'].extend(list(set(matches)))

    return result

def diff_analysis(analysis1, analysis2, file1, file2):
    """对比两个分析结果"""
    print('=' * 60)
    print('两次辅导方法论偏离对比')
    print('=' * 60)

    print(f'\n文件 1: {os.path.basename(file1)} ({analysis1["字数"]} 字)')
    print(f'文件 2: {os.path.basename(file2)} ({analysis2["字数"]} 字)')

    # 1. 方法论引用对比
    print(f'\n{"─"*40}')
    print('1. 方法论引用对比')
    print(f'{"─"*40}')
    all_methods = set(list(analysis1['方法论引用'].keys()) + list(analysis2['方法论引用'].keys()))
    if not all_methods:
        print('  [WARN] 两次辅导均未检测到方法论关键词')
    else:
        print(f'  {"方法论":8s} | {"文件1":6s} | {"文件2":6s} | 偏离')
        print(f'  {"─"*40}')
        for m in sorted(all_methods):
            c1 = analysis1['方法论引用'].get(m, 0)
            c2 = analysis2['方法论引用'].get(m, 0)
            diff = '[!] 偏离' if c1 != c2 else '[OK] 一致'
            print(f'  {m:8s} | {c1:6d} | {c2:6d} | {diff}')

    # 2. 六合一覆盖对比
    print(f'\n{"─"*40}')
    print('2. 六合一覆盖对比')
    print(f'{"─"*40}')
    s1 = set(analysis1['六合一覆盖'])
    s2 = set(analysis2['六合一覆盖'])
    missing1 = set(SIX_IN_ONE) - s1
    missing2 = set(SIX_IN_ONE) - s2
    print(f'  文件1 覆盖: {len(s1)}/6 {"[OK]" if not missing1 else "[!] 缺: " + ", ".join(missing1)}')
    print(f'  文件2 覆盖: {len(s2)}/6 {"[OK]" if not missing2 else "[!] 缺: " + ", ".join(missing2)}')

    # 3. 情绪预判对比
    print(f'\n{"─"*40}')
    print('3. 情绪预判对比')
    print(f'{"─"*40}')
    e1 = analysis1['情绪预判关键词']
    e2 = analysis2['情绪预判关键词']
    print(f'  文件1: {len(e1)} 个 ({", ".join(e1) if e1 else "无"})')
    print(f'  文件2: {len(e2)} 个 ({", ".join(e2) if e2 else "无"})')
    if len(e1) != len(e2):
        print(f'  [!] 情绪预判数量不一致（差 {abs(len(e1)-len(e2))} 个）')

    # 4. 知识脉络学段数
    print(f'\n{"─"*40}')
    print('4. 知识脉络学段覆盖')
    print(f'{"─"*40}')
    g1 = analysis1['知识脉络学段']
    g2 = analysis2['知识脉络学段']
    print(f'  文件1: {len(g1)} 个学段 ({", ".join(g1) if g1 else "无"})')
    print(f'  文件2: {len(g2)} 个学段 ({", ".join(g2) if g2 else "无"})')
    if abs(len(g1) - len(g2)) >= 2:
        print(f'  [!] 学段覆盖差异 >= 2，可能方法论偏离')

    # 5. LaTeX 合规
    print(f'\n{"─"*40}')
    print('5. LaTeX 合规检查')
    print(f'{"─"*40}')
    print(f'  文件1: {"[!] 有LaTeX残留" if analysis1["有LaTeX"] else "[OK] 无LaTeX"}')
    print(f'  文件2: {"[!] 有LaTeX残留" if analysis2["有LaTeX"] else "[OK] 无LaTeX"}')

    # 6. 双发合规（D3：仅文本启发式，不代表真实送达）
    print(f'\n{"─"*40}')
    print('6. 微信双发合规（仅文本启发式，不代表真实送达）')
    print(f'{"─"*40}')
    print(f'  文件1: {"[OK] 有双发标记" if analysis1["有双发"] else "[!] 无双发标记"}')
    print(f'  文件2: {"[OK] 有双发标记" if analysis2["有双发"] else "[!] 无双发标记"}')

    # 总结
    print(f'\n{"="*60}')
    deviations = 0
    if analysis1['方法论引用'] != analysis2['方法论引用']:
        deviations += 1
    if missing1 or missing2:
        deviations += 1
    if abs(len(e1) - len(e2)) >= 2:
        deviations += 1
    if abs(len(g1) - len(g2)) >= 2:
        deviations += 1
    if analysis1['有LaTeX'] or analysis2['有LaTeX']:
        deviations += 1

    if deviations == 0:
        print(f'[OK] 两次辅导方法论一致性良好，无明显偏离')
    else:
        print(f'[!] 发现 {deviations} 处方法论偏离，建议检查是否需要追加 gotcha')

    print(f'\n建议:')
    print(f'  - 偏离 ≥ 2 处 → 追加 G 编号到 references/gotchas.md 飞轮追加区')
    print(f'  - 偏离 = 1 处 → 记录到 references/tutor-log.md 待观察')
    print(f'  - 偏离 = 0 处 → 方法论稳定，无需动作')

    return deviations

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='对比两次同类型题辅导输出的方法论偏离')
    parser.add_argument('file1', help='第一次辅导输出文件')
    parser.add_argument('file2', help='第二次辅导输出文件')
    args = parser.parse_args()

    # D6：file1 == file2 无意义自比较（恒"一致"），拒绝并提示
    if os.path.exists(args.file1) and os.path.exists(args.file2) and \
            os.path.samefile(args.file1, args.file2):
        print('[ERROR] file1 与 file2 是同一文件，自比较无意义')
        sys.exit(2)

    text1 = parse_file(args.file1)
    text2 = parse_file(args.file2)

    # D6：读取失败 exit 2（工具自身错误），区别于"发现偏离"的 exit 1
    if text1 is None or text2 is None:
        sys.exit(2)
    if not text1 or not text2:
        sys.exit(1)

    a1 = analyze_content(text1)
    a2 = analyze_content(text2)

    deviations = diff_analysis(a1, a2, args.file1, args.file2)

    # D6：退出码契约（0=一致，1=发现偏离 ≥2 处需追 gotcha，2=工具自身错误）
    sys.exit(1 if deviations >= 2 else 0)
