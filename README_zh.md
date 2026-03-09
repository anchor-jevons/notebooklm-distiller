# NotebookLM Distiller

一个 [OpenClaw](https://github.com/openclaw) 技能插件，用于从 Google NotebookLM 笔记本中提取知识，并将其写入 Obsidian 的结构化 Markdown 笔记。

> **版本 2.0** — 新增三个子命令：`distill`、`research`、`persist`。

---

## 功能特性

- **`distill`** — 从已有 NotebookLM 笔记本中提取知识，写入 Obsidian
  - 三种模式：`qa`（15-20 对深度问答）、`summary`（五节结构化摘要）、`glossary`（15-30 个领域术语）
  - 基于关键词的笔记本匹配（大小写不敏感，子字符串匹配）
  - 自动生成 Obsidian 兼容的 YAML frontmatter
- **`research`** — 对任意主题发起 NotebookLM 网络调研，等待完成后输出笔记本 ID，供后续蒸馏使用
- **`persist`** — 将任意 Markdown 内容直接写入 Obsidian vault，自动附加 frontmatter

无需爬虫依赖 —— 可与 [DeepReader](https://github.com/astonysh/OpenClaw-DeepReeder) 配合使用，实现完整的「URL → Obsidian」自动化流水线。

---

## 安装说明

**1. 将技能复制到 OpenClaw 目录：**
```bash
cp -r notebooklm-distiller ~/.openclaw/skills/
```

**2. 安装 NotebookLM CLI：**
```bash
pip3 install notebooklm-py
```

**3. 完成 Google 身份验证（仅首次需要）：**
```bash
notebooklm login
# 会自动打开浏览器，使用绑定了 NotebookLM 的 Google 账号登录
```

**环境要求：** Python 3.10+，除 `notebooklm-py` 外无其他 pip 依赖。

---

## 使用指南

### 子命令：`distill`

从标题匹配关键词的笔记本中提取知识。

```bash
python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py distill \
  --keywords "机器学习" "transformer" \
  --topic "ML研究" \
  --vault-dir "/path/to/your/Obsidian/Vault" \
  --mode qa
```

**参数说明：**

| 参数 | 必填 | 说明 |
|---|---|---|
| `--keywords` | ✅ | 用于匹配笔记本标题的关键词（可多个） |
| `--topic` | ✅ | 输出文件在 `--vault-dir` 下的子目录名 |
| `--vault-dir` | ✅ | Obsidian vault 路径（或任意输出目录） |
| `--mode` | | `qa`（默认）、`summary` 或 `glossary` |
| `--cli-path` | | `notebooklm` 可执行文件路径（不在 $PATH 时使用） |

**输出格式示例：**

文件路径：`<vault-dir>/<topic>/<笔记本名>_<Mode>.md`

```markdown
---
title: "我的笔记本 | Deep Q&A"
date: 2026-03-09
type: knowledge-note
author: notebooklm-distiller
tags: ["distillation", "qa", "ml研究"]
source: "NotebookLM/我的笔记本"
project: "ML研究"
status: draft
---

# 我的笔记本 — Deep Q&A

## Q01

> [!question]
> Transformer 注意力机制的核心权衡是什么？

**Answer:**
...
```

---

### 子命令：`research`

对任意主题发起网络调研，在 NotebookLM 中新建笔记本并等待完成。

```bash
python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py research \
  --topic "量子计算" \
  --mode deep
```

**参数说明：**

| 参数 | 必填 | 说明 |
|---|---|---|
| `--topic` | ✅ | 调研主题（同时作为笔记本名称） |
| `--mode` | | `deep`（默认）或 `fast` |
| `--cli-path` | | `notebooklm` 可执行文件路径 |

输出：打印笔记本 ID 和名称，随后可用 `distill` 子命令提取结果。

**完整调研→蒸馏流程：**
```bash
# 第一步：调研
python3 distill.py research --topic "量子计算"
# → Notebook: Research: 量子计算 (ID: abc123)

# 第二步：蒸馏
python3 distill.py distill \
  --keywords "量子计算" \
  --topic "QuantumComputing" \
  --vault-dir ~/Obsidian/Vault \
  --mode summary
```

---

### 子命令：`persist`

将任意 Markdown 内容写入 Obsidian vault，自动生成 YAML frontmatter。

```bash
# 从内联文字写入
python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py persist \
  --vault-dir "/path/to/Obsidian/Vault" \
  --path "Notes/2026-03-09-会议.md" \
  --title "团队会议记录" \
  --content "核心决策：..." \
  --tags "会议,笔记,2026"

# 从已有文件写入
python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py persist \
  --vault-dir "/path/to/Obsidian/Vault" \
  --path "Research/草稿.md" \
  --file ~/Desktop/草稿.md
```

---

## 与 DeepReader 的配合使用

本技能只负责**蒸馏**。如需实现完整的 **URL → NotebookLM → Obsidian** 流水线，请配合 [DeepReader](https://github.com/astonysh/OpenClaw-DeepReeder) 使用。

### 组合工作流（在 OpenClaw agent 中）

```
用户："读这个 https://example.com/paper 然后蒸馏存入 Obsidian"
  │
  ├─ DeepReader
  │    ├─ 抓取并解析目标 URL
  │    ├─ 将干净的 .md 保存到 memory/inbox/
  │    └─ 上传到 NotebookLM（智能路由：加入已有 notebook 或新建）
  │         └─ 返回：notebook_title、action
  │
  └─ NotebookLM Distiller
       ├─ 通过标题关键词匹配笔记本
       └─ 执行 distill → 写入 Obsidian vault
```

### 自然语言触发示例（在 OpenClaw 中）

```
# 蒸馏已有笔记本
"提取'量子计算'笔记本的摘要，存到 Obsidian"
"用 glossary 模式处理 ML Research 笔记本"

# 先调研再蒸馏
"研究一下 transformer architecture，蒸馏后存入知识库"

# 归档讨论结论
"把这段对话的结论存到 Obsidian"
```

---

## Obsidian 配置说明

**无需任何 Obsidian 插件或模板配置。** 只需将 `--vault-dir` 指向你的 vault 根目录或任意子目录，脚本会自动创建子目录并注入 Obsidian 可直接识别的 YAML frontmatter。

**推荐 vault 目录结构：**
```
YourVault/
└── Knowledge/
    └── MachineLearning/         ← --topic "MachineLearning"
        ├── MyNotebook_QA.md
        ├── MyNotebook_Summary.md
        └── MyNotebook_Glossary.md
```

---

## 常见问题

| 错误 | 解决方案 |
|---|---|
| `notebooklm: command not found` | 使用 `--cli-path $(which notebooklm)` 或重新安装 `pip3 install notebooklm-py` |
| `No notebooks matched` | 运行 `notebooklm list` 查看精确标题，调整 `--keywords` |
| 认证失败 / session 过期 | 运行 `notebooklm login` 刷新 `~/.book_client_session` |
| 蒸馏时速率限制或超时 | 内置重试逻辑可处理大多数情况；大笔记本建议先用 `--mode summary` |

---

## 许可证

MIT
