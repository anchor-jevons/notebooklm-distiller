# NotebookLM Distiller

一个 [OpenClaw](https://github.com/openclaw) 技能插件，用于从 Google NotebookLM 笔记本中提取知识，并将其写入 Obsidian 的结构化 Markdown 笔记 —— 支持可选的语音朗读功能。

> **版本 3.0** — 新增：`generate-audio` 子命令，用于生成官方 NotebookLM 音频概览（深度探讨/简报/批判/辩论）；`distill` 新增 `--voice` 参数，支持通过 edge-tts 朗读深度报告；类型安全修复；`audio-popular`/`audio-pro` 模板移至内部使用。

---

## 功能特性

- **`distill`** — 从已有 NotebookLM 笔记本中提取知识，写入 Obsidian
  - **传统模式：** `qa`（15-20 对深度问答）、`summary`（五节专家知识地图）、`glossary`（15-30 个领域术语）
  - **输出模板：** `brief`、`notes`、`report`、`slides`、`plan` — 结构化多段落提取
  - **`--voice`** *(新)*：通过 edge-tts 将蒸馏出的报告转为语音（MP3 文件保存在 markdown 旁）
  - **`--auto-route`**：根据笔记本名称自动选择最佳模板
  - 基于关键词的笔记本匹配（大小写不敏感子字符串）
  - 自动生成 Obsidian 兼容的 YAML frontmatter

- **`generate-audio`** *(新)* — 触发官方 NotebookLM 音频概览（Audio Overview）
  - 格式：`deep-dive`（深度探讨）、`brief`（简报）、`critique`（批判）、`debate`（辩论）
  - 可配置语言（默认 `zh`）、长度（`short` / `medium` / `long`）以及 `--custom-prompt`
  - 由 NotebookLM 原生音频引擎驱动 —— 非 TTS 合成

- **`generate-slides`** *(新)* — 触发官方 NotebookLM Slide Deck 生成
  - 格式：`detailed` (默认) \| `presenter`
  - 可配置语言（默认 `zh_Hans`）、长度（`default` \| `short`）以及 `--custom-prompt`
  - 由 NotebookLM 原生演示引擎驱动

- **`quiz`** — 生成测验问题（JSON 格式），供 agent 编排的互动环节（如 Discord）使用
- **`evaluate`** — 将用户答案与笔记本资料源比对评估；返回结构化反馈 JSON
- **`research`** — 对任意主题发起 NotebookLM 网络调研，等待完成后输出笔记本 ID 供后续使用
- **`persist`** — 将任意 Markdown 内容直接写入 Obsidian，并自动生成 frontmatter

无需网络爬虫依赖 —— 可与 [DeepReader](https://github.com/astonysh/OpenClaw-DeepReeder) 配合使用，实现完整的 URL 到 Obsidian 自动化流程。

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

**4. （可选）安装 edge-tts 以支持 `--voice` 语音朗读：**
```bash
pip3 install edge-tts
```

**环境要求：** Python 3.10+，`notebooklm-py`。`edge-tts` 仅在需要 `--voice` 时安装。

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
| `--topic` | ✅ | 输出文件在 `--vault-dir` 下的子目录名称 |
| `--vault-dir` | ✅ | Obsidian vault 路径（或任意输出目录） |
| `--mode` | | 传统模式：`qa`（默认）、`summary` 或 `glossary`。使用 `--template` 或 `--auto-route` 匹配时将被忽略。 |
| `--template` | | 使用命名输出模板（见下文 **输出模板**） |
| `--auto-route` | | 根据笔记本名称中的关键词自动推断最佳模板。若无匹配则回退至 `--mode`。 |
| `--lang` | | 输出语言：`en`（默认）或 `zh`（中文） |
| `--voice` | | **(新)** 通过 edge-tts 将蒸馏的报告转换为语音。提供一个语音名称（例如 `zh-CN-YunxiNeural`）。与 `.md` 文件同名保存为 `.mp3`。 |
| `--writeback` | | 同时将蒸馏结果写回到 NotebookLM 笔记本作为来源笔记 |
| `--cli-path` | | `notebooklm` 可执行文件路径（如果不在 `$PATH` 中） |

**优先级：** `--template` > `--auto-route` > `--mode`

---

### 输出模板

模板定义了**提取什么**以及**如何组织结构**。每个模板向 NotebookLM 发送一个或多个提示词，并将所有回复组装成一篇 Obsidian 笔记。

| 名称 | 输出文件 | 段落数 | 最佳适用场景 |
|------|-------------|----------|---------|
| `brief` | `_ExecutiveBrief.md` | 1 | 高管摘要、财务报告、快速决策备忘录 |
| `notes` | `_LearningNotes.md` | 1 | 个人学习笔记、教程、课程 |
| `report` | `_DeepDiveReport.md` | 4 | 论文、研究、深度分析 |
| `slides` | `_Slides.md` | 3 | 演示大纲、演讲准备 |
| `plan` | `_ActionPlan.md` | 1 | 项目计划、需求制定、路线图 |

> `audio-popular` 和 `audio-pro` 在 `templates.json` 中保留为**内部使用的对话脚本模板** —— 它们不会作为面向用户的命令暴露。如需生成真正的音频输出，请使用 `generate-audio` 命令。

#### 示例：带语音朗读的深度报告

```bash
python3 distill.py distill \
  --keywords "LLVM RVV" \
  --topic "ChipDesign" \
  --vault-dir ~/Obsidian/Vault \
  --template report \
  --lang zh \
  --voice zh-CN-YunxiNeural
```

→ 将写入 `ChipDesign/LLVM_RVV_DeepDiveReport.md`（四段式中文报告）**以及**由 Yunxi 朗读的 `LLVM_RVV_DeepDiveReport.mp3`。

**常用的 edge-tts 语音节点：**

| 语音名 | 语言 | 风格 |
|-------|----------|-------|
| `zh-CN-YunxiNeural` | 中文（普通话） | 男性，清晰 |
| `zh-CN-XiaoxiaoNeural` | 中文（普通话） | 女性，温暖 |
| `en-US-EmmaMultilingualNeural` | 英文 | 女性，多语种 |
| `en-GB-RyanNeural` | 英文（英国） | 男性 |

列出所有可用语音：`edge-tts --list-voices`

---

### 子命令：`generate-audio` *(新)*

触发官方的 NotebookLM 音频概览（Audio Overview）生成，支持全面控制格式、语言、长度和自定义向导提示词。

```bash
python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py generate-audio \
  --keywords "LLVM RVV" \
  --format debate \
  --lang zh \
  --length long \
  --custom-prompt "重点讨论 vsetvli 插入策略对 Simulator 建模的影响"
```

**参数：**

| 参数 | 必填 | 说明 |
|---|---|---|
| `--keywords` | ✅ | 用于匹配笔记本标题的关键词 |
| `--format` | | `deep-dive`（默认）\| `brief` \| `critique` \| `debate` |
| `--lang` | | 音频语言：`zh`（默认中文）\| `en` |
| `--length` | | `short`（约 5 分钟）\| `medium`（约 15 分钟，默认）\| `long`（约 30 分钟） |
| `--custom-prompt` | | 注入到音频提示词中的附加指导信息 |
| `--cli-path` | | `notebooklm` 二进制文件路径 |

**音频格式说明：**

| 格式 | 官方描述 | 自然语言触发词 | 最佳适用场景 |
|--------|----------------------|---------------------------|---------|
| `deep-dive` | 两位主持人之间生动有趣的对话，旨在解读和关联来源中的主题。 | `深度分析`、`深入探究`、`对话版`、`通俗讲解` | 一般性学习，概念探索 |
| `brief` | 简短概要，旨在帮助您快速了解来源的核心思想。 | `简报`、`概要`、`快速了解`、`5分钟版` | 快速概览，时间紧凑场合 |
| `critique` | 对来源的专家评价，旨在提供建设性反馈，帮助您改进内容。 | `专家评审`、`找茬`、`批判性建议`、`改进反馈` | 审查论文、设计文档、提案 |
| `debate` | 两位主持人之间思维缜密的辩论，旨在阐明对来源的不同观点。 | `辩论`、`多方观点`、`正反方`、`思维碰撞` | 争议话题、决策权衡 |

#### Discord 自然语言与 `generate-audio` 的映射关系

| 用户输入 | 生成的命令参数 |
|-----------|------------------|
| "深度分析" / "对话版" / "通俗讲解" | `--format deep-dive` |
| "专家评审" / "挑毛病" / "批判性建议" | `--format critique` |
| "辩论" / "正反两方" / "思维碰撞" | `--format debate` |
| "简报" / "概要" / "5分钟版" | `--format brief` |
| + "英文版" | `+ --lang en` |
| + "长一点" / "30分钟" | `+ --length long` |
| + "重点讨论 X" | `+ --custom-prompt "重点讨论 X"` |

---

### 两种音频工作流对比

| | `distill --voice` | `generate-audio` |
|---|---|---|
| **内容来源** | distill.py 生成报告 → 清除 markdown 标记 → TTS | NotebookLM 原生音频引擎 |
| **内容掌控力** | 极高 —— 精确到逐字朗读报告内容 | 中等 —— 依赖格式和自定义提示词引导 |
| **声音质量** | edge-tts (微软 Neural TTS, 极其出色) | NotebookLM 原生 (Google, 极其自然的对话式) |
| **输出风格** | 单一播音员结构化朗读 | 双主挂对话 (`deep-dive`) 或 辩论式 |
| **适用场景** | "我希望每个字都包含最核心的知识信息" | "我想要一段自然的闲聊式学习听觉体验" |

---

### 子命令：`quiz` 与 `evaluate`（Discord 互动测验）

**第一步 — 生成问题：**
```bash
python3 distill.py quiz \
  --keywords "机器学习" \
  --count 10 \
  --lang zh
```

输出（JSON）：
```json
{
  "notebook_id": "abc123",
  "notebook_name": "ML Research Notes",
  "questions": ["为什么 dropout 在推理阶段的行为不同？", "..."],
  "total": 10
}
```

**第二步 — 评估用户答案：**
```bash
python3 distill.py evaluate \
  --notebook-id "abc123" \
  --question "为什么 dropout 在推理阶段的行为不同？" \
  --answer "因为预测时我们不需要随机性" \
  --lang zh
```

**Agent（Discord）交互编排流程：**
```
Agent 调用 quiz → 获得问题列表
  → 宣告提示: "来，N 道题（来源：{notebook_name} · ID: {notebook_id[:8]}）"
  → 发送 Q1 到 Discord → 等待用户回复
  → 调用 evaluate → 发送反馈结果
  → 发送 Q2 → 循环直至结束
```

---

### 子命令：`research`

对任意主题发起网络调研，在 NotebookLM 中新建笔记本并等待完成。

```bash
python3 distill.py research --topic "量子计算" --mode deep
```

输出：打印笔记本的 ID 与名称。后续可配合 `distill` 使用提取到 Obsidian 中。

---

### 子命令：`persist`

将任意的 Markdown 内容写入 Obsidian，并自动生成 YAML frontmatter。

```bash
python3 distill.py persist \
  --vault-dir "/path/to/Obsidian/Vault" \
  --path "Notes/2026-03-14-meeting.md" \
  --title "Team Meeting Notes" \
  --content "Key decisions: ..." \
  --tags "meeting,notes"
```

---

## 与 DeepReader 整合使用

本技能仅负责**知识蒸馏（提取部分）**。若需完整的 **URL → NotebookLM → Obsidian** 自动化管道，请与 [DeepReader](https://github.com/astonysh/OpenClaw-DeepReeder) 结合使用。

```
用户："读取 https://example.com/paper 并且将内容提取进入 Obsidian"
  │
  ├─ DeepReader: 拉取网页内容 → 文本解析 → 上传至 NotebookLM → 返回 notebook_title (笔记本标题)
  │
  └─ NotebookLM Distiller: 通过标题进行匹配 → 进入蒸馏(distill) → 写入 .md → (可选生成 .mp3)
```

---

## 自定义模板

所有的模板都保存在 [`scripts/templates.json`](scripts/templates.json) 文件中。直接编辑、增加或删除模板，无需修改 Python 代码。

```jsonc
{
  "template-name": {
    "file_suffix": "_OutputFile.md",
    "title": "Human-Readable Title",
    "auto_route_keywords": ["keyword1", "keyword2"],
    "sections": [
      {
        "heading": "Section Heading",
        "prompt": "Prompt text sent to NLM"
      }
    ]
  }
}
```

修改后，运行 `distill.py distill --help` 确保您的模板显示位于 `--template` 选项之中即可使用。

---

## 语言输出支持

- `distill`、`quiz`、`evaluate`: 默认 `en`（英文）；可附加 `--lang zh` 获取中文输出
- `generate-audio`: 默认 `zh`（中文）；可附加 `--lang en` 获取英文音频输出

---

## 疑难排解

| 错误信息 | 解决方案 |
|---|---|
| `notebooklm: command not found` | 执行 `pip3 install notebooklm-py` 或使用 `--cli-path` 参数 |
| `No notebooks matched` | 执行 `notebooklm list` 查证精确标题，修改 `--keywords` 等待匹配 |
| 授权鉴权失败 / 会话断开超时 | 执行 `notebooklm login` 刷新更新 `~/.book_client_session` 会话 |
| `edge-tts not found` | 执行 `pip3 install edge-tts` (仅使用 `--voice` 特性时必需) |
| `notebooklm audio` not supported | 升级更新 notebooklm-py 包: `pip3 install -U notebooklm-py` |
| 请求太频被限流 / 请求超时 | 脚本内部重试机制能应对绝大部分情况；建议尝试优先使用 `--template brief` 或者 `--mode summary` 缩小请求量。|
| Template not found | 验证 `scripts/templates.json` 文件路径存在并且格式是有效合法的 JSON 数据 |

---

## 许可协议

MIT
