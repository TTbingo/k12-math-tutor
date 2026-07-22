---
title: "K12 双发与文件交付工作流"
version: 2.0
last_updated: 2026-07-22
usage: "当需要在移动端/微信双发 HTML 或交付可视化图表时 → 查本文件（从 SKILL.md 抽出，保留核心原则在 SKILL.md）"
---

# 🚨 输出原子化工作流（P0 硬规则，2026-07-03 重构）

> **核心原则**：生成 HTML 和调用 `deliver_attachments` 是**同一个动作**，不是两个步骤。禁止在"生成 HTML"和"调工具发附件"之间插入任何文字回复。
> **适用范围**：**仅限移动端/微信**；非移动端/微信用户跳过 `deliver_attachments`（直接生成 HTML 文件即可，由 `present_files` 预览展示），其余步骤不变。

## 正确动作序列（必须严格按顺序执行）

```
Step A: 生成 HTML 文件（Write 工具）
   ↓
Step B: 同一轮响应中立即调用 deliver_attachments 工具（传入 HTML 文件路径）
   ↓
Step C: 等待工具返回成功确认
   ↓
Step D: 输出文字摘要（精简版内容）
```

**关键约束**：
- Step A 和 Step B 必须在**同一轮工具调用**中完成（即同一个 `<function_calls>` 块）
- 禁止 Step A 完成后先输出文字（"已生成 HTML"），再在下一轮调工具
- 禁止只调 `preview_url` 而不调 `deliver_attachments`（微信用户需要附件，不只是预览）

## 错误模式（禁止）

| 错误序列 | 后果 | 对应 gotcha |
|---------|------|-------------|
| 生成 HTML → 文字回复"已发" → 结束 | 用户收不到附件（G26） | G26 |
| 生成 HTML → `preview_url` → 文字回复 | 微信用户无法打开预览链接（G25） | G25 |
| 生成 HTML → 自检清单 → 文字回复（漏调工具） | 用户收不到附件（G26 变体） | G26 |

## 正确模式（Few-shot 示例）

**示例 1：生成 HTML 后立即发附件（正确）**
```
[工具调用块]
1. Write(file_path="...review.html", content="...")
2. deliver_attachments(file_paths='["...review.html"]', explanation="...")
[然后文字回复]
"复习指南已生成，HTML 附件已发送到你的微信。"
```

**示例 2：只生成 Markdown（不需要 HTML 时）**
```
不需要调用 deliver_attachments。
只在生成 .html 文件时才需要双发。
```

## 与自检清单的关系

本工作流是**动作级约束**（决定"怎么做事"），自检清单是**输出级约束**（决定"输出是否完整"）。

- 本工作流保证：生成 HTML 后**一定会调工具**
- 自检清单保证：输出内容**完整且符合要求**

两层都过，才能输出。
   - 详见 `references/mistake-bank.md`

---

# 可视化图表交付工作流（App 兼容，2026-07-06 新增）

> **触发条件**：辅导中需要生成数学概念图、对比图、流程图、数轴图等可视化内容时（**仅限移动端/微信需 `deliver_attachments`**；非移动端/微信生成 HTML 文件 + `present_files` 预览即可）。
>
> **问题背景**：`show_widget` 工具在 Web 端可内联渲染 SVG，但 WorkBuddy 桌面 App **不支持内联渲染**，用户只看到文字、看不到图。

## 正确动作序列

```
Step A: 将 SVG 图表写入 HTML 文件（SVG 嵌入 <body>，加基本样式适配手机）
   ↓
Step B: 同一轮调用 deliver_attachments 发送 HTML 文件（保证微信/App 用户收到）
   ↓
Step C: 调用 preview_url 在桌面 App 内展示（App 用户可直接查看）
   ↓
Step D: 可选——同时调 show_widget 供 Web 端用户内联查看（双通道）
```

## 禁止模式

| 错误动作 | 后果 | 对应 gotcha |
|---------|------|-------------|
| 只调 `show_widget` 不生成文件 | App 用户看不到图 | **G38** |
| 生成 SVG 文件但不调 deliver_attachments | 微信/App 用户收不到 | G26 变体 |
| 生成 HTML 但不调 preview_url | App 用户无法在应用内查看 | **G38** |

## 实践要点

- **SVG → HTML 包装**：`<html><body style="margin:0;padding:16px;background:#fff"><svg>...</svg></body></html>`，确保手机端也能看
- **文件命名**：`{题目简称}-图表.html`，放在 `${OUTPUT_DIR}` 对应子目录
- **与 show_widget 的关系**：`show_widget` 是 Web 端增强（锦上添花），文件交付是基础保障（雪中送炭）。两者不互斥，但文件交付不可省略
