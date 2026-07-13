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
import argparse

# Windows GBK 终端兼容
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 方法论关键词
METHODOLOGY_KEYWORDS = {
    '胡小群': ['算理', '三个什么', '公式三重', '先好再快', '巧算', '吃透'],
    '昍爸': ['苏格拉底', '六大思维', '化抽象为具象', '有序枚举', '逆向', '递归', '整体', '对称', '疑问', '框架'],
    '子贤': ['情绪翻译机', '彩虹夸夸', '十步沟通', '积极复盘', '754', '名词扫描', '教练式'],
    '塞利格曼': ['3P', 'ABCDE', '永久性', '普遍性', '个人化', '表现满意', '感觉满意', 'H=S+C+V', 'ACR', '乐观式批评'],
}

# 六合一关键词
SIX_IN_ONE = ['题目解析', '一题多解', '难点预判', '引导脚本', '知识脉络', '延伸练习']

# 情绪预判关键词
EMOTION_KEYWORDS = ['情绪', '畏难', '急躁', '焦虑', '崩溃', '恐惧', '烦躁', '放弃', '轻敌', '自我否定']

def parse_file(filepath):
    """读取文件内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f'[ERROR] 读取文件失败: {filepath} - {e}')
        return ''

def analyze_content(text):
    """分析单个辅导内容"""
    result = {
        '方法论引用': {},
        '六合一覆盖': [],
        '情绪预判关键词': [],
        '知识脉络学段': [],
        '字数': len(text),
        '有LaTeX': bool(re.search(r'\\(times|div|frac|quad|leq|geq)', text)),
        '有双发': '精简版' in text or '完整版' in text or 'HTML' in text,
    }

    # 方法论引用统计
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

    # 知识脉络学段（简单匹配）
    grade_patterns = [r'一[上下]', r'二[上下]', r'三[上下]', r'四[上下]', r'五[上下]', r'六[上下]', r'初一', r'初二', r'高一']
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

    # 6. 双发合规
    print(f'\n{"─"*40}')
    print('6. 微信双发合规')
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='对比两次同类型题辅导输出的方法论偏离')
    parser.add_argument('file1', help='第一次辅导输出文件')
    parser.add_argument('file2', help='第二次辅导输出文件')
    args = parser.parse_args()

    text1 = parse_file(args.file1)
    text2 = parse_file(args.file2)

    if not text1 or not text2:
        sys.exit(1)

    a1 = analyze_content(text1)
    a2 = analyze_content(text2)

    diff_analysis(a1, a2, args.file1, args.file2)
