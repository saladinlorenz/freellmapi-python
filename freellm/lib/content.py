from __future__ import annotations

def normalize_messages(messages: list[dict]) -> list[dict]:
    out = []
    for m in messages:
        role = m.get("role")
        content = m.get("content")
        nm = {"role": role}
        if isinstance(content, list):
            # keep as-is for vision etc., but ensure valid
            nm["content"] = content
        else:
            nm["content"] = content
        if m.get("name"):
            nm["name"] = m["name"]
        if m.get("tool_calls"):
            nm["tool_calls"] = m["tool_calls"]
        if m.get("tool_call_id"):
            nm["tool_call_id"] = m["tool_call_id"]
        if m.get("reasoning_content"):
            nm["reasoning_content"] = m["reasoning_content"]
        out.append(nm)
    return out

def has_image_content(messages: list[dict]) -> bool:
    for m in messages:
        c = m.get("content")
        if isinstance(c, list):
            for part in c:
                if isinstance(part, dict) and part.get("type") == "image_url":
                    return True
                if isinstance(part, dict) and part.get("type") == "image":
                    return True
    return False

def flatten_content_to_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for p in content:
            if isinstance(p, dict):
                if p.get("type") == "text":
                    texts.append(p.get("text") or "")
                elif "text" in p and isinstance(p["text"], str):
                    texts.append(p["text"])
        return "\n".join(texts)
    return str(content)
