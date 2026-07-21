#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate-structure.py — 通用 Skill 结构完整性校验工具

用途：对任意 Skill 目录执行结构自检，确保无断链/版本漂移/跨文件数值不一致。
用法：python validate-structure.py [--dir SKILL_DIR]

通用检查项（适用于所有 Skill）：
  1. SKILL.md / README.md / test-prompts.json 版本号一致性
  2. 跨文件数值引用一致性（核心——改一查全，不扫完不推送）
  3. references 目录文件存在性 & frontmatter 版本
  4. 编号序列连续性（G/M/N/F 等，自动检测）
  5. 跨文件 § 引用有效性（→ §N 模式）
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

from _compat import setup_console
setup_console()


# ─── S6 统一容错读取 ───────────────────────────────────────
def _read(path):
    """utf-8 失败回退 gb18030；再失败返回 None（调用方 log_error 并跳过）。

    旧版所有 read_text(encoding="utf-8") 无容错，一个 GBK/BOM 文件即
    UnicodeDecodeError 拖垮整轮校验（后续检查项全部不执行）。
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="gb18030")
        except Exception:
            return None
    except OSError:
        return None

# ─── 路径解析 ──────────────────────────────────────────────
def resolve_skill_dir():
    """S3：argparse 统一入口（旧版手撕 sys.argv，--dir 缺值静默、无 --help）"""
    parser = argparse.ArgumentParser(description="Skill 结构完整性校验")
    parser.add_argument("--dir", default=None,
                        help="Skill 目录（默认脚本所在目录的上一级）")
    args = parser.parse_args()
    if args.dir:
        return Path(args.dir).resolve()
    return Path(__file__).resolve().parent.parent

SKILL_DIR = resolve_skill_dir()
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


# ─── 1. 版本一致性（通用）────────────────────────────────
def check_versions():
    print("\n📦 版本一致性")
    skill_md = SKILL_DIR / "SKILL.md"
    if not skill_md.exists():
        log_error("SKILL.md 不存在")
        return None
    content = _read(skill_md)
    if content is None:
        log_error("SKILL.md 读取失败（编码异常）")
        return None
    m = re.search(r'version:\s*([\d.]+)', content)
    skill_ver = m.group(1) if m else None

    if skill_ver:
        log_ok(f"SKILL.md 版本: {skill_ver}")
    else:
        log_error("SKILL.md 缺 version 字段")
        return None

    # README badge
    readme = SKILL_DIR / "README.md"
    if readme.exists():
        rm = _read(readme)
        if rm is None:
            log_warn("README.md 读取失败（编码异常）")
            rm = ""
        bm = re.search(r'badge/version-([\d.]+)', rm)
        readme_ver = bm.group(1) if bm else None
        if readme_ver and readme_ver == skill_ver:
            log_ok(f"README.md 版本一致: {readme_ver}")
        elif readme_ver:
            log_error(f"README.md 版本不一致: {readme_ver} ≠ {skill_ver}")
        else:
            log_warn("README.md 缺版本 badge")
    else:
        log_warn("README.md 不存在")

    # test-prompts.json
    tp = SKILL_DIR / "test-prompts.json"
    if tp.exists():
        try:
            raw = _read(tp)
            if raw is None:
                raise ValueError("编码异常")
            data = json.loads(raw)
            tp_ver = data.get("version")
            if tp_ver and tp_ver == skill_ver:
                log_ok(f"test-prompts.json 版本一致: {tp_ver}")
            elif tp_ver:
                log_error(f"test-prompts.json 版本不一致: {tp_ver} ≠ {skill_ver}")
            else:
                log_warn("test-prompts.json 缺 version 字段")
        except Exception:
            log_warn("test-prompts.json 解析失败")
    else:
        log_warn("test-prompts.json 不存在")

    return skill_ver


# ─── 2. 跨文件数值引用一致性（通用——核心检查）────────────
def check_cross_file_numbers():
    """扫描 SKILL.md 中的关键数值声明，在全仓 .md 文件中验证所有引用一致"""
    print("\n🔢 跨文件数值引用一致性")

    skill_md = SKILL_DIR / "SKILL.md"
    if not skill_md.exists():
        return
    content = _read(skill_md)
    if content is None:
        log_error("SKILL.md 读取失败（编码异常）")
        return

    # ── 2a. 收集 SKILL.md 中的数值声明 ──
    # 模式：标题或正文中的 "N 条/N 个/N 步/N 层/N 种/N 项 + 语义标签"
    declarations = {}  # {语义标签: (数值, 行号)}

    patterns = [
        # "## 📋 17 条硬约束" 或 "## 约束表（17 条）"
        (r'#{1,4}\s+[^\n]*?(\d+)\s*条\s*(硬约束|约束|规则|铁律)', 'constraint'),
        (r'#{1,4}\s+[^\n]*?(\d+)\s*条\s*(检查项|自检项|审计项)', 'check_item'),
        (r'#{1,4}\s+[^\n]*?(\d+)\s*步', 'step'),
        (r'#{1,4}\s+[^\n]*?(\d+)\s*层', 'layer'),
        (r'#{1,4}\s+[^\n]*?(\d+)\s*个\s*(阶段|模块|维度|核心)', 'component'),
        (r'#{1,4}\s+[^\n]*?(\d+)\s*种\s*(模式|方法|类型|风格)', 'type'),
        (r'#{1,4}\s+[^\n]*?(\d+)\s*项\s*(原则|能力|要求)', 'principle'),
    ]

    for pattern, tag in patterns:
        for m in re.finditer(pattern, content):
            num = int(m.group(1))
            line_no = content[:m.start()].count('\n') + 1
            declarations[tag] = (num, line_no)
            break  # 每种只取第一个匹配

    if not declarations:
        log_warn("未检测到数值声明（可能 Skill 结构简单，跳过）")
        return

    for tag, (num, line_no) in declarations.items():
        log_ok(f"SKILL.md L{line_no}: {tag} = {num}")

    # ── 2b. 全仓扫描所有 .md 文件中的数值引用 ──
    print("   🔍 全仓扫描数值引用...")
    all_md = list(SKILL_DIR.rglob("*.md"))
    stale_found = False

    # 构建搜索模式：对每个声明数值，在所有文件中找 "N 条/N 个/N 步..." 
    # 中文语义锚点：旧版用英文 tag 拼搜索模式（如 "17 条 constraint"）在中文文档中
    # 永不命中，跨文件检查形同虚设却输出"零残留"。改为按 tag 映射回中文名词扫描。
    tag_patterns = {
        'constraint': r'(\d+)\s*条\s*(?:硬约束|约束|规则|铁律)',
        'check_item': r'(\d+)\s*条\s*(?:检查项|自检项|审计项)',
        'step':       r'(\d+)\s*步',
        'layer':      r'(\d+)\s*层',
        'component':  r'(\d+)\s*个\s*(?:阶段|模块|维度|核心)',
        'type':       r'(\d+)\s*种\s*(?:模式|方法|类型|风格)',
        'principle':  r'(\d+)\s*项\s*(?:原则|能力|要求)',
    }

    for tag, (declared_num, _) in declarations.items():
        search_pattern = tag_patterns.get(tag)
        if not search_pattern:
            continue
        for fpath in all_md:
            if '.git' in fpath.parts:
                continue
            fc = _read(fpath)
            if fc is None:
                log_error(f"{fpath.relative_to(SKILL_DIR)} 读取失败（编码异常），跳过数值检查")
                continue
            rel = fpath.relative_to(SKILL_DIR)

            for m in re.finditer(search_pattern, fc):
                found_n = int(m.group(1))
                if found_n != declared_num:
                    line_no = fc[:m.start()].count('\n') + 1
                    line_start = fc.rfind('\n', 0, m.start()) + 1
                    is_header = fc[line_start:m.start()].lstrip().startswith('#')
                    msg = f"{rel}:{line_no} 「{m.group(0)}」与声明值 {declared_num} 不一致（{tag}）"
                    if is_header:
                        # 标题是结构性声明，数值不一致视为断链
                        log_error(msg)
                        stale_found = True
                    else:
                        # 正文提及可能只是局部语境（如"共 6 条子规则"），降级为警告
                        log_warn(msg)

    if not stale_found:
        log_ok("全仓数值引用一致，零残留")



# ─── 3. References 文件完整性（通用）──────────────────────
def check_references():
    print("\n📁 References 文件完整性")

    refs_dir = SKILL_DIR / "references"

    # Collect references from SKILL.md table（S2 修正：.py 脚本引用校验独立于
    # references/ 目录存在与否——scripts/ 与 references/ 是平级目录，旧结构在
    # references/ 缺失时整体 return，会连带跳过 scripts/*.py 断链检测）
    skill_md = SKILL_DIR / "SKILL.md"
    if not skill_md.exists():
        if not refs_dir.exists():
            log_warn("references/ 目录不存在，跳过")
        return
    content = _read(skill_md)
    if content is None:
        log_error("SKILL.md 读取失败（编码异常）")
        return

    # .py 引用（如 scripts/verify-answer.py）统一按 SKILL_DIR 相对路径校验（S2：
    # 旧版正则只覆盖 .md，`scripts/extract-equation.py` 这类真实引用从不被校验）
    py_refs = set(re.findall(r'`((?:[a-zA-Z0-9_\-]+/)*[a-zA-Z0-9_\-]+\.py)`', content))
    for ref in sorted(py_refs):
        if (SKILL_DIR / ref).exists():
            log_ok(f"{ref} 存在")
        else:
            log_error(f"引用文件不存在: {ref}")

    if not refs_dir.exists():
        log_warn("references/ 目录不存在，跳过 references 检查")
        return

    all_files = set(f.name for f in refs_dir.iterdir() if f.is_file())
    md_files = {f for f in all_files if f.endswith('.md')}

    # 支持裸文件名（默认 references/ 下）与子目录路径（如 evals/eval-set.md）两种引用；
    # 旧版正则不含 "/"，`evals/eval-set.md` 等子目录引用从不被校验
    refs_in_table = set(re.findall(r'`((?:[a-zA-Z0-9_\-]+/)*[a-zA-Z0-9_\-]+\.md)`', content))
    bare_refs = {r for r in refs_in_table if '/' not in r}
    path_refs = {r for r in refs_in_table if '/' in r}

    # 路径型引用（references/ 之外，如 evals/）：相对 SKILL_DIR 校验存在性
    for ref in sorted(r for r in path_refs if not r.startswith('references/')):
        if (SKILL_DIR / ref).exists():
            log_ok(f"{ref} 存在")
        else:
            log_error(f"引用文件不存在: {ref}")

    # references/ 内被引用的文件 = 裸文件名 + references/ 前缀路径
    ref_names = bare_refs | {r.split('/', 1)[1] for r in path_refs if r.startswith('references/')}

    # Check each referenced .md exists
    missing = ref_names - md_files
    for f in sorted(missing):
        log_error(f"引用文件不存在: references/{f}")

    for f in sorted(ref_names & md_files):
        log_ok(f"references/{f} 存在")

    # Check orphan files
    orphans = md_files - ref_names
    for f in sorted(orphans):
        # Skip methodology files (common pattern)
        if f.startswith('methodology-'):
            log_ok(f"references/{f} (方法论文件，按模式引用)")
        else:
            log_warn(f"references/{f} 在目录中但不在 SKILL.md 引用表中")

    # Check referenced HTML files exist（同样支持子目录路径）
    html_in_table = set(re.findall(r'`((?:[a-zA-Z0-9_\-]+/)*[a-zA-Z0-9_\-]+\.html)`', content))
    for f in sorted(html_in_table):
        target = (SKILL_DIR / f) if '/' in f else (refs_dir / f)
        if not target.exists():
            log_error(f"引用 HTML 文件不存在: {f}")

    # Check frontmatter version consistency
    skill_ver_m = re.search(r'version:\s*([\d.]+)', content)
    expected_ver = skill_ver_m.group(1) if skill_ver_m else None

    if expected_ver and md_files:
        print("\n📋 Reference frontmatter 版本")
        for fname in sorted(md_files):
            fpath = refs_dir / fname
            fc = _read(fpath)
            if fc is None:
                log_error(f"{fname} 读取失败（编码异常），跳过版本检查")
                continue
            m = re.search(r'^version:\s*([\d.]+)', fc, re.MULTILINE)
            if m:
                ver = m.group(1)
                if ver == expected_ver:
                    log_ok(f"{fname} → {ver}")
                else:
                    log_error(f"{fname} 版本 {ver} ≠ {expected_ver}")


# ─── 4. 编号序列连续性（通用，自动检测）──────────────────
def check_number_sequences():
    """自动检测 references/ 中 .md 文件的编号序列（G/M/N/F 等前缀）"""
    print("\n🔗 编号序列连续性")

    refs_dir = SKILL_DIR / "references"
    if not refs_dir.exists():
        return

    # Scan all .md files for numbered sections with letter prefixes
    sequences = {}  # {prefix: [numbers]}

    for fpath in sorted(refs_dir.glob("*.md")):
        content = _read(fpath)
        if content is None:
            log_error(f"{fpath.name} 读取失败（编码异常），跳过编号检查")
            continue
        # Find patterns like "## G1", "### M3", "## N5 标题"
        for m in re.finditer(r'^#{2,4}\s+([A-Z])(\d+)', content, re.MULTILINE):
            prefix = m.group(1)
            num = int(m.group(2))
            if prefix not in sequences:
                sequences[prefix] = []
            sequences[prefix].append(num)

    if not sequences:
        log_warn("未检测到编号序列")
        return

    for prefix, nums in sequences.items():
        nums_sorted = sorted(set(nums))
        expected = list(range(nums_sorted[0], nums_sorted[-1] + 1))
        missing = sorted(set(expected) - set(nums_sorted))
        if not missing:
            log_ok(f"{prefix} 编号连续: {prefix}{nums_sorted[0]}-{prefix}{nums_sorted[-1]} ({len(nums_sorted)}条)")
        else:
            log_error(f"{prefix} 编号缺: {missing}")


# ─── 5. 跨文件 § 引用（通用）─────────────────────────────
def check_section_refs():
    """检查 SKILL.md 中 → §N 引用是否指向有效章节"""
    print("\n📎 跨文件 § 引用")

    skill_md = SKILL_DIR / "SKILL.md"
    if not skill_md.exists():
        return
    content = _read(skill_md)
    if content is None:
        log_error("SKILL.md 读取失败（编码异常）")
        return

    # Find all → §N references
    targets_raw = re.findall(r'→\s*§(\d+)', content)
    if not targets_raw:
        log_ok("无 § 引用，跳过")
        return

    targets = [int(t) for t in targets_raw]

    # Try to find matching numbered sections in SKILL.md
    # Look for constraint numbers in table, or generic numbered items
    constraint_nums = [int(m) for m in
                       re.findall(r'^\|\s*\*\*(\d+)\*\*\s*\|',
                                  content[content.find("| # |"):] if "| # |" in content else "",
                                  re.MULTILINE)]

    if not constraint_nums:
        log_warn("未找到编号表，无法验证 § 引用")
        return

    dead_refs = set(targets) - set(constraint_nums)
    if dead_refs:
        for d in sorted(dead_refs):
            log_error(f"§{d} 引用目标不存在于编号表中")
    else:
        log_ok(f"{len(targets)} 条 § 引用全部有效 ({len(set(targets))} 个唯一目标)")


# ─── main ───────────────────────────────────────────────────
def main():
    skill_name = SKILL_DIR.name if SKILL_DIR.name else "Unknown"
    print(f"🔍 Skill 结构校验: {skill_name}")
    print(f"  目录: {SKILL_DIR}\n")

    ver = check_versions()
    check_cross_file_numbers()       # 核心：跨文件数值一致性
    check_references()
    check_number_sequences()
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
        print("\n💡 提示：修复后重新运行本脚本确认。")
        sys.exit(1)
    else:
        print("\n✅ 全部通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
