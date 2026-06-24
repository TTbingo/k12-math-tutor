#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate-structure.py — K12 Math Tutor Skill 结构完整性校验

用途：每次修改 SKILL.md 或 references/ 后跑一次，确保无断链/版本漂移。
触发：git pre-commit hook / CI / 手动 `python validate-structure.py`
用法：python validate-structure.py [--dir SKILL_DIR]

检查项：
  1. SKILL.md frontmatter version 与 README/test-prompts 一致
  2. 约束计数：标题 N 条 == 实际行数
  3. references 表所有文件存在
  4. G 编号连续性（gotchas.md）
  5. 无跨文件幽灵引用（§ → 目标章节存在）
"""

import os
import re
import sys
import json
from pathlib import Path

# Fix Windows GBK encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SKILL_DIR = Path(__file__).resolve().parent.parent
errors = []
warnings = []

def log_error(msg):
    errors.append(msg)
    print(f"  ❌ {msg}")

def log_warn(msg):
    warnings.append(msg)
    print(f"  ⚠️  {msg}")

def log_ok(msg):
    print(f"  ✅ {msg}")

# ─── 1. 版本一致性 ──────────────────────────────────────────
def check_versions():
    print("\n📦 版本一致性")
    # SKILL.md frontmatter
    skill_md = SKILL_DIR / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    m = re.search(r'version:\s*([\d.]+)', content)
    skill_ver = m.group(1) if m else None

    # README badge
    readme = SKILL_DIR / "README.md"
    if readme.exists():
        rm = readme.read_text(encoding="utf-8")
        bm = re.search(r'badge/version-([\d.]+)', rm)
        readme_ver = bm.group(1) if bm else None
    else:
        readme_ver = None

    # test-prompts.json
    tp = SKILL_DIR / "test-prompts.json"
    if tp.exists():
        try:
            data = json.loads(tp.read_text(encoding="utf-8"))
            tp_ver = data.get("version")
        except:
            tp_ver = None
    else:
        tp_ver = None

    if skill_ver:
        log_ok(f"SKILL.md 版本: {skill_ver}")
    else:
        log_error("SKILL.md 缺 version 字段")

    if readme_ver and readme_ver == skill_ver:
        log_ok(f"README.md 版本一致: {readme_ver}")
    elif readme_ver:
        log_error(f"README.md 版本不一致: {readme_ver} ≠ {skill_ver}")
    else:
        log_warn("README.md 缺版本 badge")

    if tp_ver and tp_ver == skill_ver:
        log_ok(f"test-prompts.json 版本一致: {tp_ver}")
    elif tp_ver:
        log_error(f"test-prompts.json 版本不一致: {tp_ver} ≠ {skill_ver}")
    else:
        log_warn("test-prompts.json 缺 version 字段")

    return skill_ver


# ─── 2. 约束计数 ──────────────────────────────────────────
def check_constraint_count(content):
    """检查 SKILL.md 约束计数 + 全仓「N条」引用一致性"""
    print("\n🔢 约束计数")
    # Find header N
    m_header = re.search(r'## 📋 (\d+) 条硬约束', content)
    if not m_header:
        log_error("未找到约束表标题 '## 📋 N 条硬约束'")
        return
    declared = int(m_header.group(1))

    # Count rows in constraints table
    table_start = content.find("| # | 约束名 | 一句话红线 | 详细 |")
    if table_start == -1:
        log_error("未找到约束表")
        return

    # Count actual constraint rows (| **N** | ...)
    table_section = content[table_start:]
    # Find end of table (blank line or next ##)
    table_end = re.search(r'\n\n(?:---|\n)', table_section[table_section.index('\n')+1:])
    if table_end:
        end_pos = table_section.index('\n') + 1 + table_end.start()
    else:
        end_pos = len(table_section)

    table_body = table_section[:end_pos]
    actual_rows = len(re.findall(r'^\|\s*\*\*\d+\*\*\s*\|', table_body, re.MULTILINE))

    if actual_rows == declared:
        log_ok(f"SKILL.md 约束计数一致: 标题 {declared}条 = 实际 {actual_rows}条")
    else:
        log_error(f"SKILL.md 约束计数不一致: 标题 {declared}条 ≠ 实际 {actual_rows}条")

    # ─── 2b. 交叉验证 constraints-quick-ref.md ───
    cqr = SKILL_DIR / "references" / "constraints-quick-ref.md"
    if cqr.exists():
        cqr_content = cqr.read_text(encoding="utf-8")
        # Count constraint sections: "## 约束 N｜" or "## 约束 N（"
        cqr_constraints = len(re.findall(r'^## 约束\s+\d+[｜(（]', cqr_content, re.MULTILINE))
        if cqr_constraints == declared:
            log_ok(f"constraints-quick-ref.md 约束计数一致: {cqr_constraints}条")
        else:
            log_error(f"constraints-quick-ref.md 约束计数不一致: {cqr_constraints}条 ≠ SKILL.md 声明的 {declared}条")

    # ─── 2c. 全仓扫描「N条」引用 ───
    print("   🔍 全仓扫描「N条」引用...")
    all_md = list(SKILL_DIR.rglob("*.md"))
    stale_refs = []
    for fpath in all_md:
        if '.git' in fpath.parts:
            continue
        fc = fpath.read_text(encoding="utf-8")
        # Find all "N条" / "N 条" patterns
        for m in re.finditer(r'(\d+)\s*条\s*(硬约束|约束)', fc):
            found_n = int(m.group(1))
            if found_n != declared:
                rel = fpath.relative_to(SKILL_DIR)
                stale_refs.append(f"{rel}:{fc[:m.start()].count(chr(10))+1} 「{m.group(0)}」应为{declared}条")

    if stale_refs:
        for s in stale_refs:
            log_error(f"残留旧引用: {s}")
    else:
        log_ok(f"全仓「{declared}条」引用一致，零残留")


# ─── 3. References 文件存在性 & frontmatter version ─────────
def check_references():
    print("\n📁 References 文件完整性")

    refs_dir = SKILL_DIR / "references"
    if not refs_dir.exists():
        log_error("references/ 目录不存在")
        return

    all_files = set(f.name for f in refs_dir.iterdir() if f.is_file())
    md_files = {f for f in all_files if f.endswith('.md')}

    # Collect references from SKILL.md table
    skill_md = SKILL_DIR / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    refs_in_table = set(re.findall(r'`([a-zA-Z][a-zA-Z0-9_\-.]*\.md)`', content))

    # Check each referenced .md exists
    missing = refs_in_table - md_files
    for f in sorted(missing):
        log_error(f"引用文件不存在: references/{f}")

    for f in sorted(refs_in_table & md_files):
        log_ok(f"references/{f} 存在")

    # Check orphan files (in dir but not in SKILL.md table)
    referenced_html = set(re.findall(r'`([a-zA-Z][a-zA-Z0-9_\-.]*\.html)`', content))
    expected_refs = refs_in_table | referenced_html | {'SKILL.md'}

    orphans = md_files - refs_in_table
    for f in sorted(orphans):
        # Skip methodology files (referenced by pattern not exact name)
        if f.startswith('methodology-'):
            log_ok(f"references/{f} (方法论文件，按模式引用)")
        else:
            log_warn(f"references/{f} 在目录中但不在 SKILL.md 引用表中")

    # Check referenced HTML files exist
    html_in_table = referenced_html - all_files
    for f in sorted(html_in_table):
        log_error(f"引用 HTML 文件不存在: references/{f}")

    # Check frontmatter version consistency in all .md references
    print("\n📋 Reference frontmatter 版本")
    for fname in sorted(md_files):
        fpath = refs_dir / fname
        fc = fpath.read_text(encoding="utf-8")
        m = re.search(r'^version:\s*([\d.]+)', fc, re.MULTILINE)
        if m:
            ver = m.group(1)
            if ver == "1.0.0":
                log_ok(f"{fname} → {ver}")
            else:
                log_warn(f"{fname} 版本 {ver} ≠ 1.0.0")
        # Skip if no version frontmatter (not all .md files have it)


# ─── 4. G 编号连续性 ─────────────────────────────────────
def check_g_numbers():
    print("\n🔗 G 编号连续性")
    gotchas = SKILL_DIR / "references" / "gotchas.md"
    if not gotchas.exists():
        log_error("references/gotchas.md 不存在")
        return

    content = gotchas.read_text(encoding="utf-8")
    # Find all G numbers in section headers
    g_nums = [int(m) for m in re.findall(r'^## G(\d+)', content, re.MULTILINE)]
    g_nums.sort()

    if not g_nums:
        log_warn("未找到 G 编号")
        return

    expected = list(range(g_nums[0], g_nums[-1] + 1))
    missing = set(expected) - set(g_nums)
    extra = set(g_nums) - set(expected)

    if not missing:
        log_ok(f"G 编号连续: G{g_nums[0]}-G{g_nums[-1]} ({len(g_nums)}条)")
    else:
        log_error(f"G 编号缺: {sorted(missing)}")


# ─── 5. 跨文件 § 引用 ──────────────────────────────────────
def check_section_refs():
    print("\n📎 跨文件 § 引用")
    skill_md = SKILL_DIR / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")

    # Find all → §N references in constraints table
    targets_raw = re.findall(r'→ §(\d+)', content)
    targets = [int(t) for t in targets_raw]

    # These should map to constraint numbers in the table
    constraint_nums = [int(m) for m in
                       re.findall(r'^\|\s*\*\*(\d+)\*\*\s*\|',
                                  content[content.find("| # | 约束名"):],
                                  re.MULTILINE)]

    dead_refs = set(targets) - set(constraint_nums)
    if dead_refs:
        for d in sorted(dead_refs):
            log_error(f"§{d} 引用目标不存在于约束表中")
    else:
        log_ok(f"{len(targets)} 条 § 引用全部有效 ({len(set(targets))} 个唯一目标)")


# ─── main ───────────────────────────────────────────────────
def main():
    print(f"🔍 K12 Math Tutor 结构校验")
    print(f"  目录: {SKILL_DIR}\n")

    ver = check_versions()

    skill_content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    check_constraint_count(skill_content)
    check_references()
    check_g_numbers()
    check_section_refs()

    # Summary
    print(f"\n{'='*50}")
    print(f"结果: {len(errors)} 错误, {len(warnings)} 警告")
    if errors:
        print(f"\n❌ 错误列表:")
        for e in errors:
            print(f"  - {e}")
    if warnings:
        print(f"\n⚠️  警告列表:")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        sys.exit(1)
    else:
        print("\n✅ 全部通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
