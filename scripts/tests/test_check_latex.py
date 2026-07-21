# -*- coding: utf-8 -*-
"""check-latex.py 测试：C1 白名单语义 + C4 退出码契约 + C3/C5/C6 xfail。"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "check-latex.py"


def run_scan(d):
    return subprocess.run([sys.executable, str(SCRIPT), "--dir", str(d)],
                          capture_output=True, text=True)


def write(d, name, text):
    (d / name).write_text(text, encoding="utf-8")


def alerts(stdout, level):
    """从逐条告警行提取级别计数——总结区 '[HIGH]: N' 永远存在，只数告警行。"""
    return sum(1 for l in stdout.splitlines()
               if re.search(r"行 \d+ \[%s\]" % level, l))


# ── 正常流程（C1 语义） ──────────────────────────────────
def test_prose_command_is_high(tmp_path):
    write(tmp_path, "a.md", "prose \\times here\n")
    assert alerts(run_scan(tmp_path).stdout, "HIGH") == 1

def test_fence_block_is_info(tmp_path):
    write(tmp_path, "b.md", "```\n\\frac{1}{2}\n```\n")
    out = run_scan(tmp_path).stdout
    assert alerts(out, "INFO") == 1 and alerts(out, "HIGH") == 0

def test_inline_backticks_is_info(tmp_path):
    write(tmp_path, "c.md", "use `\\times` inline\n")
    out = run_scan(tmp_path).stdout
    assert alerts(out, "INFO") == 1 and alerts(out, "HIGH") == 0

def test_docs_whitelist_is_info(tmp_path):
    write(tmp_path, "latex-guide.md", "\\frac{1}{2} 教学内容\n")
    out = run_scan(tmp_path).stdout
    assert alerts(out, "INFO") == 1 and alerts(out, "HIGH") == 0

def test_escaped_pipe_no_alert(tmp_path):
    write(tmp_path, "e.md", "| a \\| b |\n")
    out = run_scan(tmp_path).stdout
    assert alerts(out, "HIGH") == 0 and alerts(out, "INFO") == 0


# ── C4 钉住：退出码契约 ──────────────────────────────────
def test_exit_0_when_clean(tmp_path):
    write(tmp_path, "clean.md", "no latex here\n")
    assert run_scan(tmp_path).returncode == 0

def test_exit_1_when_high(tmp_path):
    write(tmp_path, "a.md", "prose \\times here\n")
    assert run_scan(tmp_path).returncode == 1


# ── 异常：GBK 文件不中断 ─────────────────────────────────
def test_gbk_file_does_not_abort(tmp_path):
    (tmp_path / "gbk.md").write_bytes("中文 \\times 内容\n".encode("gbk"))
    write(tmp_path, "ok.md", "clean\n")
    r = run_scan(tmp_path)
    assert "ERROR" in r.stdout or "gbk" in r.stdout  # 报 ERROR 但其余文件继续


# ── C2 钉住：同行反引号内外混合正确分级 ─────────────────
def test_mixed_backtick_and_prose_same_line(tmp_path):
    write(tmp_path, "m.md", "`\\frac` 说明 \\times\n")
    out = run_scan(tmp_path).stdout
    # \frac 在反引号内 INFO；\times 在正文应为 HIGH（C2 修复后按命令独立判定）
    assert alerts(out, "HIGH") == 1 and alerts(out, "INFO") == 1

def test_dotgithub_scanned(tmp_path):
    sub = tmp_path / ".github"
    sub.mkdir()
    write(sub, "w.md", "prose \\times\n")
    assert alerts(run_scan(tmp_path).stdout, "HIGH") == 1

def test_tilde_fence_is_info(tmp_path):
    write(tmp_path, "t.md", "~~~\n\\frac{1}{2}\n~~~\n")
    out = run_scan(tmp_path).stdout
    assert alerts(out, "HIGH") == 0 and alerts(out, "INFO") == 1

def test_word_boundary_divide(tmp_path):
    write(tmp_path, "d.md", "\\divide 是自定义命令\n")
    out = run_scan(tmp_path).stdout
    # 词边界断言（?![a-zA-Z]）使 \divide 不再命中 \div → 应报 0
    assert alerts(out, "HIGH") == 0
