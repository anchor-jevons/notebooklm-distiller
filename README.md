# NotebookLM Distiller

An [OpenClaw](https://github.com/openclaw) skill that extracts knowledge from Google NotebookLM notebooks and writes structured Markdown notes to your Obsidian vault — with optional voice narration.

> **Version 3.0** — New: `generate-audio` subcommand for official NotebookLM Audio Overview (Deep Dive / Brief / Critique / Debate); `--voice` flag on `distill` for edge-tts narration of deep reports; type-safety fixes; `audio-popular`/`audio-pro` templates moved to internal-only.

---

## Features

- **`distill`** — Extract knowledge from existing NotebookLM notebooks into Obsidian
  - **Legacy modes:** `qa` (15-20 deep Q&A pairs), `summary` (5-section expert knowledge map), `glossary` (15-30 domain terms)
  - **Output templates:** `brief`, `notes`, `report`, `slides`, `plan` — structured multi-section extraction
  - **`--voice`** *(NEW)*: convert the distilled report to speech via edge-tts (MP3 saved alongside the markdown)
  - **`--auto-route`**: infer the best template from the notebook name automatically
  - Keyword-based notebook matching (case-insensitive substring)
  - Auto-generated YAML frontmatter compatible with Obsidian

- **`generate-audio`** *(NEW)* — Trigger official NotebookLM Audio Overview
  - Formats: `deep-dive`, `brief`, `critique`, `debate`
  - Configurable language (`zh` default), length (`short` / `medium` / `long`), and `--custom-prompt`
  - Backed by NotebookLM's native audio engine — no TTS synthesis

- **`generate-slides`** *(NEW)* — Trigger official NotebookLM Slide Deck generation
  - Formats: `detailed` (default) \| `presenter`
  - Configurable language (`zh_Hans` default), length (`default` \| `short`), and `--custom-prompt`
  - Backed by NotebookLM's native presentation engine

- **`quiz`** — Generate quiz questions as JSON for agent-orchestrated interactive sessions (e.g. Discord)
- **`evaluate`** — Evaluate a user's answer against notebook sources; returns structured feedback as JSON
- **`research`** — Start a NotebookLM web research session on any topic, wait for completion, output notebook ID for follow-up
- **`persist`** — Write any Markdown content directly into Obsidian with auto-generated frontmatter

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

**4. (Optional) Install edge-tts for `--voice` narration:**
```bash
pip3 install edge-tts
```

**Requirements:** Python 3.9+, `notebooklm-py`. `edge-tts` only needed for `--voice`.

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
| `--voice` | | **(NEW)** Convert distilled report to speech via edge-tts. Provide a voice name (e.g. `zh-CN-YunxiNeural`). Saves `.mp3` alongside the `.md` file. |
| `--writeback` | | Also write distilled content back into the NotebookLM notebook as a source note |
| `--cli-path` | | Path to `notebooklm` binary if not in `$PATH` |

**Priority:** `--template` > `--auto-route` > `--mode`

---

### Output Templates

Templates define **what you extract** and **how it's structured**. Each template sends one or more prompts to NotebookLM and assembles the responses into a single Obsidian note.

| Name | Output file | Sections | Best for |
|------|-------------|----------|---------|
| `brief` | `_ExecutiveBrief.md` | 1 | Executive summaries, financial reports, quick decision memos |
| `notes` | `_LearningNotes.md` | 1 | Personal study notes, tutorials, courses |
| `report` | `_DeepDiveReport.md` | 4 | Papers, research, in-depth analysis |
| `slides` | `_Slides.md` | 3 | Presentation outlines, talk preparation |
| `plan` | `_ActionPlan.md` | 1 | Project plans, requirements, roadmaps |

> `audio-popular` and `audio-pro` are retained in `templates.json` as **internal dialogue-script templates** — they are not exposed as user-facing commands. Use `generate-audio` for actual audio output.

#### Example: deep dive report with voice narration

```bash
python3 distill.py distill \
  --keywords "LLVM RVV" \
  --topic "ChipDesign" \
  --vault-dir ~/Obsidian/Vault \
  --template report \
  --lang zh \
  --voice zh-CN-YunxiNeural
```

→ Writes `ChipDesign/LLVM_RVV_DeepDiveReport.md` (4-section Chinese report) **and** `LLVM_RVV_DeepDiveReport.mp3` narrated by Yunxi.

**Common edge-tts voices:**

| Voice | Language | Style |
|-------|----------|-------|
| `zh-CN-YunxiNeural` | Chinese (Mandarin) | Male, clear |
| `zh-CN-XiaoxiaoNeural` | Chinese (Mandarin) | Female, warm |
| `en-US-EmmaMultilingualNeural` | English | Female, multilingual |
| `en-GB-RyanNeural` | English (UK) | Male |

List all available voices: `edge-tts --list-voices`

---

### Subcommand: `generate-audio` *(NEW)*

Trigger official NotebookLM Audio Overview generation with full control over format, language, length, and custom guidance.

```bash
python3 ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py generate-audio \
  --keywords "LLVM RVV" \
  --format debate \
  --lang zh \
  --length long \
  --custom-prompt "重点讨论 vsetvli 插入策略对 Simulator 建模的影响"
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `--keywords` | ✅ | Keywords to match against notebook titles |
| `--format` | | `deep-dive` (default) \| `brief` \| `critique` \| `debate` |
| `--lang` | | Audio language: `zh` (default, Chinese) \| `en` |
| `--length` | | `short` (~5 min) \| `medium` (~15 min, default) \| `long` (~30 min) |
| `--custom-prompt` | | Additional guidance injected into the audio prompt |
| `--cli-path` | | Path to `notebooklm` binary |

**Audio formats:**

| Format | Official Description | Natural Language Triggers | Best for |
|--------|----------------------|---------------------------|---------|
| `deep-dive` | A lively and engaging conversation between two hosts who interpret and connect themes in your sources. | `Deep analysis`, `Deep dive`, `Dialogue`, `Popular science` | General learning, concept exploration |
| `brief` | A brief summary designed to help you quickly understand the core ideas of your sources. | `Briefing`, `Summary`, `Quick overview`, `5-minute version` | Quick overviews, busy schedules |
| `critique` | An expert evaluation of your sources, designed to provide constructive feedback to help you improve your content. | `Expert review`, `Find flaws`, `Critical advice`, `Improvement feedback` | Reviewing papers, design docs, proposals |
| `debate` | A thoughtful debate between two hosts, designed to clarify different perspectives on your sources. | `Debate`, `Multi-perspective`, `Pros and cons`, `Brainstorming` | Controversial topics, decision tradeoffs |

#### Discord natural language → `generate-audio` mapping

| User says | Command generated |
|-----------|------------------|
| "Deep analysis" / "Popular science" / "Dialogue" | `--format deep-dive` |
| "Critique" / "Find flaws" / "Expert review" | `--format critique` |
| "Debate" / "Pros and cons" / "Brainstorming" | `--format debate` |
| "Briefing" / "Summary" / "5-minute version" | `--format brief` |
| + "English version" | `+ --lang en` |
| + "Longer" / "30 minutes" | `+ --length long` |
| + "Focus on X" | `+ --custom-prompt "Focus on X"` |

---

### Two audio workflows compared

| | `distill --voice` | `generate-audio` |
|---|---|---|
| **Content source** | distill.py generates report → strip markdown → TTS | NotebookLM's native audio engine |
| **Content control** | Very high — exact report content, word for word | Medium — format + custom prompt guides it |
| **Voice quality** | edge-tts (Microsoft Neural TTS, excellent) | NotebookLM native (Google, natural conversation) |
| **Output style** | Single narrator, structured prose | Two-host dialogue (Deep Dive) or debate |
| **Best for** | "I want every word to be actionable information" | "I want a natural listening experience" |

---

### Subcommand: `quiz` + `evaluate` (Discord interactive quiz)

**Step 1 — Generate questions:**
```bash
python3 distill.py quiz \
  --keywords "machine learning" \
  --count 10 \
  --lang zh
```

Output (JSON):
```json
{
  "notebook_id": "abc123",
  "notebook_name": "ML Research Notes",
  "questions": ["Why does dropout work differently at inference time?", "..."],
  "total": 10
}
```

**Step 2 — Evaluate a user's answer:**
```bash
python3 distill.py evaluate \
  --notebook-id "abc123" \
  --question "Why does dropout work differently at inference time?" \
  --answer "Because we don't want randomness when predicting" \
  --lang zh
```

**Agent orchestration flow (Discord):**
```
Agent calls quiz → gets questions list
  → announces: "来，N 道题（来源：{notebook_name} · ID: {notebook_id[:8]}）"
  → posts Q1 to Discord → waits for user reply
  → calls evaluate → posts feedback
  → posts Q2 → repeat until done
```

---

### Subcommand: `research`

Create a new NotebookLM notebook from web research and wait for completion.

```bash
python3 distill.py research --topic "Quantum Computing" --mode deep
```

Output: prints notebook ID and name. Follow up with `distill` to extract into Obsidian.

---

### Subcommand: `persist`

Write any Markdown content into Obsidian with auto-generated YAML frontmatter.

```bash
python3 distill.py persist \
  --vault-dir "/path/to/Obsidian/Vault" \
  --path "Notes/2026-03-14-meeting.md" \
  --title "Team Meeting Notes" \
  --content "Key decisions: ..." \
  --tags "meeting,notes"
```

---

## Integration with DeepReader

This skill handles **distillation only**. For the full **URL → NotebookLM → Obsidian** pipeline, pair it with [DeepReader](https://github.com/astonysh/OpenClaw-DeepReeder).

```
User: "Read https://example.com/paper and distill it into my Obsidian"
  │
  ├─ DeepReader: fetch → parse → upload to NotebookLM → returns notebook_title
  │
  └─ NotebookLM Distiller: match by title → distill → write .md → (optional) .mp3
```

---

## Customizing Templates

All templates live in [`scripts/templates.json`](scripts/templates.json). Edit, add, or remove templates without touching Python.

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

After editing, run `distill.py distill --help` to verify your template appears in `--template` choices.

---

## Language output

- `distill`, `quiz`, `evaluate`: default `en`; add `--lang zh` for Chinese
- `generate-audio`: default `zh`; add `--lang en` for English audio

---

## Troubleshooting

| Error | Fix |
|---|---|
| `notebooklm: command not found` | `pip3 install notebooklm-py` or use `--cli-path` |
| `No notebooks matched` | Run `notebooklm list` to verify exact titles, adjust `--keywords` |
| Auth failure / session expired | `notebooklm login` to refresh `~/.book_client_session` |
| `edge-tts not found` | `pip3 install edge-tts` (only needed for `--voice`) |
| `notebooklm audio` not supported | Update notebooklm-py: `pip3 install -U notebooklm-py` |
| Rate limit / timeout | Built-in retry handles most cases; try `--template brief` or `--mode summary` first |
| Template not found | Verify `scripts/templates.json` exists and is valid JSON |

---

## License

MIT
