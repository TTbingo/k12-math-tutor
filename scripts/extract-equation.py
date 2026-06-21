#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract-equation.py — 从试卷图片中提取数学题，自动识别算理考点

用途：辅助家长拍照上传试卷 -> 自动识别题目类型和算理考点
触发：家长发来试卷图片时辅助使用
用法：python extract-equation.py <image_path>
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

# 算理考点匹配表（关键词 → 考点 → 对应方法论）
ARITHMETIC_PATTERNS = {
    # 计算类
    '除法': {'考点': '算理优先（为什么这样除）', '方法论': '胡小群 §三个什么', '年级': '2-5'},
    '竖式': {'考点': '竖式背后的分配律', '方法论': '胡小群 §公式三重境界', '年级': '3-5'},
    '乘法': {'考点': '乘法意义（几个几）', '方法论': '胡小群 §算理优先', '年级': '2-4'},
    '分数': {'考点': '分数的意义/运算', '方法论': '昍爸 §化抽象为具象', '年级': '4-6'},
    '小数': {'考点': '小数与分数的关系', '方法论': '胡小群 §小初高一体化', '年级': '4-6'},
    '余数': {'考点': '有余数除法的意义', '方法论': '胡小群 §算理优先', '年级': '2-4'},

    # 应用题类
    '鸡兔同笼': {'考点': '假设法', '方法论': '昍爸 §六大思维之逆向', '年级': '4-5'},
    '行程': {'考点': '速度×时间=路程', '方法论': '昍爸 §化抽象为具象', '年级': '4-6'},
    '相遇': {'考点': '速度叠加', '方法论': '昍爸 §生活场景数学化', '年级': '4-6'},
    '工程': {'考点': '归一思想（总工程=1）', '方法论': '胡小群 §归一', '年级': '6'},
    '归一': {'考点': '先求每份数', '方法论': '胡小群 §归一', '年级': '3-4'},
    '和差': {'考点': '线段图', '方法论': '昍爸 §化抽象为具象', '年级': '3-4'},
    '比例': {'考点': '比例关系', '方法论': '胡小群 §小初高一体化', '年级': '6-初一'},

    # 几何类
    '面积': {'考点': '面积公式推导', '方法论': '昍爸 §化抽象为具象', '年级': '3-6'},
    '周长': {'考点': '周长概念', '方法论': '昍爸 §化抽象为具象', '年级': '3-4'},
    '三角形': {'考点': '三角形性质', '方法论': '昍爸 §几何辅助线', '年级': '4-初一'},
    '正方形': {'考点': '正方形性质', '方法论': '昍爸 §化抽象为具象', '年级': '3-5'},
    '长方体': {'考点': '三维展开', '方法论': '昍爸 §化抽象为具象', '年级': '5'},
    '圆': {'考点': '圆面积/周长', '方法论': '昍爸 §极限雏形', '年级': '6'},

    # 代数类
    '方程': {'考点': '字母表示数→解方程', '方法论': '胡小群 §小初高一体化', '年级': '5-初一'},
    '未知数': {'考点': '设未知数', '方法论': '胡小群 §小初高一体化', '年级': '5-初一'},
    '看错': {'考点': '差量分析（消不变量）', '方法论': '昍爸 §六大思维之逆向', '年级': '4-6'},

    # 情绪/心理类
    '考砸': {'考点': '3P诊断+ABCDE', '方法论': '塞利格曼 §ABCDE', '年级': '全'},
    '不会': {'考点': '情绪翻译机', '方法论': '子贤 §情绪翻译机', '年级': '全'},
    '笨': {'考点': '永久性悲观→ABCDE', '方法论': '塞利格曼 §3P', '年级': '全'},
}

def analyze_text(text):
    """从识别文本中匹配算理考点"""
    matches = []
    for keyword, info in ARITHMETIC_PATTERNS.items():
        if keyword in text:
            matches.append({
                '关键词': keyword,
                '考点': info['考点'],
                '方法论': info['方法论'],
                '年级': info['年级'],
            })
    return matches

def main():
    parser = argparse.ArgumentParser(description='从试卷图片提取数学题+识别算理考点')
    parser.add_argument('image', nargs='?', help='试卷图片路径')
    parser.add_argument('--text', help='直接传入 OCR 识别后的文本')
    args = parser.parse_args()

    print('=' * 60)
    print('K12 数学题算理考点识别工具')
    print('=' * 60)

    # 如果直接传入文本
    if args.text:
        print(f'\n输入文本: {args.text[:100]}...')
        matches = analyze_text(args.text)
        print_results(matches)
        return

    if not args.image:
        print('\n用法:')
        print('  python extract-equation.py <图片路径>     # 图片模式（需 OCR）')
        print('  python extract-equation.py --text "题目文本"  # 文本模式')
        print('\n算理考点匹配表（共 {} 条）:'.format(len(ARITHMETIC_PATTERNS)))
        for k, v in ARITHMETIC_PATTERNS.items():
            print(f'  {k:8s} → {v["考点"]:20s} | {v["方法论"]:20s} | {v["年级"]}')
        return

    # 图片模式
    image_path = os.path.abspath(args.image)
    if not os.path.exists(image_path):
        print(f'[ERROR] 文件不存在: {image_path}')
        return

    print(f'\n图片: {image_path}')
    print(f'大小: {os.path.getsize(image_path)} bytes')

    # 尝试 PIL 预处理
    try:
        from PIL import Image
        img = Image.open(image_path)
        print(f'尺寸: {img.size}')
        print(f'模式: {img.mode}')

        # 基本预处理建议
        print('\n[预处理建议]')
        if img.mode != 'L':
            print('  - 建议转为灰度: img.convert("L")')
        w, h = img.size
        if w < 1000 or h < 1000:
            print(f'  - 建议放大: 当前 {w}x{h} → 放大到 2000+ 宽度提升 OCR 精度')
        if w > 3000:
            print(f'  - 建议缩小: 当前 {w}x{h} → 缩到 2000-3000 宽度')
        print('  - 建议二值化: threshold=128')
        print('  - 建议去噪: median_filter(size=3)')

    except ImportError:
        print('\n[WARN] 未安装 Pillow，跳过图片预处理')
        print('  安装: pip install Pillow')

    # OCR 部分（框架）
    print('\n[OCR 识别]')
    print('  当前版本不内置 OCR 引擎。请使用以下方式之一：')
    print('  1. 微信图片转文字')
    print('  2. 在线 OCR 服务')
    print('  3. 识别后用 --text 参数传入本工具分析考点')
    print('\n  示例:')
    print('  python extract-equation.py --text "小华在计算除法时把除数7看成了9"')

    print('\n' + '=' * 60)

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
