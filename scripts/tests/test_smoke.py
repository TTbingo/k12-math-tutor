# -*- coding: utf-8 -*-
"""集成层冒烟：5 个脚本 --help 均无 traceback，exit code ∈ {0,2}。"""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
SCRIPTS = ["verify-answer.py", "check-latex.py", "diff-case.py",
           "extract-equation.py", "validate-structure.py"]


@pytest.mark.parametrize("name", SCRIPTS)
def test_help_no_traceback(name):
    r = subprocess.run([sys.executable, str(SCRIPTS_DIR / name), "--help"],
                       capture_output=True, text=True)
    assert "Traceback" not in r.stderr
    assert r.returncode in (0, 2)
