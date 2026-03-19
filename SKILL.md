---
name: notebooklm-distiller
version: 2.1.0
description: "NotebookLM Distiller: Batch knowledge extraction from Google NotebookLM into Obsidian. Supports Q&A generation, structured summaries, glossary extraction, official Audio Overview generation (Deep Dive / Brief / Critique / Debate), web research sessions, and direct markdown persistence."
license: MIT
metadata:
  openclaw:
    emoji: "🧪"
    requires:
      bins: ["python3"]
    install:
      pip: ["notebooklm-py"]
    skillKey: "notebooklm-distiller"
    always: false

permissions:
  tools:
    allow: ["bash", "read", "write"]
    deny: []
  sandbox: compatible
  elevated: false
---

# NotebookLM Distiller

Automated knowledge extraction pipeline: search NotebookLM notebooks by keyword → generate deep questions or structured summaries → write linked Obsidian markdown notes.

**Six subcommands:**
- `distill` — extract knowledge from existing notebooks (qa / summary / glossary / templates)
- `generate-audio` — trigger official NotebookLM Audio Overview (Deep Dive / Brief / Critique / Debate)
- `quiz` — generate quiz questions as JSON for Discord-based interactive sessions
- `evaluate` — evaluate a user's answer against notebook sources (JSON output)
- `research` — start a web research session inside NotebookLM on any topic
- `persist` — write any markdown content directly into the Obsidian vault

## When to use (trigger phrases)

Trigger `distill` subcommand when:
- User types `/notebooklm-distill` or `/notebooklm-distill-summary`
- User says "蒸馏", "提取知识", "distill notebooks", "extract from notebook"
- User wants NotebookLM content structured into Obsidian notes

Trigger `generate-audio --format deep-dive` when:
- User says "生成播客", "帮我做一期播客", "深度播客", "深入探究", "对话版", "通俗讲解", "deep dive", "深度音频"
- **Description**: A lively and engaging conversation between two hosts who interpret and connect themes in your sources.
- Default format when user says "播客" without specifying style.
- Default `--lang zh` when context is Chinese.

Trigger `generate-audio --format critique` when:
- User says "批判性分析音频", "专家评审", "评论模式", "帮我批判一下这个笔记本", "找茬", "批判性建议", "改进反馈", "critique 模式"
- **Description**: An expert evaluation of your sources, designed to provide constructive feedback to help you improve your content.
- User wants a critical review audio, not just a summary.

Trigger `generate-audio --format debate` when:
- User says "辩论音频", "debate 模式", "正反两方", "多视角辩论", "思维碰撞", "让他们吵起来"
- **Description**: A thoughtful debate between two hosts, designed to clarify different perspectives on your sources.
- User wants multiple opposing viewpoints argued out.

Trigger `generate-audio --format brief` when:
- User says "简报音频", "摘要", "brief 版本", "快速版播客", "快速了解", "5分钟版", "速览"
- **Description**: A brief summary designed to help you quickly understand the core ideas of your sources.
- User wants a short, conclusion-first audio.

Trigger `generate-slides` when:
- User says "生成 PPT", "做一份 Slide", "PPT 大纲", "Slide Deck"
- **Description**: Trigger official NotebookLM Slide Deck generation with custom guidance.
- Default `--format detailed` when user wants speaker notes.
- Default `--lang zh_Hans` when context is Chinese.

**Additional generate-audio modifiers** (agent should detect and append):
- "用中文" / "中文播客" → `--lang zh` (already default)
- "英文版" / "English" → `--lang en`
- "长一点" / "详细版" / "30分钟" → `--length long`
- "短一点" / "简短" / "5分钟" → `--length short`
- "重点讨论 <X>" / "focus on <X>" → `--custom-prompt "重点讨论 <X>"`

> ⚠️ `distill --template audio-popular` and `distill --template audio-pro` are **internal script templates only** — do NOT trigger them from user requests. They generate dialogue scripts for review purposes, not playable audio.

