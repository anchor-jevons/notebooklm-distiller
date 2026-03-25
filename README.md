# NotebookLM Distiller

**NotebookLM Distiller** is a deeply integrated AI agent skill designed to autonomously orchestrate Google's NotebookLM via a headless CLI pipeline. This tool automates the process of knowledge extraction, web research summarization, audio/slide generation, and seamless integration of distilled insights into your local Obsidian vault.

---

## 🌟 Key Capabilities

- **Automated Distillation (`distill`)**: Automatically searches for notebooks matching specific keywords, triggers Google's intelligence (Audio/Briefings), and exports the artifacts.
- **Autonomous Web Research (`research`)**: Bootstraps a fresh notebook, ingests web URLs, processes the context, and generates comprehensive domain expert summaries.
- **Obsidian Vault Integration (`persist`)**: Directly injects synthesized knowledge into your personal Obsidian notes (with auto-generated YAML metadata tags).
- **Audio & Slide Pipelines**: Handles NotebookLM's rich media formats (Audio overview podcasts and structured slide decks), delivering them straight to your workspace inbox.

---

## 📥 Installation & Setup

### 1. Prerequisites
- **Python 3.11+**: Required for the `notebooklm-py` headless client.
- **NotebookLM CLI Auth**: Ensure you've authenticated with your Google account via `notebooklm login`.
- **Obsidian Vault**: A local path to your primary note-taking vault.

### 2. ⚠️ IMPORTANT: Path Configuration
Because this skill orchestrates other local processes (like downloading to specific folders, executing specific Python virtual environments), **it relies heavily on absolute paths**.

Before using this tool, you **MUST** replace all placeholder text in the installation:
Open `SKILL.md` and `scripts/distill.py` and run a global find-and-replace:
- Switch all instances of `YOUR_ABSOLUTE_PATH` to the absolute path of your system where this skill is located (e.g., `/Users/alice/projects`).

If you skip this step, the script will crash with "Folder not found" or "Interpreter not found" errors!

### 3. Usage Example
Once installed and registered as an OpenClaw Agent Skill:
```bash
> @notebooklm-distiller distill the latest papers on Q-Star architecture to my Obsidian Inbox.
```

## 📄 License
MIT License.
