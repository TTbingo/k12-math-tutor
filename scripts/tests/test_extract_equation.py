# -*- coding: utf-8 -*-
"""extract-equation.py 测试：E1 正名 + E2/E4 xfail。"""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "extract-equation.py"

import importlib.util
spec = importlib.util.spec_from_file_location("extract_equation", SCRIPT)
ee = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ee)


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


# ── 正常流程（文本模式） ─────────────────────────────────
def test_text_chicken_rabbit():
    r = run("--text", "鸡兔同笼，头35足94")
    assert "假设法" in r.stdout

def test_text_area():
    r = run("--text", "长方形的面积是多少")
    assert "面积" in r.stdout


# ── E1 钉住：图片模式显式未实现 ──────────────────────────
def test_image_mode_not_implemented(tmp_path):
    img = tmp_path / "p.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    r = run("--image", str(img))
    assert "NOT IMPLEMENTED" in r.stdout
    assert r.returncode == 1

def test_image_missing_exit_1():
    r = run("--image", "C:/nonexistent/definitely/pic.png")
    assert r.returncode == 1


# ── P3 修复后回归（E2/E4 已修） ──────────────────────────
def test_e2_single_char_circle():
    matches = ee.analyze_text("这个圆的半径是3")
    assert not any(m["关键词"] == "圆" for m in matches)

def test_e2_emotion_not_triggered_by_problem_text():
    matches = ee.analyze_text("小明不会算这道题")
    assert not any(m["方法论"] == "子贤 §情绪翻译机" for m in matches)

def test_e2_emotion_triggered_by_first_person():
    matches = ee.analyze_text("我不会做这道题，好难")
    assert any(m["方法论"] == "子贤 §情绪翻译机" for m in matches)

def test_e2_circle_area_dedup():
    matches = ee.analyze_text("求圆的面积")
    kws = [m["关键词"] for m in matches]
    assert "圆的面积" in kws and "面积" not in kws  # 长词吸收泛化短词

def test_e4_text_and_image_mutex(tmp_path):
    img = tmp_path / "p.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    r = run("--image", str(img), "--text", "题目")
    assert "互斥" in r.stdout or "WARN" in r.stdout
