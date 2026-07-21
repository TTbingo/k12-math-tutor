#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_compat.py — K12 scripts 共享兼容层（X1）

5 个脚本头部曾各自复制同一段 sys.stdout.reconfigure 样板（其中
validate-structure.py 还曾漏写 try/except 而分叉）。抽出统一入口，
各脚本一行调用：

    from _compat import setup_console
    setup_console()
"""
import sys


def setup_console():
    """Windows GBK 终端兼容：stdout 强制 UTF-8。

    stdout 被重定向为非文本流时 reconfigure 抛 AttributeError（S4），
    此处统一吞掉——终端显示错误不应让工具崩溃。
    """
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
