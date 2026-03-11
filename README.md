# NotebookLM Distiller

An [OpenClaw](https://github.com/openclaw) skill that extracts knowledge from Google NotebookLM notebooks and writes structured Markdown notes to your Obsidian vault.

> **Version 2.1** — New: output templates (`--template`) for structured extraction (briefs, slides, reports, podcasts, action plans, learning notes). Templates are externalized in `templates.json` for easy customization.

---

## Features

- **`distill`** — Extract knowledge from existing NotebookLM notebooks into Obsidian
  - **Legacy modes:** `qa` (15-20 deep Q&A pairs), `summary` (5-section expert knowledge map), `glossary` (15-30 domain terms)
  - **Output templates** (NEW): `brief`, `notes`, `report`, `slides`, `plan`, `audio-popular`, `audio-pro` — structured extraction with multi-section prompts for complex formats
  - **Auto-routing** (NEW): `--auto-route` infers the best template from the notebook name
  - Keyword-based notebook matching (case-insensitive substring)
  - Auto-generated YAML frontmatter compatible with Obsidian
- **`quiz`** — Generate quiz questions as JSON for agent-orchestrated interactive sessions (e.g. Discord)
- **`evaluate`** — Evaluate a user's answer against notebook sources; returns structured feedback as JSON
- **`research`** — Start a NotebookLM web research session on any topic, wait for completion, output the notebook ID for follow-up distillation
- **`persist`** — Write any Markdown content directly into your Obsidian vault with frontmatter

No web-scraping dependencies required — pairs with [DeepReader](https://github.com/astonysh/OpenClaw-DeepReeder) for full URL-to-Obsidian automation.

---

## Installation

**1. Copy the skill into OpenClaw:**
```bash
cp -r notebooklm-distiller ~/.openclaw/skills/
```

**2. Install the NotebookLM CLI:**
```bash
pip3 install notebooklm-py
```

**3. Authenticate with Google (once only):**
```bash
notebooklm login
# Opens a browser — log in with your Google account linked to NotebookLM
```

**Requirements:** Python 3.10+, no extra pip packages beyond `notebooklm-py`.

---

## Usage

### Subcommand: `distill`

Extract knowledge from one or more notebooks whose titles match your keywords.

```bash
python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py distill \
  --keywords "machine learning" "transformer" \
  --topic "ML Research" \
  --vault-dir "/path/to/your/Obsidian/Vault" \
  --mode qa
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `--keywords` | ✅ | One or more words to match against notebook titles |
| `--topic` | ✅ | Subfolder name inside `--vault-dir` for the output file |
| `--vault-dir` | ✅ | Path to your Obsidian vault (or any output directory) |
| `--mode` | | Legacy: `qa` (default), `summary`, or `glossary`. Ignored when `--template` or `--auto-route` matches. |
| `--template` | | Use a named output template (see **Output Templates** below) |
| `--auto-route` | | Infer the best template automatically from notebook name keywords. Falls back to `--mode` if no match. |
| `--lang` | | Output language: `en` (default) or `zh` (Chinese) |
| `--writeback` | | Also write distilled content back into the NotebookLM notebook as a source note |
| `--cli-path` | | Path to `notebooklm` binary if not in `$PATH` |

**Priority:** `--template` > `--auto-route` > `--mode`

---

### Output Templates

Templates define **what you extract** from a notebook and **how it's structured**. Each template sends one or more prompts to NotebookLM and assembles the responses into a single Obsidian note.

| Name | Output file | Sections | Best for |
|------|-------------|----------|---------|
| `brief` | `_ExecutiveBrief.md` | 1 | Executive summaries, financial reports, quick decision memos |
| `notes` | `_LearningNotes.md` | 1 | Personal study notes, tutorials, courses |
| `report` | `_DeepDiveReport.md` | 4 | Papers, research, in-depth analysis |
| `slides` | `_Slides.md` | 3 | Presentation outlines, talk preparation |
| `plan` | `_ActionPlan.md` | 1 | Project plans, requirements, roadmaps |
| `audio-popular` | `_AudioPodcast_Popular.md` | 1 | Podcast scripts for general audience |
| `audio-pro` | `_AudioPodcast_Pro.md` | 1 | Podcast scripts for industry practitioners |

> Templates with multiple sections make separate NLM calls per section, producing richer output for complex formats.

#### Usage examples

**Generate an executive brief:**
```bash
python3 distill.py distill \
  --keywords "Q4 Revenue" \
  --topic "Finance" \
  --vault-dir ~/Obsidian/Vault \
  --template brief \
  --lang zh
```
→ Output: `Finance/Q4_Revenue_Report_ExecutiveBrief.md` — a 300-word structured memo with findings, metrics, and action items.

**Generate a podcast script:**
```bash
python3 distill.py distill \
  --keywords "AI Trends" \
  --topic "Podcasts" \
  --vault-dir ~/Obsidian/Vault \
  --template audio-popular
```
→ Output: `Podcasts/AI_Trends_AudioPodcast_Popular.md` — a two-host dialogue script with opening hook, core content, and closing.

**Generate a deep dive report (multi-section):**
```bash
python3 distill.py distill \
  --keywords "transformer" \
  --topic "Research" \
  --vault-dir ~/Obsidian/Vault \
  --template report \
  --lang zh
```
→ Output: `Research/Transformer_DeepDiveReport.md` — 4 sections (Executive Summary & Background → Core Analysis → Comparative Analysis & Insights → Recommendations & Limitations), each from a separate NLM call.

**Use auto-routing (let the notebook name decide):**
```bash
python3 distill.py distill \
  --keywords "Q3 earnings" \
  --topic "Finance" \
  --vault-dir ~/Obsidian/Vault \
  --auto-route
```
→ Notebook name contains "earnings" → auto-routes to `brief` template. If no keyword matches, falls back to `--mode` (default: `qa`).

#### Changing the target audience or tone

Templates are defined in [`scripts/templates.json`](scripts/templates.json). To change the target audience, tone, or structure of any template, edit the JSON file directly:

```jsonc
// Example: change the brief template to target investors instead of executives
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

You can also **add entirely new templates** — just add a new key to `templates.json` and it will automatically appear in `--template` choices and `--auto-route` matching.

---

### Subcommand: `quiz` + `evaluate` (Discord interactive quiz)

These two subcommands are designed to be orchestrated by an agent (e.g. OpenClaw) to run an interactive quiz inside Discord or any chat interface.

**Step 1 — Generate questions:**
```bash
python3 distill.py quiz \
  --keywords "machine learning" \
  --count 10
```

Output (JSON):
```json
{
  "notebook_id": "abc123",
  "notebook_name": "ML Research Notes",
  "questions": [
    "Why does dropout work differently at inference time than training time?",
    "..."
  ],
  "total": 10
}
```

**Step 2 — Evaluate a user's answer:**
```bash
python3 distill.py evaluate \
  --notebook-id "abc123" \
  --question "Why does dropout work differently at inference time?" \
  --answer "Because we don't want randomness when predicting"
```

Output (JSON):
```json
{
  "question": "Why does dropout work differently...",
  "user_answer": "Because we don't want randomness when predicting",
  "feedback": "What you got right: ... What you're missing: ... Complete answer: ..."
}
```

**Agent orchestration flow (Discord example):**
```
Agent calls quiz → gets questions list
  → posts Q1 to Discord
  → waits for user reply
  → calls evaluate with user's reply
  → posts NLM feedback to Discord
  → posts Q2 → repeat
```

---

### Subcommand: `research`

Create a new NotebookLM notebook from web research on any topic and wait for it to finish.

```bash
python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py research \
  --topic "Quantum Computing" \
  --mode deep
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `--topic` | ✅ | Research topic (used as notebook name) |
| `--mode` | | `deep` (default) or `fast` |
| `--cli-path` | | Path to `notebooklm` binary |

Output: prints the notebook ID and name. Use `distill` to extract results into Obsidian.

**Full research-to-Obsidian workflow:**
```bash
# Step 1: research
python3 distill.py research --topic "Quantum Computing"
# → Notebook: Research: Quantum Computing (ID: abc123)

# Step 2: distill with a template
python3 distill.py distill \
  --keywords "Quantum Computing" \
  --topic "QuantumComputing" \
  --vault-dir ~/Obsidian/Vault \
  --template report --lang zh
```

---

### Subcommand: `persist`

Write any Markdown content into your Obsidian vault with auto-generated YAML frontmatter.

```bash
# From inline content
python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py persist \
  --vault-dir "/path/to/Obsidian/Vault" \
  --path "Notes/2026-03-09-meeting.md" \
  --title "Team Meeting Notes" \
  --content "Key decisions: ..." \
  --tags "meeting,notes,2026"

# From an existing file
python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py persist \
  --vault-dir "/path/to/Obsidian/Vault" \
  --path "Research/draft.md" \
  --file ~/Desktop/draft.md
```

---

## Integration with DeepReader

This skill handles **distillation only**. For the full **URL → NotebookLM → Obsidian** pipeline, pair it with [DeepReader](https://github.com/astonysh/OpenClaw-DeepReeder).

### Combined workflow (inside OpenClaw agent)

```
User: "Read https://example.com/paper and distill it into my Obsidian"
  │
  ├─ DeepReader
  │    ├─ Fetches and parses the URL
  │    ├─ Saves clean .md to memory/inbox/
  │    └─ Uploads to NotebookLM (smart routing: add to existing or create new)
  │         └─ Returns: notebook_title, action
  │
  └─ NotebookLM Distiller
       ├─ Matches notebook by title keyword
       └─ Runs distill (--template or --mode) → writes .md to Obsidian vault
```

### Natural language triggers (inside OpenClaw)

```
# Distill an existing notebook
"提取 'ML Research' 笔记本的摘要，存到 Obsidian"
"distill the Quantum Computing notebook using glossary mode"

# Distill with a template
"用 brief 模板蒸馏财报笔记本"
"generate a deep dive report from the AI Research notebook"

# Research a topic then distill
"研究一下 transformer architecture，蒸馏后存入知识库"

# Persist discussion conclusions
"把这段对话的结论存到 Obsidian"
```

---

## Discord Command Examples

When using this skill inside an OpenClaw agent on Discord, users can issue natural language commands. The agent translates them into `distill.py` calls.

### Template shortcuts

| User says in Discord | Agent calls |
|----------------------|------------|
| `[URL or keywords] --audio` | `--template audio-popular` (general audience) |
| `[URL or keywords] --audio --pro` | `--template audio-pro` (practitioners) |
| `[URL or keywords] --brief` | `--template brief` |
| `[URL or keywords] --slides` | `--template slides` |
| `[URL or keywords] --notes` | `--template notes` |
| `[URL or keywords] --plan` | `--template plan` |
| `[URL or keywords] --report` | `--template report` |

### Audience and tone overrides

| User says | Agent interpretation |
|-----------|---------------------|
| `--audience exec` or `给CEO/高管看` | Uses `brief` template |
| `--audience tech` or `给工程师看` | Uses `report` or `notes` template |
| `--tone casual` or `科普向` | Uses `audio-popular` (dialogue, general audience) |
| `--tone pro` or `专业向` | Uses `audio-pro` (practitioner depth) |
| `--lang zh` or `用中文` | Adds `--lang zh` to the command |

### Example Discord interactions

```
# Auto-routing (agent infers template from notebook name)
用户: 蒸馏一下 "Q4 财报" 这个笔记本
Agent: distill --keywords "Q4 财报" --auto-route ...
→ Matches "earnings/财报" keyword → routes to brief template

# Explicit template
用户: 把 AI Trends 笔记本做成播客脚本
Agent: distill --keywords "AI Trends" --template audio-popular ...

# Professional audience
用户: 生成 transformer 的专业播客，给工程师听
Agent: distill --keywords "transformer" --template audio-pro ...

# Slides for a talk
用户: 把这个笔记本做成演讲幻灯片，用中文
Agent: distill --keywords "..." --template slides --lang zh ...

# Research then distill
用户: 调研一下量子计算，然后出一份深度报告
Agent (step 1): research --topic "量子计算"
Agent (step 2): distill --keywords "量子计算" --template report --lang zh ...
```

### Quiz session (Discord interactive)

```
用户: 考考我 ML Research 笔记本的内容，出 5 题
Agent → quiz --keywords "ML Research" --count 5 --lang zh
  → JSON: { "notebook_id": "...", "questions": [...], "total": 5 }
  → Agent announces: "来，5 道题（来源：ML Research · ID: abc12345）"
  → Posts Q1, waits for user reply
  → evaluate --notebook-id "..." --question "..." --answer "<reply>" --lang zh
  → Posts feedback, moves to Q2
  → Repeats until done
```

> **Note:** The agent always announces the notebook source (`notebook_name` + first 8 chars of `notebook_id`) before the first question so users can verify questions came from NotebookLM, not the agent's own knowledge.

---

## Obsidian Setup

No special template or plugin configuration required. Just point `--vault-dir` to your vault's root or any subfolder. The script creates subdirectories automatically and injects YAML frontmatter that Obsidian reads natively.

**Recommended vault structure:**
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

## Customizing Templates

All templates live in [`scripts/templates.json`](scripts/templates.json). You can edit, add, or remove templates without touching any Python code.

Each template entry has:

```jsonc
{
  "template-name": {
    "file_suffix": "_OutputFile.md",         // filename suffix for Obsidian
    "title": "Human-Readable Title",         // shown in note heading
    "auto_route_keywords": ["keyword1", "keyword2"],  // for --auto-route matching
    "sections": [                            // one or more prompt sections
      {
        "heading": "Section Heading",        // markdown ## heading in output
        "prompt": "Prompt text sent to NLM"  // the actual NLM query
      }
    ]
  }
}
```

**Tips:**
- Single-section templates (e.g. `brief`) send one prompt and produce a concise output
- Multi-section templates (e.g. `report` with 4 sections) make separate NLM calls per section for richer, non-truncated output
- After editing `templates.json`, run `distill.py distill --help` to verify your new template appears in `--template` choices

---

## Notes on output language

By default, `distill`, `quiz`, and `evaluate` reply in English. Add `--lang zh` to get Chinese output:

```bash
python3 distill.py distill --keywords "Machine Learning" --topic "AI" \
  --vault-dir ~/Obsidian/Vault --template notes --lang zh
```

## Notes on NLM conversation history

The `notebooklm ask --new` command used internally creates **ephemeral CLI sessions** that are not visible in the NotebookLM web interface. This is expected behaviour — the CLI and web UI maintain separate conversation spaces.

**What this means:** You will not see distill, quiz, or evaluate queries appear in your NotebookLM notebook history. The answers are still generated from your notebook's sources, but the conversation is not persisted.

**To verify source authenticity:** After distilling, search a key phrase from the output in your original NotebookLM sources. The CLI always scopes queries to the specified `--notebook` ID and does not use outside knowledge.

## Troubleshooting

| Error | Fix |
|---|---|
| `notebooklm: command not found` | Use `--cli-path $(which notebooklm)` or install with `pip3 install notebooklm-py` |
| `No notebooks matched` | Run `notebooklm list` to check exact notebook titles, adjust `--keywords` |
| Auth failure / session expired | Run `notebooklm login` to refresh `~/.book_client_session` |
| Rate limit / timeout on distill | Built-in retry logic handles most cases; for large notebooks try `--template brief` or `--mode summary` first |
| Template not found | Verify `scripts/templates.json` exists and is valid JSON; run `distill.py distill --help` to check |

---

## License

MIT
