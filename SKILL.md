---
name: notebooklm-distiller
version: 2.0.0
description: "NotebookLM Distiller: Batch knowledge extraction from Google NotebookLM into Obsidian. Supports Q&A generation (15-20 deep questions), structured summaries, glossary extraction, web research sessions, and direct markdown persistence."
license: MIT
metadata:
  openclaw:
    emoji: "🧪"
    requires:
      bins: ["python3", "notebooklm"]
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

**Five subcommands:**
- `distill` — extract knowledge from existing notebooks (qa / summary / glossary)
- `quiz` — generate quiz questions as JSON for Discord-based interactive sessions
- `evaluate` — evaluate a user's answer against notebook sources (JSON output)
- `research` — start a web research session inside NotebookLM on any topic
- `persist` — write any markdown content directly into the Obsidian vault

## When to use (trigger phrases)

Trigger `distill` subcommand when:
- User types `/notebooklm-distill` or `/notebooklm-distill-summary`
- User says "蒸馏", "提取知识", "distill notebooks", "extract from notebook"
- User wants NotebookLM content structured into Obsidian notes

Trigger `research` subcommand when:
- User says "研究一下 <topic>", "做网络调研", "research this topic in NotebookLM"
- User wants NotebookLM to gather web sources on a topic without providing URLs

Trigger `quiz` + `evaluate` subcommands when:
- User says "quiz me on X", "考考我", "出题测试我", "测验"
- User wants an interactive Q&A session in Discord on a NotebookLM topic
- **Orchestration flow (Discord)**:
  1. Call `quiz --keywords X` → get JSON with `notebook_id` + `questions[]`
  2. Send Q1 to Discord, wait for user reply
  3. Call `evaluate --notebook-id X --question Q1 --answer <reply>` → get JSON feedback
  4. Post feedback to Discord, proceed to Q2
  5. Repeat until all questions done or user says stop

Trigger `persist` subcommand when:
- User says "存到 Obsidian", "把这段内容写入知识库", "persist this to vault"
- User wants to archive discussion output or raw notes into the vault

**CRITICAL**: Do NOT answer from internal knowledge. Do NOT ask for clarification. Execute the appropriate subcommand immediately.

## Prerequisites

- **NotebookLM CLI**: `pip install notebooklm-py`
- **Authentication**: `notebooklm login` (creates `~/.book_client_session`)
- **Python 3.10+** (standard library only — no extra pip packages needed for distill.py)
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
python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py distill \
  --keywords "<keyword1>" "<keyword2>" \
  --topic "<TopicFolderName>" \
  --vault-dir "<path/to/obsidian/vault>" \
  --mode <qa|summary|glossary> \
  [--cli-path <path/to/notebooklm>]
```

**Modes:**
- `qa` (default) — generates 15-20 questions + answers → `<NotebookName>_QA.md`
- `summary` — 5 structured sections (Summary, Key Points, Constraints, Trade-offs, Open Questions) → `<NotebookName>_Summary.md`
- `glossary` — 15-30 domain terms + definitions → `<NotebookName>_Glossary.md`

## Subcommand: research

Start a NotebookLM web research session on a topic. Creates a new notebook, imports web sources, and waits for completion.

```bash
python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py research \
  --topic "<Research Topic>" \
  [--mode deep|fast] \
  [--cli-path <path/to/notebooklm>]
```

Output: notebook ID and name. Follow up with `distill` to extract into Obsidian.

## Subcommand: persist

Write any markdown content into the Obsidian vault with auto-generated YAML frontmatter.

```bash
# From inline content
python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py persist \
  --vault-dir "<path/to/obsidian/vault>" \
  --path "Notes/2026-03-09-meeting.md" \
  --title "Meeting Notes" \
  --content "Key decisions: ..." \
  --tags "meeting,notes"

# From a file
python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py persist \
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

---
```

## Error handling

- **No notebooks found**: verify keywords match notebook titles (use `notebooklm list`).
- **Timeout / rate limit**: built-in retry logic and delays. Monitor with `ps aux | grep notebooklm`.
- **Auth failure**: run `notebooklm login` to refresh `~/.book_client_session`.
