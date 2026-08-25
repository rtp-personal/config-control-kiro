#!/usr/bin/env python3
"""Append the latest Kiro session context to .kiro/context.md once per day.

This script is meant to run from a cron/systemd/timer job at 19:00 UTC, e.g.:

    0 19 * * * /usr/bin/env python3 /path/to/repo/.kiro/scripts/sync-kiro-session-context.py /path/to/repo

Environment variables:
    KIRO_SESSIONS_DIR  Path to ~/.kiro/sessions (default: ~/.kiro/sessions)
    CONTEXT_LIMIT      Max characters per message to keep (default: 500)
    MAX_ENTRIES        Keep only the last N session entries (default: 60)
"""

import argparse
import datetime
import json
import os
import re
from pathlib import Path

DEFAULT_KIRO_SESSIONS_DIR = Path.home() / ".kiro" / "sessions"
CONTEXT_FILE = Path(".kiro") / "context.md"
SESSION_RE = re.compile(r"sess_([0-9a-fA-F-]+)")


def find_latest_messages_file(sessions_dir: Path) -> Path | None:
    """Return the most recently modified messages.jsonl under the sessions tree."""
    candidates = list(sessions_dir.rglob("messages.jsonl"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def extract_session_id(messages_path: Path) -> str | None:
    match = SESSION_RE.search(str(messages_path))
    return match.group(1) if match else None


def read_latest_messages(messages_path: Path, limit: int) -> list[dict]:
    """Read JSONL messages and return a compact list of role/content entries."""
    entries = []
    with messages_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = msg.get("role") or msg.get("author", "unknown")
            content = msg.get("content", "")
            if isinstance(content, dict):
                content = json.dumps(content, ensure_ascii=False)
            if not content:
                continue
            if len(content) > limit:
                content = content[:limit].rstrip() + " ...[truncated]"
            entries.append({"role": role, "content": content, "timestamp": msg.get("timestamp")})
    return entries


def load_context(repo: Path) -> tuple[str, set[str]]:
    """Read existing context file and collect already-recorded session IDs."""
    context_path = repo / CONTEXT_FILE
    if not context_path.exists():
        return "# Kiro Session Context\n\n", set()
    text = context_path.read_text(encoding="utf-8", errors="replace")
    ids = set(SESSION_RE.findall(text))
    return text, ids


def trim_entries(text: str, max_entries: int) -> str:
    """Keep only the most recent N session entries."""
    heading_re = re.compile(r"^(## .+?- sess_[0-9a-fA-F-]+.*)$", re.MULTILINE)
    headings = list(heading_re.finditer(text))
    if len(headings) <= max_entries:
        return text
    # Split text before the first heading to keep the preamble
    preamble_end = headings[0].start()
    preamble = text[:preamble_end]
    entries = []
    for i, match in enumerate(headings):
        start = match.start()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        entries.append(text[start:end])
    # Keep the most recent entries
    kept = entries[-max_entries:]
    return preamble + "".join(kept)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Kiro session context to .kiro/context.md")
    parser.add_argument("repo", nargs="?", default=".", help="Path to the repo containing .kiro/context.md")
    parser.add_argument("--limit", type=int, default=int(os.getenv("CONTEXT_LIMIT", 500)), help="Max chars per message")
    parser.add_argument("--max-entries", type=int, default=int(os.getenv("MAX_ENTRIES", 60)), help="Max session entries to keep")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    context_path = repo / CONTEXT_FILE

    sessions_dir = Path(os.getenv("KIRO_SESSIONS_DIR", DEFAULT_KIRO_SESSIONS_DIR))
    if not sessions_dir.exists():
        print(f"No Kiro sessions directory found at {sessions_dir}; nothing to sync.")
        return 0

    latest = find_latest_messages_file(sessions_dir)
    if not latest:
        print(f"No messages.jsonl found under {sessions_dir}; nothing to sync.")
        return 0

    session_id = extract_session_id(latest)
    if not session_id:
        session_id = latest.stem

    context_text, recorded_ids = load_context(repo)
    if session_id in recorded_ids:
        print(f"Session {session_id} is already recorded in {CONTEXT_FILE}; nothing to do.")
        return 0

    messages = read_latest_messages(latest, args.limit)
    if not messages:
        print(f"Latest session file {latest} contains no readable messages.")
        return 0

    when = datetime.datetime.fromtimestamp(latest.stat().st_mtime, tz=datetime.timezone.utc)
    heading = f"## {when.strftime('%Y-%m-%d %H:%M UTC')} - sess_{session_id}\n\n"
    body_lines = [f"- **{m['role']}:** {m['content']}" for m in messages]
    body = "\n".join(body_lines) + "\n\n"

    # Ensure the context file has a top-level header
    if not context_text.lstrip().startswith("# "):
        context_text = "# Kiro Session Context\n\n" + context_text

    updated = context_text + heading + body
    updated = trim_entries(updated, args.max_entries)

    context_path.parent.mkdir(parents=True, exist_ok=True)
    context_path.write_text(updated, encoding="utf-8")
    print(f"Updated {CONTEXT_FILE} with session {session_id} ({len(messages)} messages).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
