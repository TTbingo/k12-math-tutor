# -*- coding: utf-8 -*-
"""validate-structure.py 测试：S1 中文锚点 + S2 断链 + S3/S4/S6 xfail。"""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "validate-structure.py"


def run(d):
    return subprocess.run([sys.executable, str(SCRIPT), "--dir", str(d)],
                          capture_output=True, text=True)


def make_skill(d, skill_md, refs=None):
    (d / "SKILL.md").write_text(skill_md, encoding="utf-8")
    if refs:
        rd = d / "references"
        rd.mkdir(exist_ok=True)
        for name, text in refs.items():
            (rd / name).write_text(text, encoding="utf-8")


# ── 正常流程：当前仓库 ───────────────────────────────────
def test_real_repo_passes():
    r = run(SCRIPT.parent.parent)
    assert "0 错误" in r.stdout and r.returncode == 0


# ── S1 钉住：中文锚点漂移检测 / 局部语境降级 ─────────────
def test_s1_heading_drift_is_error(tmp_path):
    make_skill(tmp_path,
               "---\nversion: 1.0.0\n---\n## 📋 17 条硬约束(if-then 表)\n详见 `references/constraints-quick-ref.md`。",
               {"constraints-quick-ref.md": "# 16 条硬约束速查卡\n"})
    assert "16 条硬约束" in run(tmp_path).stdout and "❌" in run(tmp_path).stdout

def test_s1_body_mention_is_warn_not_error(tmp_path):
    make_skill(tmp_path,
               "---\nversion: 1.0.0\n---\n## 📋 17 条硬约束(if-then 表)\n详见 `references/constraints-quick-ref.md`。",
               {"constraints-quick-ref.md": "# 17 条硬约束速查卡\n双输出规则（共 5 条规则）如下。\n"})
    r = run(tmp_path)
    assert "5 条规则" not in r.stdout or "⚠️" in r.stdout
    assert "❌" not in r.stdout


# ── S2 钉住：evals/ 子目录 + scripts/*.py 断链 ───────────
def test_s2_evals_missing_is_error(tmp_path):
    make_skill(tmp_path,
               "---\nversion: 1.0.0\n---\n测试集 `evals/eval-set.md`。\n",
               {"a.md": "# ok\n"})
    assert "evals/eval-set.md" in run(tmp_path).stdout and "不存在" in run(tmp_path).stdout

def test_s2_ghost_py_is_error(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "real.py").write_text("# ok\n", encoding="utf-8")
    make_skill(tmp_path,
               "---\nversion: 1.0.0\n---\n见 `scripts/ghost.py` 与 `scripts/real.py`。\n")
    r = run(tmp_path)
    assert "scripts/ghost.py" in r.stdout and "不存在" in r.stdout
    assert "scripts/real.py 存在" in r.stdout


# ── 异常：GBK references 不中断（S6：单文件解码失败不应拖垮整轮） ──
def test_s6_gbk_file_does_not_abort(tmp_path):
    rd = tmp_path / "references"
    rd.mkdir()
    (rd / "gbk.md").write_bytes("中文内容\n".encode("gbk"))
    (rd / "ok.md").write_text("# ok\n", encoding="utf-8")
    make_skill(tmp_path, "---\nversion: 1.0.0\n---\n见 `references/ok.md`。\n")
    r = run(tmp_path)
    assert "Traceback" not in r.stderr      # 修复后不应崩溃
    assert "ok.md 存在" in r.stdout          # 且其余检查继续


# ── S4 钉住：stdout 重定向到非文本流不崩溃 ──────────────
def test_s4_stdout_redirect_no_crash():
    import io, os
    script = SCRIPT.parent.parent
    code = (
        "import sys,subprocess,os;"
        "f=open(os.devnull,'wb');"
        "r=subprocess.run([sys.executable,r'%s','--dir',r'%s'],stdout=f,stderr=subprocess.PIPE);"
        "print(r.returncode)"
    ) % (SCRIPT, script)
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.stdout.strip() == "0"

def test_s3_dir_missing_value_errors():
    r = subprocess.run([sys.executable, str(SCRIPT), "--dir"], capture_output=True, text=True)
    assert r.returncode == 2
