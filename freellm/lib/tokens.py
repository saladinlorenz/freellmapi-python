from __future__ import annotations
import math

def estimate_tokens(messages, tools=None) -> int:
    total_chars = 0
    for m in messages:
        c = m.get("content")
        if isinstance(c, str):
            total_chars += len(c)
        elif isinstance(c, list):
            for part in c:
                if isinstance(part, dict):
                    t = part.get("text") or part.get("content") or ""
                    if isinstance(t, str):
                        total_chars += len(t)
                    # image_url etc. counted minimally
        # tool_calls in assistant messages
        tcs = m.get("tool_calls") or []
        for tc in tcs:
            fn = tc.get("function") or {}
            total_chars += len(fn.get("name") or "") + len(fn.get("arguments") or "")
    if tools:
        for tl in tools:
            fn = tl.get("function") or {}
            total_chars += len(fn.get("name") or "") + len(str(fn.get("description") or ""))
    return math.ceil(total_chars / 4) if total_chars else 1

def content_to_string(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, dict):
                if p.get("type") == "text":
                    parts.append(p.get("text") or "")
                elif "text" in p:
                    parts.append(p["text"])
        return "\n".join(parts)
    return str(content)