Trigger `research` subcommand when:
- User says "研究一下 <topic>", "做网络调研", "research this topic in NotebookLM"
- User wants NotebookLM to gather web sources on a topic without providing URLs

Trigger `quiz` + `evaluate` subcommands when:
- User says "quiz me on X", "考考我", "出题测试我", "测验"
- User wants an interactive Q&A session in Discord on a NotebookLM topic
- **Orchestration flow (Discord)**:
  1. Call `quiz --keywords X` → get JSON with `notebook_id` + `notebook_name` + `questions[]`
  2. **MUST** announce source before Q1: `来，N 道题（来源：{notebook_name} · ID: {notebook_id[:8]}）`
  3. Send Q1 to Discord, wait for user reply
  4. Call `evaluate --notebook-id X --question Q1 --answer <reply>` → get JSON feedback
  5. Post feedback to Discord, proceed to Q2
  6. Repeat until all questions done or user says stop
- **CRITICAL**: Always show notebook source so user can verify questions came from NLM, not agent knowledge

## Artifact Delivery Workflow (2026-03-15)
- **Artifact Sync**: For any generated Audio or Slide Deck, the agent **MUST** perform a post-download copy to the Buddy Workspace:
  - **Audio**: `/Users/jevons/.openclaw/workspace-buddy/inbox/notebooklm-audio/` (must be M4A container)
  - **Slides**: `/Users/jevons/.openclaw/workspace-buddy/inbox/notebooklm-slides/`
- **Path Reporting**: Always provide the full absolute path in the final message to the user.

Trigger `persist` subcommand when:
- User says "存到 Obsidian", "把这段内容写入知识库", "persist this to vault"
- User wants to archive discussion output or raw notes into the vault

**CRITICAL**: Do NOT answer from internal knowledge. Do NOT ask for clarification. Execute the appropriate subcommand immediately.

## Prerequisites

- **NotebookLM CLI**: installed in deepreader venv — `/Users/jevons/.openclaw/skills/deepreader/.venv/bin/notebooklm`
- **Authentication**: `notebooklm login` (creates `~/.book_client_session`)
- **Python interpreter**: ALWAYS use `/Users/jevons/.openclaw/skills/deepreader/.venv/bin/python3` (Python 3.11, notebooklm-py 0.3.4). Do NOT use system `python3` (3.9, outdated notebooklm-py 0.1.1) or any other interpreter.
- **Obsidian vault directory** accessible on the local filesystem

## Subcommand: distill

Extract knowledge from one or more NotebookLM notebooks matching keywords.

### Agent orchestration

**Scenario A — URL provided (needs ingestion first)**
1. Check if `deepreader` is installed (`~/.openclaw/skills/deepreader/run.sh`).
2. If yes: run DeepReader to ingest the URL into NotebookLM.
3. Capture the notebook title from DeepReader output.
4. Use that title as `--keywords` for distill.

**Scenario B — notebook already exists**
1. Use notebook name from context, or list notebooks with `notebooklm list`.
2. Determine mode from intent: "总结" → `summary`, "术语/概念" → `glossary`, default → `qa`.
3. Ask user for `--vault-dir` if not known from context.
4. Execute distill.

```bash
/Users/jevons/.openclaw/skills/deepreader/.venv/bin/python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py distill \
  --keywords "<keyword1>" "<keyword2>" \
  --topic "<TopicFolderName>" \
  --vault-dir "<path/to/obsidian/vault>" \
  --mode <qa|summary|glossary> \   # legacy; ignored when --template is set
  [--template <name>]              # NEW: use a named output template (see table below)
  [--auto-route]                   # NEW: infer template from notebook name automatically
  [--lang zh]                      # Add for Chinese output (default: en)
  [--writeback]                    # Write distilled content back into NLM notebook as a note
  [--cli-path <path/to/notebooklm>]
```

