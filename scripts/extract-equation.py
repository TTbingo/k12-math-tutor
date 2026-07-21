#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract-equation.py — K12 算理考点匹配工具（文本模式）

用途：输入题目文本（OCR 识别结果或手动输入），自动匹配算理考点 + 方法论 + 适用年级
触发：家长发来题目文本时辅助使用
用法：python extract-equation.py --text "题目文本"

说明（E1 正名）：本工具只做"文本 → 考点匹配"。图片 OCR 模式未实现——
传入图片路径时仅打印引导提示并退出，不做任何识别。
旧版 docstring 宣称"从试卷图片中提取数学题"，名不符实，已修正。
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

from _compat import setup_console
setup_console()


def _load_patterns():
    """E6：匹配表抽到 references/arithmetic-patterns.json，数据与代码解耦。
    加载时校验字段完整性（考点/方法论/年级必填）。"""
    path = Path(__file__).resolve().parent.parent / "references" / "arithmetic-patterns.json"
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    table = {k: v for k, v in raw.items() if not k.startswith("_")}
    for k, v in table.items():
        for field in ("考点", "方法论", "年级"):
            if field not in v:
                raise ValueError(f"arithmetic-patterns.json 条目 '{k}' 缺字段 '{field}'")
    return table


ARITHMETIC_PATTERNS = _load_patterns()

# E2：情绪类关键词的上下文触发条件——题干叙述（"小明不会算"）不应误触情绪
# 方法论。触发条件：伴随第一人称主语"我"，或位于句首/独立短句（前无名词主语）。
_FIRST_PERSON = ('我', '孩子', '娃')
_SUBJECT_CHARS = '小明华李张王赵同学他她你'


def _emotion_triggered(keyword, text):
    """情绪词仅当疑似真实情绪表达时才命中。"""
    for m in re.finditer(re.escape(keyword), text):
        start = m.start()
        # 句首或紧邻标点（独立短句开头）
        if start == 0 or text[start - 1] in '，。！？；、\n':
            return True
        # 前文 6 字内含第一人称主语
        ctx = text[max(0, start - 6):start]
        if any(p in ctx for p in _FIRST_PERSON):
            return True
        # 前文紧邻第三人称题目主语（小明/小华等）→ 题干叙述，不触发
    return False


def analyze_text(text):
    """从识别文本中匹配算理考点。

    E2：情绪类关键词加上下文触发条件；命中按关键词长度降序去重，
    同族考点只保留最具体一条（如"圆的面积"命中后不再报"面积"泛化项）。
    """
    hits = []
    for keyword, info in ARITHMETIC_PATTERNS.items():
        if keyword not in text:
            continue
        if info.get("情绪") and not _emotion_triggered(keyword, text):
            continue
        hits.append({
            '关键词': keyword,
            '考点': info['考点'],
            '方法论': info['方法论'],
            '年级': info['年级'],
        })
    # 按关键词长度降序；若长词的文本区间完全覆盖短词，则短词是同族泛化项，去重
    hits.sort(key=lambda h: -len(h['关键词']))
    kept = []
    for h in hits:
        kw = h['关键词']
        absorbed = False
        for longer in kept:
            lk = longer['关键词']
            # 短词是长词的子串，且两者命中的是同一处文本 → 泛化项被吸收
            if kw != lk and kw in lk:
                absorbed = True
                break
        if not absorbed:
            kept.append(h)
    return kept

def main():
    parser = argparse.ArgumentParser(description='K12 算理考点匹配（文本模式；图片 OCR 未实现）')
    parser.add_argument('image', nargs='?', help='试卷图片路径')
    parser.add_argument('--text', help='直接传入 OCR 识别后的文本')
    args = parser.parse_args()

    print('=' * 60)
    print('K12 数学题算理考点识别工具')
    print('=' * 60)

    # E4：--text 与 image 同传时 image 被静默忽略——显式 WARN 提示互斥
    if args.text and args.image:
        print(f'[WARN] --text 与图片路径同时传入，图片参数 "{args.image}" 被忽略（互斥，优先 --text）')

    # 如果直接传入文本
    if args.text:
        print(f'\n输入文本: {args.text[:100]}...')
        matches = analyze_text(args.text)
        print_results(matches)
        return

    if not args.image:
        print('\n用法:')
        print('  python extract-equation.py --text "题目文本"  # 文本模式（可用）')
        print('  python extract-equation.py <图片路径>       # 图片模式（未实现，仅提示）')
        print('\n算理考点匹配表（共 {} 条）:'.format(len(ARITHMETIC_PATTERNS)))
        for k, v in ARITHMETIC_PATTERNS.items():
            print(f'  {k:8s} → {v["考点"]:20s} | {v["方法论"]:20s} | {v["年级"]}')
        return

    # 图片模式：OCR 链路未实现（E1 正名）——旧版只打印预处理建议后结束，
    # 无任何提取却宣称"提取"，名不符实。显式声明未实现并引导 --text。
    image_path = os.path.abspath(args.image)
    if not os.path.exists(image_path):
        print(f'[ERROR] 文件不存在: {image_path}')
        sys.exit(1)

    print(f'\n[NOT IMPLEMENTED] 图片 OCR 模式未实现: {image_path}')
    print('  本工具仅支持文本模式。请先用微信"图片转文字"或在线 OCR 识别题目，')
    print('  再把识别文本传入:')
    print('  python extract-equation.py --text "识别后的题目文本"')
    sys.exit(1)

def print_results(matches):
    """打印匹配结果"""
    if not matches:
        print('\n[INFO] 未匹配到已知算理考点')
        print('  可能原因: 题目类型不在匹配表中，或 OCR 文本不完整')
        print('  建议: 手动查 references/methodology-*.md 头部「快速调用矩阵」')
        return

    print(f'\n匹配到 {len(matches)} 个算理考点:\n')
    print(f'{"关键词":8s} | {"考点":20s} | {"方法论":20s} | {"年级"}')
    print('-' * 60)
    for m in matches:
        print(f'{m["关键词"]:8s} | {m["考点"]:20s} | {m["方法论"]:20s} | {m["年级"]}')

    print(f'\n建议:')
    print(f'  1. 查方法论文件: references/ 目录下对应文件')
    print(f'  2. 查约束卡片: references/constraints-quick-ref.md')
    print(f'  3. 查案例: references/case-studies.md')

if __name__ == '__main__':
    main()
