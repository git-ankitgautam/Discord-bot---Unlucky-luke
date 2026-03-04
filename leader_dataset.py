import json
import random
import re
from pathlib import Path
from typing import Optional


TOKEN_RE = re.compile(r"[a-z0-9']+")
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def _clean_message(text: str) -> str:
    return text.replace("\n", " ").strip()


def _is_usable_message(text: str) -> bool:
    if len(text) < 4:
        return False
    if text.startswith("!"):
        return False
    if URL_RE.search(text):
        return False
    return True


def find_latest_dataset_file(folder: str = ".") -> Optional[Path]:
    files = list(Path(folder).glob("user_messages_*.jsonl"))
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def load_leader_messages(dataset_path: Path) -> list[dict]:
    messages = []
    seen = set()

    with dataset_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue

            content = _clean_message(str(row.get("content", "")))
            if not _is_usable_message(content):
                continue

            key = content.lower()
            if key in seen:
                continue
            seen.add(key)

            messages.append(
                {
                    "content": content,
                    "jump_url": str(row.get("jump_url", "")),
                    "created_at": str(row.get("created_at", "")),
                    "channel_name": str(row.get("channel_name", "")),
                }
            )

    return messages


def pick_random_message(messages: list[dict]) -> Optional[dict]:
    if not messages:
        return None
    return random.choice(messages)


def pick_best_match(messages: list[dict], prompt: str) -> Optional[dict]:
    if not messages:
        return None

    prompt_tokens = _tokenize(prompt)
    if not prompt_tokens:
        return pick_random_message(messages)

    best = None
    best_score = -1.0

    for msg in messages:
        text_tokens = _tokenize(msg["content"])
        if not text_tokens:
            continue

        overlap = len(prompt_tokens & text_tokens)
        if overlap == 0:
            continue

        score = overlap / (len(prompt_tokens) ** 0.5 * len(text_tokens) ** 0.5)
        if score > best_score:
            best = msg
            best_score = score

    if best is None:
        return pick_random_message(messages)
    return best
