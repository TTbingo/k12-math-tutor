# -*- coding: utf-8 -*-
"""verify-answer.py 测试：V1-V5 回归 + 安全 + 边界。"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SCRIPT = Path(__file__).resolve().parent.parent / "verify-answer.py"


def run(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *args],
                       capture_output=True, text=True, timeout=30)
    return r


def parse(r):
    """stdout 必须是合法 JSON（V3 契约：任何失败都无 traceback）。"""
    assert "Traceback" not in r.stderr, f"出现 traceback: {r.stderr[:200]}"
    return json.loads(r.stdout)


# ── 正常流程 ──────────────────────────────────────────────
def test_equivalent_true():
    assert parse(run("--check", "a>b", "--option", "b-a<0"))["valid"] is True

def test_equivalent_add_const():
    assert parse(run("--check", "a>b", "--option", "a+2>b+2"))["valid"] is True

def test_equation_linear():
    assert parse(run("--equation", "x-3=5", "--answer", "x=8"))["valid"] is True

def test_equation_coeff():
    assert parse(run("--equation", "2*x=10", "--answer", "x=5"))["valid"] is True


# ── V1 钉住：单向蕴涵不得判等价 ───────────────────────────
def test_v1_implication_not_equivalence():
    assert parse(run("--check", "a>b", "--option", "a+1>b"))["valid"] is False

def test_v1_original_g_case():
    assert parse(run("--check", "a>b", "--option", "b-a>0"))["valid"] is False


# ── V2 钉住：近边界盲区 ──────────────────────────────────
def test_v2_near_boundary():
    assert parse(run("--check", "a>b", "--option", "a-b>0.05"))["valid"] is False


# ── 边界：除法 / 幂预处理 ────────────────────────────────
def test_equation_division():
    assert parse(run("--equation", "x/2=4", "--answer", "x=8"))["valid"] is True

def test_equation_caret_preprocess():
    assert parse(run("--equation", "x^2=16", "--answer", "x=4"))["valid"] is True


# ── V3 钉住：长链/深层嵌套输出 JSON 不崩溃 ────────────────
def test_v3_long_chain_no_crash():
    chain = "1+" * 3000 + "1"
    r = run("--check", "a>" + chain, "--option", "b>0")
    assert parse(r)["valid"] is False

def test_v3_deep_nesting_no_crash():
    nested = "(" * 150 + "1" + ")" * 150
    r = run("--check", "a>" + nested, "--option", "b>0")
    assert parse(r)["valid"] is False


# ── V4 钉住：巨大指数快速拒绝 ────────────────────────────
def test_v4_huge_pow_rejected():
    r = run("--check", "a>b", "--option", "a+9**999999999>b")
    assert parse(r)["valid"] is False


# ── V5 钉住：大数量级浮点判等 ────────────────────────────
def test_v5_large_magnitude():
    assert parse(run("--equation", "x*100000000=200000000", "--answer", "x=2"))["valid"] is True


# ── 异常：缺参 / 注入 / 全角 ─────────────────────────────
def test_missing_args():
    r = run("--check", "a>b")
    assert parse(r)["valid"] is False
    assert r.returncode == 1

@pytest.mark.parametrize("payload", ['__import__("os")', "open(", "x.__class__"])
def test_injection_rejected(payload):
    r = run("--check", payload, "--option", "b>0")
    assert parse(r)["valid"] is False

def test_fullwidth_equals():
    assert parse(run("--equation", "x-3=5", "--answer", "x＝8"))["valid"] is True

def test_multi_root_report():
    res = parse(run("--equation", "x^2=16", "--answer", "x=4或x=-4"))
    assert res["valid"] is True and "2 个根" in res["reason"]
