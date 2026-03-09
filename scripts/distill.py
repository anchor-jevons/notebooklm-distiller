#!/usr/bin/env python3
"""
NotebookLM Distiller — Knowledge Extraction & Management for Obsidian

Subcommands:
  distill   Extract knowledge from NotebookLM notebooks into Obsidian markdown.
  research  Kick off a NotebookLM web research session on a topic.
  persist   Write any markdown content directly into the Obsidian vault.
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def yaml_quote(value: str) -> str:
    """Return a YAML-safe quoted scalar (JSON string escaping)."""
    return json.dumps(value, ensure_ascii=False)


def run_command(cmd: List[str], timeout: int = 120) -> str:
    """Run a CLI command and return stdout. Returns '' on error/timeout."""
    logging.info(f"[RUN] {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        logging.error(f"[ERROR] Command timed out after {timeout}s: {' '.join(cmd)}")
        return ""
    if result.returncode != 0:
        logging.error(f"[ERROR] Command failed (rc={result.returncode}): {result.stderr.strip()}")
        return ""
    return result.stdout.strip()


def sanitize_filename(name: str) -> str:
    """Remove unsafe filename characters and truncate to 100 chars."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace("\n", " ").strip()
    return name[:100]


def clean_cli_output(output: str) -> str:
    """Strip NotebookLM CLI noise lines; preserve actual content."""
    noise_prefixes = (
        "Starting new conversation",
        "New conversation: ",
        "Generating response",
    )
    lines = output.split('\n')
    cleaned = []
    for line in lines:
        if any(line.startswith(p) for p in noise_prefixes):
            continue
        if line.startswith("Answer:"):
            rest = line[len("Answer:"):].strip()
            if rest:
                cleaned.append(rest)
            continue
        cleaned.append(line)
    return '\n'.join(cleaned).strip()


def build_frontmatter(title: str, date_str: str, source: str,
                      topic: str, mode: str, extra_tags: List[str] = None) -> str:
    """Build a standard YAML frontmatter block."""
    safe_topic = sanitize_filename(topic).replace(' ', '-')
    tags = ["distillation", mode, safe_topic] + (extra_tags or [])
    lines = [
        "---",
        f"title: {yaml_quote(title)}",
        f"date: {date_str}",
        "type: knowledge-note",
        "author: notebooklm-distiller",
        f"tags: {json.dumps(tags, ensure_ascii=False)}",
        f"source: {yaml_quote(source)}",
        f"project: {yaml_quote(topic)}",
        "status: draft",
        "---",
    ]
    return '\n'.join(lines)


