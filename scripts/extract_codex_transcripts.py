#!/usr/bin/env python3
"""Distill local Codex task logs into compact, scan-ready text files.

Reads active and archived JSONL task logs under ~/.codex, keeps user prompts and
assistant messages, removes injected host context and tool noise, redacts obvious
secrets, and writes one text file per task plus an index.tsv. Stdlib only.
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


INJECTED_USER_PREFIXES = (
    "# AGENTS.md instructions",
    "<environment_context>",
    "<permissions instructions>",
    "<app-context>",
    "<recommended_plugins>",
    "<turn_aborted>",
)

REDACTIONS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{16,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]+"),
    re.compile(r"\b0x[a-fA-F0-9]{64}\b"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{16,}"),
]


def redact(text: str) -> str:
    for pattern in REDACTIONS:
        text = pattern.sub("[REDACTED]", text)
    return text


def clean_text(text: str, role: str) -> str:
    text = text.strip()
    if not text:
        return ""

    if role == "user":
        # Desktop context can be prepended to a genuine request. Keep the request
        # while dropping volatile browser/file metadata.
        for marker in ("## My request for Codex:", "# My request for Codex:"):
            if marker in text:
                text = text.split(marker, 1)[1].strip()
                break
        else:
            if text.startswith(INJECTED_USER_PREFIXES):
                return ""

    return redact(text)


def message_text(payload: dict, role: str) -> list[str]:
    content = payload.get("content")
    if isinstance(content, str):
        cleaned = clean_text(content, role)
        return [cleaned] if cleaned else []

    texts: list[str] = []
    if isinstance(content, list):
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") not in ("input_text", "output_text", "text"):
                continue
            value = item.get("text")
            if isinstance(value, str):
                cleaned = clean_text(value, role)
                if cleaned:
                    texts.append(cleaned)
    return texts


def task_metadata(path: Path) -> dict:
    metadata = {
        "id": path.stem,
        "cwd": "unknown",
        "date": "unknown",
        "source": "unknown",
    }
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") != "session_meta":
                    continue
                payload = entry.get("payload") or {}
                metadata.update(
                    {
                        "id": str(payload.get("id") or path.stem),
                        "cwd": str(payload.get("cwd") or "unknown"),
                        "date": str(payload.get("timestamp") or entry.get("timestamp") or "unknown")[:10],
                        "source": str(payload.get("originator") or payload.get("source") or "unknown"),
                    }
                )
                break
    except OSError:
        pass
    return metadata


def timestamp_seconds(value: object) -> Optional[float]:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def extract_task(path: Path, max_msg_chars: int, max_task_chars: int, cutoff: float):
    meta = task_metadata(path)
    turns: list[tuple[str, str]] = []
    first_date: Optional[str] = None

    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            entry_timestamp = entry.get("timestamp")
            entry_seconds = timestamp_seconds(entry_timestamp)
            if entry_seconds is not None and entry_seconds < cutoff:
                continue
            if entry.get("type") != "response_item":
                continue
            payload = entry.get("payload") or {}
            if payload.get("type") != "message":
                continue
            role = payload.get("role")
            if role not in ("user", "assistant"):
                continue
            for text in message_text(payload, role):
                if first_date is None and isinstance(entry_timestamp, str):
                    first_date = entry_timestamp[:10]
                if len(text) > max_msg_chars:
                    text = text[:max_msg_chars] + " ...[truncated]"
                turns.append(("U" if role == "user" else "A", text))

    user_turns = sum(1 for role, _ in turns if role == "U")
    if user_turns == 0:
        return None

    chunks: list[str] = []
    total = 0
    for role, text in turns:
        chunk = f"{role}: {text}\n\n"
        if total + len(chunk) > max_task_chars:
            chunks.append("[task truncated at size cap]\n")
            break
        chunks.append(chunk)
        total += len(chunk)

    project = Path(meta["cwd"]).name if meta["cwd"] != "unknown" else "unknown"
    return {
        **meta,
        "date": first_date or meta["date"],
        "project": project or "root",
        "user_turns": user_turns,
        "assistant_turns": sum(1 for role, _ in turns if role == "A"),
        "body": "".join(chunks),
    }


def discover(paths: list[Path], cutoff: float) -> list[Path]:
    by_id: dict[str, Path] = {}
    for root in paths:
        if not root.exists():
            continue
        for jsonl in root.rglob("*.jsonl"):
            try:
                if jsonl.stat().st_mtime < cutoff:
                    continue
            except OSError:
                continue
            task_id = task_metadata(jsonl)["id"]
            previous = by_id.get(task_id)
            if previous is None or jsonl.stat().st_mtime > previous.stat().st_mtime:
                by_id[task_id] = jsonl
    return sorted(by_id.values())


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument("--out", required=True, help="directory for per-task text extracts")
    parser.add_argument("--days", type=int, default=30, help="lookback window (default 30)")
    parser.add_argument("--filter", default="", help="only tasks whose cwd contains this substring")
    parser.add_argument("--max-msg-chars", type=int, default=2000)
    parser.add_argument("--max-task-chars", type=int, default=60000)
    args = parser.parse_args()

    codex_home = Path(args.codex_home).expanduser()
    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - args.days * 86400
    paths = discover([codex_home / "sessions", codex_home / "archived_sessions"], cutoff)

    scanned = written = skipped_empty = total_chars = 0
    rows: list[str] = []
    for jsonl in paths:
        meta = task_metadata(jsonl)
        if args.filter and args.filter.lower() not in meta["cwd"].lower():
            continue
        scanned += 1
        try:
            task = extract_task(jsonl, args.max_msg_chars, args.max_task_chars, cutoff)
        except OSError:
            skipped_empty += 1
            continue
        if task is None:
            skipped_empty += 1
            continue

        name = f"{safe_name(task['project'])}__{safe_name(task['id'])}.txt"
        header = (
            f"# project: {task['project']}\n# task: {task['id']}\n"
            f"# date: {task['date']}\n# cwd: {task['cwd']}\n# source: {task['source']}\n"
            f"# turns: {task['user_turns']}U/{task['assistant_turns']}A\n\n"
        )
        (out_dir / name).write_text(header + task["body"], encoding="utf-8")
        written += 1
        total_chars += len(task["body"])
        rows.append(
            f"{name}\t{task['project']}\t{task['date']}\t{task['id']}\t"
            f"{task['user_turns']}\t{task['assistant_turns']}\t{len(task['body'])}"
        )

    (out_dir / "index.tsv").write_text(
        "file\tproject\tdate\ttask_id\tuser_turns\tassistant_turns\tchars\n"
        + "\n".join(rows)
        + "\n",
        encoding="utf-8",
    )
    json.dump(
        {
            "tasks_scanned": scanned,
            "tasks_written": written,
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
