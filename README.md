<p align="center">
  <br/>
  <b><span style="font-size: 2em;">🧮 K12 Math Tutor</span></b>
  <br/><br/>
  不只是解题工具，是一套<b>教学哲学系统</b>。
  <br/>
  融合五位教育专家的方法论，编码为 18 条硬约束、41 项失败模式、5 条教学哲学线的可执行辅导引擎。
  <br/><br/>
</p>

<div align="center">

[![Version](https://img.shields.io/badge/version-1.9.0-2563eb?style=flat-square)](SKILL.md)
[![License](https://img.shields.io/badge/license-MIT-22c55e?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-64%20passing-16a34a?style=flat-square)](scripts/tests/)
[![Coverage](https://img.shields.io/badge/coverage-K12%20小初高-f97316?style=flat-square)](references/grade-quick-ref.md)
[![WorkBuddy](https://img.shields.io/badge/platform-WorkBuddy%20Skill-8b5cf6?style=flat-square)](https://www.codebuddy.cn)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)

</div>

---

## 这是什么

**K12 Math Tutor** 是一个 WorkBuddy AI Agent Skill，覆盖小学、初中、高中全学段数学辅导。与传统搜题工具的核心区别：

| 传统工具 | K12 Math Tutor |
|---------|----------------|
| 直接给答案 | 苏格拉底式追问，引导孩子自己推导 |
| 只讲"怎么算" | 深挖"为什么这么算"（算理 > 算法） |
| 机械刷题 | 吃透一道经典题，胜过刷 100 道 |
| 死记公式 | 从具象到抽象，理解推导过程 |
| 忽略情绪 | 情绪优先——先共情再教学 |
| 一次成型 | 每次失败自动追加到失败模式库，越用越准 |

**适用**：家长辅导、学生自学、教师备课。**不适用**：高等数学、考研数学、奥赛冲刺、教务管理。

---

## 目录

- [快速开始](#快速开始)
- [功能特性](#功能特性)
- [五条教学哲学线](#五条教学哲学线)
- [技术架构](#技术架构)
- [目录结构](#目录结构)
- [约束与质量保障](#约束与质量保障)
- [脚本工具](#脚本工具)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [致谢](#致谢)
- [许可证](#许可证)

---

## 快速开始

### 环境要求

| 依赖 | 版本 | 是否必需 |
|------|------|---------|
| WorkBuddy | 最新桌面 App 或 CLI | ✅ 必需 |
| Python | 3.8+ | 仅运行 scripts 时需要 |
| pytest | 7.0+ | 仅运行测试套件时需要 |

### 安装

```bash
# 克隆到 WorkBuddy skills 目录
git clone https://github.com/TTbingo/k12-math-tutor.git ~/.workbuddy/skills/k12-math-tutor
```

Skill 会在 WorkBuddy 对话中**自动识别触发词并加载**，无需手动配置。

### 第一次使用

在 WorkBuddy 对话中直接提问：

```text
孩子三年级，不会做鸡兔同笼，帮我讲一下
这道二次函数压轴题怎么做？我初二
孩子计算总是出错，怎么训练？
帮我出一道四年级的分数计算题
```

**触发关键词**（100+）：小学/初中/高中 + 数学、鸡兔同笼、奥数、算理、一题多解、几何辅助线、思维训练、情绪翻译机、ABCDE、小升初、初升高……

---

## 功能特性

### 🎯 双模式自动切换

| 模式 | 触发条件 | 行为 |
|------|---------|------|
| 🧒 **学生模式** | "我不会做…""这道题怎么做" | 苏格拉底五轮追问（L0→L4）+ 情绪扫描 + 知识脉络 |
| 👨‍👩‍👦 **家长模式** | "孩子…""我家娃…""帮我讲一下" | 六合一模板：解析 + 多解 + 难点预判 + 引导脚本 + 知识链 + 延伸练习 |

### 📚 K12 三层知识库

| 学段 | 知识文件 | 覆盖范围 |
|------|---------|---------|
| 小学 | `comprehensive-knowledge-base.md` | 全量知识点 + 算理对照 |
| 初中 | `junior-math-review-compendium.md` | 26 章中考总复习 |
| 高中 | `hs-math-review-compendium.md` | 五册 18 章深度萃取 |

### 🔄 飞轮进化机制

每次辅导失败 → 自动追加到 `gotchas.md`（G1-G41，39 条有效）→ 升级约束规则 → Skill 越用越准。P3 定期回顾（每 30 天 / 每 10 条记录 / 每次大版本变动）自动归并去重。

### 📝 错题本系统

基于子贤老师三层诊断法（🟡基础技能 / 🟢前置知识 / 🔴数学思维），构建完整复习闭环：入库定周期 → 到期提醒 → 变式出题 + 降维 → 结果回写 → 掌握归档。支持 Markdown + HTML 双格式输出。

### 🧪 质量保障

- **18 条硬约束**：if-then 规则，覆盖算理、追问、情绪、双输出、原题呈现等
- **11 项自检清单**：输出前逐项打勾，4 项强制阻塞
- **pytest 回归套件**：64 用例全绿，覆盖 5 个核心脚本
- **eval 活体测试**：20 题 × 4 维评分，月度量化

---

## 五条教学哲学线

| 哲学线 | 来源 | 核心原则 |
|--------|------|---------|
| **算理优先** | 胡小群（复旦附中名师） | 每个概念先讲"为什么这么算"，再讲"怎么算" |
| **有序枚举** | 昍爸（中科院博士） | 复杂题用递进式分类代替跳跃式猜测 |
| **积极心理学** | 子贤老师 | 情绪翻译机 + 彩虹夸夸 + 错题日复习 |
| **解释风格干预** | 塞利格曼 | 3P 诊断 + ABCDE 认知重构，修复悲观归因 |
| **课标核心素养** | 课标 2022 | 三会用 + 十大核心素养 + 跨学段衔接 |

当多条方法论线冲突时，裁决优先级：**情绪崩溃 > ABCDE > 算理优先**（详见 §G19）。

---

## 技术架构

```
┌─────────────────────────────────────────────────┐
│                   WorkBuddy Agent                │
│  (Read / Write / WebSearch / WebFetch tools)    │
└─────────────────────┬───────────────────────────┘
                      │ 加载 Skill
┌─────────────────────▼───────────────────────────┐
│              SKILL.md (主入口)                    │
│  ┌──────────┐ ┌──────────┐ ┌─────────────────┐ │
│  │ 身份识别  │ │ 方法论路由 │ │ 18 条硬约束引擎  │ │
│  │ 双模式切换│ │ 5 线决策  │ │ if-then 执行器   │ │
│  └──────────┘ └──────────┘ └─────────────────┘ │
│  ┌──────────────────────────────────────────┐   │
│  │           自检清单 (11 项 × 4 阻塞)        │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    ▼                 ▼                  ▼
┌────────┐    ┌──────────────┐    ┌────────────┐
│references│   │   scripts/   │    │   evals/   │
│ 知识库   │   │  验证工具链   │    │  活体测试   │
│ 方法论   │   │  pytest 套件  │    │  4 维评分   │
│ 案例库   │   │  _compat 层   │    │  月度评估   │
│ gotchas │   │  5 个脚本     │    │            │
└────────┘    └──────────────┘    └────────────┘
```

### 核心组件

| 组件 | 位置 | 职责 |
|------|------|------|
| **主入口** | `SKILL.md` | Skill 加载钩子、约束引擎、SOP 工作流、自检清单 |
| **知识库** | `references/`（34 个文件） | 方法论文档、K12 知识体系、案例库、错题模板 |
| **验证工具链** | `scripts/`（6 个文件） | LaTeX 检查、答案验证、偏离检测、结构校验 |
| **共享兼容层** | `scripts/_compat.py` | Windows GBK 终端 UTF-8 适配 |
| **测试套件** | `scripts/tests/`（6 个文件） | pytest 64 用例回归 + 集成冒烟 |
| **活体测试** | `evals/eval-set.md` | 20 题 × 4 维评分，月度量化 |
| **测试用例** | `test-prompts.json` | 结构化测试 prompt 集 |

---

## 目录结构

```
k12-math-tutor/
│
├── SKILL.md                                   # 主入口：加载钩子 + 约束引擎 + SOP + 自检清单
├── README.md                                  # 本文件
├── test-prompts.json                          # 结构化测试用例集
├── .gitignore                                 # Git 忽略规则
│
├── evals/
│   └── eval-set.md                            # 20 题活体测试集（月度跑）
│
├── scripts/                                   # 验证工具链（Python 3.8+）
│   ├── _compat.py                             # 共享兼容层：Windows 终端 UTF-8 适配
│   ├── check-latex.py                         # LaTeX 残留扫描
│   ├── verify-answer.py                       # 答案可逆验证（AST 安全求值器）
│   ├── diff-case.py                           # 方法论偏离对比
│   ├── extract-equation.py                    # 算理考点识别
│   ├── validate-structure.py                  # Skill 结构完整性校验
│   └── tests/                                 # pytest 回归套件（64 用例）
│       ├── conftest.py
│       ├── test_smoke.py
│       ├── test_check_latex.py
│       ├── test_verify_answer.py
│       ├── test_diff_case.py
│       ├── test_extract_equation.py
│       └── test_validate_structure.py
│
└── references/                                # 知识资产（34 个文件）
    │
    ├── 核心知识体系/
    │   ├── comprehensive-knowledge-base.md
    │   ├── junior-math-review-compendium.md
    │   ├── hs-math-review-compendium.md
    │   ├── grade-curriculum-map.md
    │   ├── grade-quick-ref.md
    │   ├── curriculum-standard-2022.md
    │   ├── k12-skill-taxonomy.md
    │   └── exam-bank.md
    │
    ├── 方法论（5 套）/
    │   ├── methodology-hu-xiaoqun.md
    │   ├── methodology-xuanba.md
    │   ├── methodology-xuanba-advanced.md
    │   ├── methodology-zixian.md
    │   ├── seligman-positive-parenting.md
    │   ├── core-formula-teaching-scripts.md
    │   ├── xuanba-problem-bank.md
    │   └── life-scene-math.md
    │
    ├── 约束与规范/
    │   ├── constraints-quick-ref.md
    │   ├── socratic-depth-algorithm.md
    │   ├── question-design.md
    │   ├── latex-guide.md
    │   ├── latex-commands.json
    │   └── latex-whitelist.json
    │
    ├── 案例与进化/
    │   ├── gotchas.md
    │   ├── case-studies.md
    │   ├── anti-patterns.md
    │   ├── olympiad-cases.md
    │   ├── tutor-log.md
    │   ├── skill-health.md
    │   └── p3-review-mechanism.md
    │
    ├── 错题与诊断/
    │   ├── mistake-bank.md
    │   └── diagnosis-card-template.html
    │
    └── 数据配置/
        ├── arithmetic-patterns.json
        └── diff-case-keywords.json
```

---

## 约束与质量保障

### 18 条硬约束

每次输出前必须通过 11 项自检清单，其中 4 项强制阻塞：

| 阻塞项 | 检查内容 | 后果 |
|--------|---------|------|
| 🚪 物理门 0 | 学员信息已确认 | 禁止输出完整解析 |
| ⑧ | 答案可逆验证通过 | 禁止发出错误答案 |
| ⑨ | 双发附件已真发 | 禁止只输出文字 |
| ⑪ | HTML 原题完整呈现 | 禁止发出缺原题的 HTML |

完整约束卡片见 [`references/constraints-quick-ref.md`](references/constraints-quick-ref.md)。

### 失败模式库

已积累 **G1-G41**（39 条有效，2 条已淘汰），按触发信号自动追加。详见 [`references/gotchas.md`](references/gotchas.md)。

---

## 脚本工具

5 个独立 Python 工具，均支持 `--help` 查看参数，退出码 0=通过。Windows 下通过 `_compat.py` 自动处理终端编码。

```bash
cd ~/.workbuddy/skills/k12-math-tutor

# LaTeX 残留扫描
python scripts/check-latex.py --dir .

# 答案可逆验证
python scripts/verify-answer.py --answer "x=6, y=72" --expected "x=6, y=72"

# 方法论偏离检测
python scripts/diff-case.py output_v1.md output_v2.md

# Skill 结构完整性校验
python scripts/validate-structure.py --skill-dir .

# 算理考点识别
python scripts/extract-equation.py --text "某超市购进大米，成本4元/kg..."
```

### 运行测试

```bash
pip install pytest
pytest scripts/tests -q
# 预期：64 passed, 0 xfailed
```

---

## 常见问题

<details>
<summary><b>这个 Skill 和搜题 App 有什么区别？</b></summary>
<p>
搜题 App 直接给答案，孩子抄完就忘。K12 Math Tutor 用苏格拉底追问引导孩子自己想出来——从"你看到了什么条件"开始，一步步推导，让答案变成孩子自己的结论。家长模式还会教你怎么跟孩子对话、怎么夸。
</p>
</details>

<details>
<summary><b>需要装什么依赖？</b></summary>
<p>
<strong>零必需依赖</strong>。Skill 本身运行在 WorkBuddy 框架内，不需要额外安装。scripts 目录的验证工具是可选的（需要 Python 3.8+ + pytest 7.0+），仅开发/维护时使用。
</p>
</details>

<details>
<summary><b>支持哪些年级？</b></summary>
<p>
小学 1-6 年级、初中 7-9 年级、高中 10-12 年级，全学段覆盖。自动根据题目难度和提问方式推断年级。不适用高等数学、考研数学、奥赛冲刺。
</p>
</details>

<details>
<summary><b>怎么区分学生模式和家长模式？</b></summary>
<p>
自动识别。措辞用"我""这道题"→学生模式；"孩子""我家娃"→家长模式。家长模式会输出辅导脚本、夸夸话术、情绪应对策略，教你怎么教。
</p>
</details>

<details>
<summary><b>答案准确吗？</b></summary>
<p>
内置答案可逆验证（将答案代回原题验证），加 64 个 pytest 回归用例。但如果发现错误，请提交 issue 触发飞轮修复——这是 Skill 越用越准的设计机制。
</p>
</details>

<details>
<summary><b>OCR 识别数学公式怎么办？</b></summary>
<p>
WorkBuddy 内置多模态能力可以直接读图。如果公式复杂，可选安装 <code>rapid-ocr</code>、<code>pix2text-ocr</code> 或 <code>mineru</code> 作为增强（在 WorkBuddy 中用 find-skills 一键安装）。
</p>
</details>

<details>
<summary><b>怎么更新到最新版本？</b></summary>

```bash
cd ~/.workbuddy/skills/k12-math-tutor
git pull origin master
```

新版本会在下次会话自动生效。
</details>

---

## 贡献指南

欢迎贡献！以下是快速入口：

| 想做什么 | 怎么做 |
|---------|--------|
| 🐛 报告问题 | [提交 Issue](https://github.com/TTbingo/k12-math-tutor/issues)，附上版本号 + 输入/输出对比 |
| 💡 提建议 | [发起 Discussion](https://github.com/TTbingo/k12-math-tutor/discussions) |
| 🔧 提交代码 | Fork → 创建分支 → 跑测试 → 提交 PR |

### PR 提交前必做

```bash
# 结构完整性
python scripts/validate-structure.py --skill-dir .

# 全量测试
pytest scripts/tests -q
```

确保 64 用例全绿后再提交。

### 约束新增规范

- 新约束 → 必须同步更新 `constraints-quick-ref.md` + `gotchas.md`（追加不覆盖）
- 修改 `SKILL.md` → 版本号递增 → 更新 README 变更日志
- **先改文档，再改实践**

### 版本号语义

`MAJOR.MINOR.PATCH`：P0 修补 PATCH，P1/P2 修补 MINOR，架构变更补 MAJOR。

---

## 致谢

| 来源 | 核心贡献 |
|------|---------|
| **胡小群**（复旦附中名师） | 算理优先、三层次理解法、小初高一体化 |
| **昍爸**（中科院博士） | 解题八步法、六大思维方法、验算四层次 |
| **子贤老师** | 情绪翻译机、彩虹夸夸、三层诊断法 |
| **马丁·塞利格曼**（积极心理学之父） | 解释风格 3P 诊断、ABCDE 认知重构 |
| **义务教育课标 2022 版** | 核心素养体系、学段目标、学业质量标准 |

---

## 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **1.9.0** | 2026-07-21 | P2 新增：约束 18（HTML 原题完整呈现）+ G39 gotcha；自检清单同步新增 ⑪ |
| 1.8.6 | 2026-07-20 | P3 修复：5 脚本重构 + pytest 64 用例 |
| 1.8.5 | 2026-07-20 | P2 修复：verify Pow 上限 / 浮点容差 / check-latex 退出码 |
| 1.8.4 | 2026-07-20 | P1 修复：validate 中文锚点 / check-latex 精确匹配 |
| 1.8.3 | 2026-07-20 | P0 修复：verify 双向真值比对 / 216 测试点 |
| 1.8.2 | 2026-07-13 | SkillHub changelog 修正 + 全项目审查 |
| 1.8.0 | 2026-07-13 | 安全修复：eval() → AST 安全求值器 |
| 1.7.0 | 2026-07-06 | 可视化图表交付工作流 + SVG→HTML 三件套 |

---

## 许可证

MIT License © 2026 TTbingo

基于五位教育专家的公开方法论整理，仅供个人学习与辅导使用。引用请注明原作者。