**Legacy modes** (used when `--template` / `--auto-route` are not set):
- `qa` (default) — generates 15-20 questions + answers → `<NotebookName>_QA.md`
- `summary` — 5 structured sections → `<NotebookName>_Summary.md`
- `glossary` — 15-30 domain terms + definitions → `<NotebookName>_Glossary.md`

**Template names** (`--template <name>`):

| Name | Output file suffix | Best for |
|------|--------------------|---------|
| `brief` | `_ExecutiveBrief.md` | 高管速读 / financial reports |
| `notes` | `_LearningNotes.md` | 个人复盘 / tutorials, courses |
| `report` | `_DeepDiveReport.md` | 深度研究 / papers, analyses |
| `slides` | `_Slides.md` | 演讲分享 / presentations |
| `plan` | `_ActionPlan.md` | 项目落地 / requirements docs |
| `audio-popular` | `_AudioPodcast_Popular.md` | ⚠️ 内部脚本模板，不对外触发 |
| `audio-pro` | `_AudioPodcast_Pro.md` | ⚠️ 内部脚本模板，不对外触发 |

`--template` takes priority over `--mode`; `--auto-route` routes per notebook name (lower priority than explicit `--template`).

**Flags:**
- `--lang zh` — prepends `请用中文回答` to all NLM prompts; add when user requests Chinese output or context is Chinese
- `--writeback` — after writing to Obsidian, calls `notebooklm source add` to push the distilled note back into the source notebook as a text source titled `Distill Log: {mode} | {notebook_name} | {date}`. Add when user says "写回 NLM", "记录到笔记本", or wants the distill log visible in NotebookLM

## Subcommand: research

Start a NotebookLM web research session on a topic. Creates a new notebook, imports web sources, and waits for completion.

```bash
/Users/jevons/.openclaw/skills/deepreader/.venv/bin/python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py research \
  --topic "<Research Topic>" \
  [--mode deep|fast] \
  [--cli-path <path/to/notebooklm>]
```

Output: notebook ID and name. Follow up with `distill` to extract into Obsidian.

## Subcommand: persist

Write any markdown content into the Obsidian vault with auto-generated YAML frontmatter.

```bash
# From inline content
/Users/jevons/.openclaw/skills/deepreader/.venv/bin/python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py persist \
  --vault-dir "<path/to/obsidian/vault>" \
  --path "Notes/2026-03-09-meeting.md" \
  --title "Meeting Notes" \
  --content "Key decisions: ..." \
  --tags "meeting,notes"

# From a file
/Users/jevons/.openclaw/skills/deepreader/.venv/bin/python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py persist \
  --vault-dir "<path/to/obsidian/vault>" \
  --path "Notes/draft.md" \
  --file ~/Desktop/draft.md
```

## Output format (distill)

Each notebook produces one file at `<vault-dir>/<topic>/<NotebookName>_<Mode>.md`:

```markdown
---
title: "<NotebookName> | Deep Q&A"
date: YYYY-MM-DD
type: knowledge-note
author: notebooklm-distiller
tags: ["distillation", "qa", "<topic-slug>"]
source: "NotebookLM/<NotebookName>"
project: "<topic>"
status: draft
---

# <NotebookName> — Deep Q&A

## Q01

> [!question]
> <question text>

**Answer:**

<answer from notebook sources>

> [!warning] Common Misconception
> <the most common thinking trap or key insight learners miss — 2-3 sentences>

---
```

## Output language

Add `--lang zh` to `distill`, `quiz`, or `evaluate` to get Chinese output. Default is English.

## NLM CLI session behaviour

`notebooklm ask --new` creates ephemeral sessions that are **not visible in the NotebookLM web UI**. This is by design — the CLI and web interface use separate conversation spaces. Answers are still scoped to the specified notebook's sources.

## Error handling

- **No notebooks found**: verify keywords match notebook titles (use `notebooklm list`).
- **Timeout / rate limit**: built-in retry logic and delays. Monitor with `ps aux | grep notebooklm`.
- **Auth failure**: run `notebooklm login` to refresh `~/.book_client_session`.