def write_note(filepath: str, content: str) -> None:
    """Write content to filepath, creating parent dirs as needed."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"Saved → {filepath}")


# ---------------------------------------------------------------------------
# NotebookLM helpers
# ---------------------------------------------------------------------------

def get_notebooks(nlm_cli: str, keywords: List[str]) -> List[Tuple[str, str]]:
    """List all notebooks and return those whose title matches any keyword.
    Returns [(notebook_id, notebook_name), ...]."""
    output = run_command([nlm_cli, "list", "--json"])
    if not output:
        return []
    try:
        notebooks = json.loads(output).get("notebooks", [])
    except json.JSONDecodeError:
        logging.error("Failed to parse notebook list JSON.")
        return []

    return [
        (nb.get("id", ""), nb.get("title", ""))
        for nb in notebooks
        if any(kw.lower() in nb.get("title", "").lower() for kw in keywords)
    ]


def extract_questions(nlm_cli: str, notebook_id: str) -> List[str]:
    """Ask NotebookLM to generate 15-20 deep questions from a notebook."""
    prompt = (
        "Please generate 15 to 20 of the most valuable questions based on all sources in this notebook. "
        "Focus on core ideas, design constraints, pain points, and solutions. "
        "Output one question per line as a flat list. No numbering, no prefixes, no markdown formatting."
    )
    output = run_command([nlm_cli, "ask", prompt, "--notebook", notebook_id, "--new"])
    if not output:
        return []

    cleaned = clean_cli_output(output)
    questions = []
    for line in cleaned.split('\n'):
        line = re.sub(r'^[\d\.\-\*\sQA:：]+', '', line).strip()
        if len(line) < 8:
            continue
        if re.search(r'^(here are|以下是|如下|问题列表)', line, re.IGNORECASE):
            continue
        questions.append(line)
    return questions


def ask_question(nlm_cli: str, question: str, notebook_id: str, retries: int = 3) -> str:
    """Ask a specific question and return the answer (with retry)."""
    cmd = [nlm_cli, "ask", question, "--notebook", notebook_id, "--new"]
    for attempt in range(retries):
        output = run_command(cmd)
        if output:
            result = clean_cli_output(output)
            if result:
                return result
        logging.warning(f"[WARN] Empty response. Retrying ({attempt + 1}/{retries})...")
        time.sleep(3)
    return "_No answer returned after 3 attempts._"


# ---------------------------------------------------------------------------
# Subcommand: distill
# ---------------------------------------------------------------------------

SUMMARY_PROMPTS = [
    ("Summary",
     "Please summarise the core theme and background of this material in 2-3 sentences."),
    ("Key Points",
     "List the core knowledge points, development thread, and key conclusions in structured Markdown."),
    ("Design Constraints",
     "Identify all core constraints, pain points, and limitations present in the material."),
    ("Trade-offs",
     "Analyse architectural / implementation trade-offs. Use a Markdown table or list."),
    ("Open Questions",
     "What unresolved questions and risk factors deserve the most attention going forward?"),
]

GLOSSARY_PROMPT = (
    "Scan all sources in this notebook and list the 15-30 most important domain terms, "
    "abbreviations, and key entities. For each, give a precise definition based on the source material. "
    "Use bold subheadings or Markdown dividers to separate entries."
)


def process_notebook(nlm_cli: str, notebook_id: str, notebook_name: str,
                     topic: str, vault_dir: str, mode: str, date_str: str) -> None:
    """Extract knowledge from one notebook and write an Obsidian note."""
    safe_nb = sanitize_filename(notebook_name)
    suffix_map = {"qa": ("_QA.md", "Deep Q&A"), "summary": ("_Summary.md", "Summary"), "glossary": ("_Glossary.md", "Glossary")}
    file_suffix, title_suffix = suffix_map[mode]

    out_path = os.path.join(vault_dir, sanitize_filename(topic), safe_nb + file_suffix)
    source_label = f"NotebookLM/{notebook_name}"
    title = f"{notebook_name} | {title_suffix}"

    fm = build_frontmatter(title, date_str, source_label, topic, mode)
    header = f"# {notebook_name} — {title_suffix}\n"
    body_parts = [fm, "", header, ""]

    logging.info(f"--- [{mode.upper()}] {notebook_name} ---")

    if mode == "qa":
        questions = extract_questions(nlm_cli, notebook_id)
        if not questions:
            logging.error(f"[FATAL] Could not generate questions for: {notebook_name}")
            return
        logging.info(f"Generated {len(questions)} questions.")
        for i, q in enumerate(questions, 1):
            num = f"{i:02d}"
            logging.info(f"[{num}/{len(questions)}] {q[:70]}...")
            answer = ask_question(nlm_cli, q, notebook_id)
            body_parts += [f"## Q{num}", "", f"> [!question]", f"> {q}", "", f"**Answer:**\n\n{answer}", "", "---", ""]
            time.sleep(2)

    elif mode == "summary":
        for section_title, prompt in SUMMARY_PROMPTS:
            logging.info(f"Extracting: {section_title} ...")
            answer = ask_question(nlm_cli, prompt, notebook_id)
            body_parts += [f"## {section_title}", "", answer, "", "---", ""]
            time.sleep(2)

    elif mode == "glossary":
        logging.info("Extracting glossary ...")
        answer = ask_question(nlm_cli, GLOSSARY_PROMPT, notebook_id)
        body_parts += ["## Glossary", "", answer, "", "---", ""]

    body_parts += ["", "*Extracted by notebooklm-distiller*"]

    write_note(out_path, '\n'.join(body_parts))
    logging.info(f"Distillation complete → {out_path}")


def cmd_distill(args) -> None:
    vault_dir = os.path.expanduser(args.vault_dir)
    if not os.path.isdir(vault_dir):
        logging.error(f"[FATAL] vault-dir does not exist: '{vault_dir}'")
        sys.exit(1)

    date_str = datetime.now().strftime("%Y-%m-%d")
    logging.info(f"=== Distill: keywords={args.keywords} mode={args.mode} ===")

    notebooks = get_notebooks(args.cli_path, args.keywords)
    if not notebooks:
        logging.error(f"[FATAL] No notebooks matched: {', '.join(args.keywords)}")
        sys.exit(1)

    logging.info(f"Found {len(notebooks)} notebook(s):")
    for nid, name in notebooks:
        logging.info(f"  - {name} ({nid})")

    for nid, name in notebooks:
        logging.info(f"\n{'='*50}\nProcessing: {name}\n{'='*50}")
        process_notebook(args.cli_path, nid, name, args.topic, vault_dir, args.mode, date_str)

    logging.info("=== All done! ===")


# ---------------------------------------------------------------------------
# Subcommand: research
# ---------------------------------------------------------------------------

def cmd_research(args) -> None:
    """Create a NotebookLM notebook via web research on a topic."""
    nlm = args.cli_path
    topic = args.topic
    mode = getattr(args, 'mode', 'deep')

    logging.info(f"=== Research: topic='{topic}' mode={mode} ===")

    # Create notebook
    nb_raw = run_command([nlm, "create", f"Research: {topic}", "--json"])
    if not nb_raw:
        logging.error("[FATAL] Failed to create research notebook.")
        sys.exit(1)
    try:
        nb_id = json.loads(nb_raw)["notebook"]["id"]
    except (json.JSONDecodeError, KeyError):
        logging.error(f"[FATAL] Unexpected create response: {nb_raw[:200]}")
        sys.exit(1)

    logging.info(f"Notebook created: Research: {topic} ({nb_id})")

    # Start research
    logging.info(f"Starting {mode} web research — this may take several minutes...")
    run_command([nlm, "source", "add-research", topic, "--mode", mode, "--notebook", nb_id])

    # Wait for completion
    logging.info("Waiting for research import to complete...")
    result = run_command(
        [nlm, "research", "wait", "--import-all", "-n", nb_id, "--timeout", "600"],
        timeout=700,
    )
    if not result:
        logging.warning("Research wait did not confirm completion — check NotebookLM manually.")

    print(f"\nResearch complete.")
    print(f"Notebook : Research: {topic}")
    print(f"ID       : {nb_id}")
    print(f"\nNext step:")
    print(f'  python3 distill.py distill --keywords "{topic}" --topic "{topic}" --vault-dir <your-vault-dir> --mode summary')


# ---------------------------------------------------------------------------
# Subcommand: persist
# ---------------------------------------------------------------------------

def cmd_persist(args) -> None:
    """Write markdown content directly into the Obsidian vault with frontmatter."""
    vault_dir = os.path.expanduser(args.vault_dir)
    if not os.path.isdir(vault_dir):
        logging.error(f"[FATAL] vault-dir does not exist: '{vault_dir}'")
        sys.exit(1)

    # Get content
    if args.file:
        content_body = open(os.path.expanduser(args.file), encoding="utf-8").read().strip()
    elif args.content:
        content_body = args.content.strip()
    else:
        logging.error("[FATAL] Provide --content or --file.")
        sys.exit(1)

    date_str = datetime.now().strftime("%Y-%m-%d")
    rel_path = args.path
    title = args.title or os.path.basename(rel_path).replace(".md", "")
    tags_list = [t.strip() for t in args.tags.split(",")] if args.tags else ["persist", "knowledge"]

    fm_lines = [
        "---",
        f"title: {yaml_quote(title)}",
        f"date: {date_str}",
        "type: knowledge-note",
        "author: notebooklm-distiller",
        f"tags: {json.dumps(tags_list, ensure_ascii=False)}",
        "status: draft",
        "---",
    ]
    full_content = '\n'.join(fm_lines) + f"\n\n# {title}\n\n{content_body}\n"

    out_path = os.path.join(vault_dir, rel_path)
    write_note(out_path, full_content)
    print(f"Persisted → {out_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(
        description="NotebookLM Distiller — knowledge extraction and management for Obsidian.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  distill   Extract knowledge from NotebookLM into Obsidian markdown notes.
  research  Start a NotebookLM web research session on a topic.
  persist   Write any markdown content directly into the Obsidian vault.

Examples:
  python3 distill.py distill --keywords "machine learning" --topic "ML Basics" \\
      --vault-dir ~/Obsidian/Vault --mode summary
  python3 distill.py research --topic "Quantum Computing"
  python3 distill.py persist --title "Meeting Notes" --vault-dir ~/Obsidian/Vault \\
      --path "Notes/2026-03-09.md" --content "Key decisions: ..."
        """,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --- distill ---
    p_distill = sub.add_parser("distill", help="Extract knowledge from NotebookLM notebooks.")
    p_distill.add_argument("--keywords", nargs="+", required=True,
                           help="Keywords to match against notebook titles (e.g. 'machine learning' 'AI')")
    p_distill.add_argument("--topic", required=True,
                           help="Topic folder name in Obsidian (e.g. 'Machine Learning Basics')")
    p_distill.add_argument("--vault-dir", required=True,
                           help="Base Obsidian directory (e.g. ~/Obsidian/Vault/10_Projects)")
    p_distill.add_argument("--mode", choices=["qa", "summary", "glossary"], default="qa",
                           help="Extraction strategy: qa (default), summary, or glossary")
    p_distill.add_argument("--cli-path", default="notebooklm",
                           help="Path to the notebooklm CLI (default: 'notebooklm' from PATH)")

    # --- research ---
    p_research = sub.add_parser("research", help="Start a NotebookLM web research session.")
    p_research.add_argument("--topic", required=True,
                            help="Research topic (e.g. 'Transformer architecture')")
    p_research.add_argument("--mode", choices=["deep", "fast"], default="deep",
                            help="Research depth (default: deep)")
    p_research.add_argument("--cli-path", default="notebooklm",
                            help="Path to the notebooklm CLI")

    # --- persist ---
    p_persist = sub.add_parser("persist", help="Write markdown content directly into Obsidian.")
    p_persist.add_argument("--vault-dir", required=True,
                           help="Base Obsidian directory")
    p_persist.add_argument("--path", required=True,
                           help="Relative path within vault (e.g. 'Notes/2026-03-09.md')")
    p_persist.add_argument("--title", default="",
                           help="Note title (defaults to filename)")
    p_persist.add_argument("--content", default="",
                           help="Markdown content to write (use --file for file input)")
    p_persist.add_argument("--file", default="",
                           help="Path to a markdown file to persist")
    p_persist.add_argument("--tags", default="",
                           help="Comma-separated tags (e.g. 'research,ai,notes')")

    args = parser.parse_args()

    dispatch = {"distill": cmd_distill, "research": cmd_research, "persist": cmd_persist}
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
