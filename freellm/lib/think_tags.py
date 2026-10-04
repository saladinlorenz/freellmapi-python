from __future__ import annotations
import re

THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)

def extract_think_from_message(msg: dict) -> None:
    content = msg.get("content")
    if not isinstance(content, str) or "<think>" not in content.lower():
        return
    m = THINK_RE.search(content)
    if not m:
        return
    reasoning = m.group(1).strip()
    cleaned = THINK_RE.sub("", content).strip()
    if reasoning:
        msg["reasoning_content"] = reasoning
    msg["content"] = cleaned

def extract_think_from_stream_text(text: str) -> tuple[str, str | None]:
    m = THINK_RE.search(text)
    if not m:
        return text, None
    reasoning = m.group(1).strip()
    cleaned = THINK_RE.sub("", text).strip()
    return cleaned, reasoning
