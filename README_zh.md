# NotebookLM Distiller

一个 [OpenClaw](https://github.com/openclaw) 技能插件，用于从 Google NotebookLM 笔记本中提取知识，并将其写入 Obsidian 的结构化 Markdown 笔记。

> **版本 2.1** — 新增：输出模板（`--template`），支持结构化提取（简报、幻灯片、深度报告、播客脚本、行动计划、学习笔记）。模板外置于 `templates.json`，可自定义。

---

## 功能特性

- **`distill`** — 从已有 NotebookLM 笔记本中提取知识，写入 Obsidian
  - **传统模式：** `qa`（15-20 对深度问答）、`summary`（五节专家知识地图）、`glossary`（15-30 个领域术语）
  - **输出模板**（新）：`brief`、`notes`、`report`、`slides`、`plan`、`audio-popular`、`audio-pro` — 复杂模板使用多段 prompt，避免截断
  - **自动路由**（新）：`--auto-route` 根据笔记本名称中的关键词自动选择模板
  - 基于关键词的笔记本匹配（大小写不敏感，子字符串匹配）
  - 自动生成 Obsidian 兼容的 YAML frontmatter
- **`quiz`** — 生成测验问题（JSON 输出），供 agent 编排的 Discord 互动测验使用
- **`evaluate`** — 将用户答案送入 NLM 评估，返回结构化反馈 JSON
- **`research`** — 对任意主题发起 NotebookLM 网络调研，等待完成后输出笔记本 ID
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
| `--mode` | | 传统模式：`qa`（默认）、`summary` 或 `glossary`。使用 `--template` 或 `--auto-route` 时忽略。 |
| `--template` | | 使用命名模板（见下方 **输出模板** 章节） |
| `--auto-route` | | 根据笔记本名称自动选择模板。无匹配时回退到 `--mode`。 |
| `--lang` | | 输出语言：`en`（默认）或 `zh`（中文） |
| `--writeback` | | 同时将蒸馏结果写回 NotebookLM 笔记本作为来源笔记 |
| `--cli-path` | | `notebooklm` 可执行文件路径（不在 $PATH 时使用） |

**优先级：** `--template` > `--auto-route` > `--mode`

---

### 输出模板

模板定义了**从笔记本提取什么**以及**如何组织输出**。每个模板向 NotebookLM 发送一个或多个 prompt，并将所有响应组装成一篇 Obsidian 笔记。

| 名称 | 输出文件 | 分段数 | 适用场景 |
|------|---------|--------|---------|
| `brief` | `_ExecutiveBrief.md` | 1 | 高管简报、财报速读、快速决策备忘 |
| `notes` | `_LearningNotes.md` | 1 | 个人学习笔记、教程复盘、课程总结 |
| `report` | `_DeepDiveReport.md` | 4 | 论文、深度研究、行业分析 |
| `slides` | `_Slides.md` | 3 | 演讲大纲、分享准备 |
| `plan` | `_ActionPlan.md` | 1 | 项目计划、需求落地、路线图 |
| `audio-popular` | `_AudioPodcast_Popular.md` | 1 | 科普向播客脚本（大众受众） |
| `audio-pro` | `_AudioPodcast_Pro.md` | 1 | 专业向播客脚本（从业者） |

> 多分段模板（如 `report` 4 段、`slides` 3 段）会对每段发起独立的 NLM 查询，产出更丰富且不会被截断的内容。

#### 使用示例

**生成高管简报：**
```bash
python3 distill.py distill \
  --keywords "Q4 营收" \
  --topic "Finance" \
  --vault-dir ~/Obsidian/Vault \
  --template brief \
  --lang zh
```
→ 输出：`Finance/Q4_营收_ExecutiveBrief.md` — 300 字以内的结构化备忘，含关键发现、核心指标、行动建议。

**生成播客脚本：**
```bash
python3 distill.py distill \
  --keywords "AI Trends" \
  --topic "Podcasts" \
  --vault-dir ~/Obsidian/Vault \
  --template audio-popular
```
→ 输出：`Podcasts/AI_Trends_AudioPodcast_Popular.md` — 双人对话式播客脚本，含开场 Hook、核心内容、收尾。

**生成深度报告（多段 prompt）：**
```bash
python3 distill.py distill \
  --keywords "transformer" \
  --topic "Research" \
  --vault-dir ~/Obsidian/Vault \
  --template report \
  --lang zh
```
→ 输出：`Research/Transformer_DeepDiveReport.md` — 4 段内容（执行摘要与背景 → 核心分析 → 对比分析与洞察 → 建议与局限），每段独立查询 NLM。

**使用自动路由（让笔记本名称决定模板）：**
```bash
python3 distill.py distill \
  --keywords "Q3 earnings" \
  --topic "Finance" \
  --vault-dir ~/Obsidian/Vault \
  --auto-route
```
→ 笔记本名称含 "earnings" → 自动路由到 `brief` 模板。若无关键词匹配，回退到 `--mode`（默认 `qa`）。

#### 修改面向对象 / 自定义模板

所有模板定义在 [`scripts/templates.json`](scripts/templates.json) 中。修改受众、语气或结构，直接编辑 JSON 即可，无需改动 Python 代码：

```jsonc
// 示例：把 brief 模板从面向高管改为面向投资人
{
  "brief": {
    "file_suffix": "_InvestorBrief.md",
    "title": "Investor Brief",
    "sections": [
      {
        "heading": "Investor Brief",
        "prompt": "Based on the sources in this notebook, write a one-page brief for angel investors. Focus on market opportunity, traction metrics, competitive moat, and investment thesis. Keep it under 400 words."
      }
    ]
  }
}
```

你也可以**新增全新的模板** —— 只需在 `templates.json` 中添加一个新 key，它会自动出现在 `--template` 的可选值和 `--auto-route` 的匹配规则中。

---

### 子命令：`quiz` + `evaluate`（Discord 互动测验）

这两个子命令专为 agent（如 OpenClaw）编排的 Discord 互动答题设计，不需要终端交互。

**第一步 — 生成问题：**
```bash
python3 distill.py quiz \
  --keywords "机器学习" \
  --count 10
```

输出（JSON）：
```json
{
  "notebook_id": "abc123",
  "notebook_name": "ML Research Notes",
  "questions": [
    "为什么 dropout 在推理阶段和训练阶段的行为不同？",
    "..."
  ],
  "total": 10
}
```

**第二步 — 评估用户答案：**
```bash
python3 distill.py evaluate \
  --notebook-id "abc123" \
  --question "为什么 dropout 在推理阶段和训练阶段的行为不同？" \
  --answer "因为推理时不需要随机性"
```

输出（JSON）：
```json
{
  "question": "为什么 dropout ...",
  "user_answer": "因为推理时不需要随机性",
  "feedback": "答对的部分：... 遗漏的关键点：... 完整答案：..."
}
```

**Discord Agent 编排流程：**
```
Agent 调用 quiz → 获取问题列表
  → 把 Q1 发到 Discord
  → 等待用户回复
  → 带用户回复调用 evaluate
  → 把 NLM 反馈发到 Discord
  → 发 Q2 → 循环
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

# 第二步：用模板蒸馏
python3 distill.py distill \
  --keywords "量子计算" \
  --topic "QuantumComputing" \
  --vault-dir ~/Obsidian/Vault \
  --template report --lang zh
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
       └─ 执行 distill（--template 或 --mode）→ 写入 Obsidian vault
```

### 自然语言触发示例（在 OpenClaw 中）

```
# 蒸馏已有笔记本
"提取'量子计算'笔记本的摘要，存到 Obsidian"
"用 glossary 模式处理 ML Research 笔记本"

# 使用模板蒸馏
"用 brief 模板蒸馏财报笔记本"
"生成 AI Research 笔记本的深度报告"

# 先调研再蒸馏
"研究一下 transformer architecture，蒸馏后存入知识库"

# 归档讨论结论
"把这段对话的结论存到 Obsidian"
```

---

## Discord 命令示例

在 Discord 中通过 OpenClaw Agent 使用本技能时，用户发自然语言指令，Agent 将其翻译为 `distill.py` 的对应调用。

### 模板快捷指令

| 用户在 Discord 说 | Agent 调用 |
|------------------|-----------|
| `[URL 或关键词] --audio` | `--template audio-popular`（大众向） |
| `[URL 或关键词] --audio --pro` | `--template audio-pro`（从业者向） |
| `[URL 或关键词] --brief` | `--template brief` |
| `[URL 或关键词] --slides` | `--template slides` |
| `[URL 或关键词] --notes` | `--template notes` |
| `[URL 或关键词] --plan` | `--template plan` |
| `[URL 或关键词] --report` | `--template report` |

### 受众与语气覆盖

| 用户说 | Agent 解读 |
|--------|-----------|
| `--audience exec` 或 `给CEO/高管看` | 使用 `brief` 模板 |
| `--audience tech` 或 `给工程师看` | 使用 `report` 或 `notes` 模板 |
| `--tone casual` 或 `科普向` | 使用 `audio-popular`（对话式，大众受众） |
| `--tone pro` 或 `专业向` | 使用 `audio-pro`（从业者深度） |
| `--lang zh` 或 `用中文` | 追加 `--lang zh` 参数 |

### Discord 交互示例

```
# 自动路由（Agent 根据笔记本名称推断模板）
用户: 蒸馏一下 "Q4 财报" 这个笔记本
Agent: distill --keywords "Q4 财报" --auto-route ...
→ 匹配到 "财报/earnings" 关键词 → 自动路由到 brief 模板

# 指定模板
用户: 把 AI Trends 笔记本做成播客脚本
Agent: distill --keywords "AI Trends" --template audio-popular ...

# 指定受众
用户: 生成 transformer 的专业播客，给工程师听
Agent: distill --keywords "transformer" --template audio-pro ...

# 幻灯片 + 中文
用户: 把这个笔记本做成演讲幻灯片，用中文
Agent: distill --keywords "..." --template slides --lang zh ...

# 先调研再出报告
用户: 调研一下量子计算，然后出一份深度报告
Agent（第一步）: research --topic "量子计算"
Agent（第二步）: distill --keywords "量子计算" --template report --lang zh ...
```

### 互动测验（Discord Quiz 流程）

```
用户: 考考我 ML Research 笔记本的内容，出 5 题
Agent → quiz --keywords "ML Research" --count 5 --lang zh
  → JSON 输出: { "notebook_id": "...", "questions": [...], "total": 5 }
  → Agent 公告: "来，5 道题（来源：ML Research · ID: abc12345）"
  → 发送 Q1，等待用户回复
  → evaluate --notebook-id "..." --question "..." --answer "<用户回复>" --lang zh
  → 将 NLM 反馈发回 Discord，进入 Q2
  → 循环直到全部题目完成
```

> **注意：** Agent 在发出第一道题之前，**必须**公告笔记本名称和 ID 前 8 位，让用户确认题目来自 NotebookLM 原始资料，而非 Agent 自身知识。

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
        ├── MyNotebook_ExecutiveBrief.md    ← --template brief
        ├── MyNotebook_DeepDiveReport.md    ← --template report
        └── MyNotebook_Slides.md            ← --template slides
```

---

## 自定义模板

所有模板定义在 [`scripts/templates.json`](scripts/templates.json) 中。增删或修改模板无需改动 Python 代码。

每个模板的结构：

```jsonc
{
  "模板名称": {
    "file_suffix": "_OutputFile.md",                    // 输出文件后缀
    "title": "显示标题",                                 // 笔记标题
    "auto_route_keywords": ["关键词1", "keyword2"],      // --auto-route 匹配关键词
    "sections": [                                        // 一个或多个 prompt 分段
      {
        "heading": "章节标题",                            // 输出中的 ## 标题
        "prompt": "发送给 NotebookLM 的提示词"            // 实际查询内容
      }
    ]
  }
}
```

**自定义技巧：**
- 单分段模板（如 `brief`）发送一次 prompt，产出精简内容
- 多分段模板（如 `report` 4 段）每段单独查询 NLM，适合复杂长文
- 修改 `templates.json` 后运行 `distill.py distill --help` 可验证新模板已生效

---

## 输出语言

默认输出为英文。使用 `--lang zh` 可切换为中文输出，适用于 `distill`、`quiz`、`evaluate` 三个子命令：

```bash
python3 distill.py distill --keywords "Machine Learning" --topic "AI" \
  --vault-dir ~/Obsidian/Vault --template notes --lang zh
```

## 关于 NotebookLM 对话历史的说明

脚本内部使用 `notebooklm ask --new` 命令，该命令创建的是**临时 CLI 会话**，不会出现在 NotebookLM 网页端的对话历史中。这是预期行为 —— CLI 与 Web UI 使用独立的会话空间。

**含义：** distill、quiz、evaluate 的查询不会显示在笔记本的历史记录里，但回答仍然来自你指定笔记本的原始资料。

**如何验证来源：** 蒸馏完成后，可将输出中的关键短语粘贴到 NotebookLM 网页端搜索，确认它来自原始资料。

## 常见问题

| 错误 | 解决方案 |
|---|---|
| `notebooklm: command not found` | 使用 `--cli-path $(which notebooklm)` 或重新安装 `pip3 install notebooklm-py` |
| `No notebooks matched` | 运行 `notebooklm list` 查看精确标题，调整 `--keywords` |
| 认证失败 / session 过期 | 运行 `notebooklm login` 刷新 `~/.book_client_session` |
| 蒸馏时速率限制或超时 | 内置重试逻辑可处理大多数情况；大笔记本建议先用 `--template brief` 或 `--mode summary` |
| 找不到模板 | 检查 `scripts/templates.json` 文件是否存在且 JSON 格式正确；运行 `distill.py distill --help` 验证 |

---

## 许可证

MIT
