# -*- coding: utf-8 -*-
"""diff-case.py 测试：D1 学段 + D3 双发标注 + D6 健壮性（部分 xfail）。"""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SCRIPT = Path(__file__).resolve().parent.parent / "diff-case.py"

import importlib.util
spec = importlib.util.spec_from_file_location("diff_case", SCRIPT)
diff_case = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diff_case)


SIX = "题目解析 一题多解 难点预判 引导脚本 知识脉络 延伸练习"


def write(d, name, text):
    p = d / name
    p.write_text(text, encoding="utf-8")
    return str(p)


# ── 正常流程 ──────────────────────────────────────────────
def test_identical_files_zero_deviation(tmp_path):
    a = write(tmp_path, "a.txt", SIX)
    b = write(tmp_path, "b.txt", SIX)
    r = subprocess.run([sys.executable, str(SCRIPT), a, b], capture_output=True, text=True)
    assert "一致性良好" in r.stdout


# ── D1 钉住：学段零命中 / 真学段识别 ─────────────────────
@pytest.mark.parametrize("text", [
    "我们看一下这道题，先统一上面的条件，再算一下结果",
    "复习一下这节课，再讨论一下",
    "他心里七上八下，低三下四不是三下五除二，也不要四下张望",
])
def test_d1_no_false_grade(text):
    assert diff_case.analyze_content(text)["知识脉络学段"] == []

def test_d1_real_grades():
    got = diff_case.analyze_content("三年级上册的乘法，初一衔接，初三冲刺")["知识脉络学段"]
    assert any("三年级上" in g for g in got) and "初一" in got and "初三" in got


# ── D3 钉住：双发指标标注启发式 ──────────────────────────
def test_d3_heuristic_label(tmp_path):
    a = write(tmp_path, "a.txt", SIX + " 精简版")
    b = write(tmp_path, "b.txt", SIX)
    r = subprocess.run([sys.executable, str(SCRIPT), a, b], capture_output=True, text=True)
    assert "仅文本启发式" in r.stdout


# ── P3 修复后回归（D2/D6 已修） ──────────────────────────
def test_d2_number_754_not_zixian():
    assert "子贤" not in diff_case.analyze_content("计算 754+246 的结果")["方法论引用"]

def test_d6_gbk_fallback(tmp_path):
    (tmp_path / "g.txt").write_bytes(SIX.encode("gbk"))
    b = write(tmp_path, "b.txt", SIX)
    r = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path / "g.txt"), b],
                       capture_output=True, text=True)
    assert r.returncode == 0

def test_d6_same_file_rejected(tmp_path):
    a = write(tmp_path, "a.txt", SIX)
    r = subprocess.run([sys.executable, str(SCRIPT), a, a], capture_output=True, text=True)
    assert r.returncode == 2

def test_d6_deviation_exit_code(tmp_path):
    a = write(tmp_path, "a.txt", SIX + " 算理 三个什么 一年级上 二年级下 三年级上 四年级下")
    b = write(tmp_path, "b.txt", SIX + " 一年级上")
    r = subprocess.run([sys.executable, str(SCRIPT), a, b], capture_output=True, text=True)
    assert r.returncode == 1  # 偏离 ≥2 处 → exit 1

def test_d5_no_double_count(tmp_path):
    a = write(tmp_path, "a.txt", SIX + " 情绪 畏难")
    b = write(tmp_path, "b.txt", SIX + " 情绪 畏难 急躁 焦虑 崩溃")
    r = subprocess.run([sys.executable, str(SCRIPT), a, b], capture_output=True, text=True)
    assert "发现 1 处" in r.stdout  # 情绪差 3 个只应计 1 处偏离，不重复计
