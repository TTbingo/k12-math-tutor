# -*- coding: utf-8 -*-
"""k12-math-tutor scripts 测试套件共享配置。"""
import sys
from pathlib import Path

# 与被测脚本同级导入：scripts/tests/ 的上一级即 scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SCRIPTS = Path(__file__).resolve().parent.parent
