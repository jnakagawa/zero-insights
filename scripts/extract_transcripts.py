#!/usr/bin/env python3
"""Distill Claude Code session transcripts into compact, scan-ready text files.

Reads ~/.claude/projects/*/*.jsonl (main-thread user prompts + assistant text only),
drops tool noise / system reminders / sidechains, redacts obvious secrets, and writes
one .txt per session plus an index.tsv. Prints a JSON summary to stdout.

Stdlib only. Local only — never uploads anything.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

SKIP_PREFIXES = (
    "<system-reminder",
    "<command-name",
    "<command-message",
    "<local-command",
    "<command-args",
    "Caveat: The messages below",
)

SYSTEM_REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)

REDACTIONS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),                      # OpenAI/Anthropic-style keys
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{16,}"),   # GitHub tokens
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),               # Slack tokens
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                          # AWS access keys
    re.compile(r"\beyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]+"),  # JWTs
    re.compile(r"\b0x[a-fA-F0-9]{64}\b"),                         # EVM private keys
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{16,}"),
]


def redact(text: str) -> str:
    for pat in REDACTIONS:
        text = pat.sub("[REDACTED]", text)
    return text


def clean_text(text: str) -> str:
    text = SYSTEM_REMINDER_RE.sub("", text).strip()
    if not text or text.startswith(SKIP_PREFIXES):
        return ""
    return redact(text)


def texts_from_content(content) -> list:
    if isinstance(content, str):
        t = clean_text(content)
        return [t] if t else []
    out = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                t = clean_text(item.get("text", ""))
                if t:
                    out.append(t)
    return out


def extract_session(path: Path, max_msg_chars: int, max_session_chars: int):
    turns = []  # (role, text)
    first_ts = None
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict) or entry.get("isSidechain"):
                continue
            etype = entry.get("type")
            if etype not in ("user", "assistant"):
                continue
            if first_ts is None and entry.get("timestamp"):
                first_ts = str(entry["timestamp"])[:10]
            message = entry.get("message") or {}
            for text in texts_from_content(message.get("content")):
                if len(text) > max_msg_chars:
                    text = text[:max_msg_chars] + " …[truncated]"
                turns.append(("U" if etype == "user" else "A", text))

    user_turns = sum(1 for r, _ in turns if r == "U")
    if user_turns == 0:
        return None

    lines, total = [], 0
    for role, text in turns:
        chunk = f"{role}: {text}\n\n"
        if total + len(chunk) > max_session_chars:
            lines.append("[session truncated at size cap]\n")
            break
        lines.append(chunk)
        total += len(chunk)

    return {
        "date": first_ts or "unknown",
        "user_turns": user_turns,
        "assistant_turns": sum(1 for r, _ in turns if r == "A"),
        "body": "".join(lines),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--projects-dir", default=str(Path.home() / ".claude" / "projects"))
    ap.add_argument("--out", required=True, help="directory for per-session .txt extracts")
    ap.add_argument("--days", type=int, default=30, help="lookback window (default 30)")
    ap.add_argument("--filter", default="", help="only project dirs containing this substring")
    ap.add_argument("--max-msg-chars", type=int, default=2000)
    ap.add_argument("--max-session-chars", type=int, default=60000)
    args = ap.parse_args()

    projects_dir = Path(args.projects_dir).expanduser()
    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - args.days * 86400

    scanned = written = skipped_empty = total_chars = 0
    index_rows = []

    for jsonl in sorted(projects_dir.glob("*/*.jsonl")):
        project = jsonl.parent.name
        if args.filter and args.filter not in project:
            continue
        try:
            if jsonl.stat().st_mtime < cutoff:
                continue
        except OSError:
            continue
        scanned += 1
        session = extract_session(jsonl, args.max_msg_chars, args.max_session_chars)
        if session is None:
            skipped_empty += 1
            continue
        name = f"{project}__{jsonl.stem}.txt"
        header = (
            f"# project: {project}\n# session: {jsonl.name}\n"
            f"# date: {session['date']}\n"
            f"# turns: {session['user_turns']}U/{session['assistant_turns']}A\n\n"
        )
        (out_dir / name).write_text(header + session["body"], encoding="utf-8")
        written += 1
        total_chars += len(session["body"])
        index_rows.append(
            f"{name}\t{project}\t{session['date']}\t"
            f"{session['user_turns']}\t{session['assistant_turns']}\t{len(session['body'])}"
        )

    (out_dir / "index.tsv").write_text(
        "file\tproject\tdate\tuser_turns\tassistant_turns\tchars\n" + "\n".join(index_rows) + "\n",
        encoding="utf-8",
    )
    json.dump(
        {
            "sessions_scanned": scanned,
            "sessions_written": written,
            "skipped_empty": skipped_empty,
            "total_chars": total_chars,
            "out_dir": str(out_dir),
        },
        sys.stdout,
        indent=2,
    )
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
