from __future__ import annotations
import json
import re

KIMI_RE = re.compile(r"<\|tool_calls_section_begin\|>.*?<\|tool_call_begin\|>functions\.(\w+):\d+<\|tool_call_argument_begin\|>(.*?)<\|tool_call_end\|>", re.DOTALL)
LLAMA_RE = re.compile(r"<function=(\w+)(.*?)</function>", re.DOTALL)
QWEN_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)

def _parse_args(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return "{}"
    try:
        json.loads(raw)
        return raw
    except Exception:
        # attempt to extract JSON object substring
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                json.loads(m.group(0))
                return m.group(0)
            except Exception:
                pass
        return raw

def rescue_inline_tool_calls(text: str, tool_names: set[str]) -> dict:
    if not text or not tool_names:
        return {"detected": False, "calls": None, "cleanText": text}
    detected = False
    calls = []
    # Kimi/DeepSeek dialect
    for m in KIMI_RE.finditer(text):
        name = m.group(1)
        if name in tool_names:
            detected = True
            calls.append({"name": name, "arguments": _parse_args(m.group(2))})
    # Llama/Groq dialect
    for m in LLAMA_RE.finditer(text):
        name = m.group(1)
        raw = m.group(2).strip()
        # raw may be "{...}" or ">{...}"
        if raw.startswith(">"):
            raw = raw[1:]
        raw = raw.lstrip("{")
        # reconstruct
        if name in tool_names:
            detected = True
            # try to parse as json
            candidate = "{" + raw if not raw.startswith("{") else raw
            # need to close properly — attempt extraction
            j = re.search(r"\{.*\}", candidate, re.DOTALL)
            args = j.group(0) if j else "{}"
            calls.append({"name": name, "arguments": _parse_args(args)})
    # Qwen/Hermes XML
    for m in QWEN_RE.finditer(text):
        try:
            obj = json.loads(m.group(1))
            name = obj.get("name") or obj.get("function", {}).get("name")
            args = obj.get("arguments") or obj.get("parameters") or "{}"
            if isinstance(args, dict):
                args = json.dumps(args)
            if name in tool_names:
                detected = True
                calls.append({"name": str(name), "arguments": _parse_args(args)})
        except Exception:
            continue
    # bare JSON fallback: single top-level JSON object with name+args keys that matches a tool
    if not detected:
        # check if text is mostly a JSON object
        stripped = text.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                obj = json.loads(stripped)
                if isinstance(obj, dict) and "name" in obj and obj["name"] in tool_names:
                    detected = True
                    args = obj.get("arguments") or obj.get("parameters") or obj.get("input") or "{}"
                    if isinstance(args, dict):
                        args = json.dumps(args)
                    calls.append({"name": obj["name"], "arguments": _parse_args(args)})
            except Exception:
                pass
    if not detected:
        # detect marker presence for hold-window logic
        markers = ["<|tool_calls", "<function=", "<tool_call>", "```json"]
        if any(mk in text for mk in markers):
            return {"detected": True, "calls": None, "cleanText": text}
        return {"detected": False, "calls": None, "cleanText": text}
    if calls:
        clean = KIMI_RE.sub("", text)
        clean = LLAMA_RE.sub("", clean)
        clean = QWEN_RE.sub("", clean)
        clean = clean.strip() or ""
        return {"detected": True, "calls": calls, "cleanText": clean}
    return {"detected": True, "calls": None, "cleanText": text}

def starts_with_dialect_marker(text: str) -> bool:
    s = text.lstrip()[:200]
    return s.startswith("<|tool") or s.startswith("<function=") or s.startswith("<tool_call>") or s.startswith("```json")

def could_become_dialect_marker(text: str) -> bool:
    s = text.lstrip()
    prefixes = ["<", "<|", "<|tool", "<function", "<tool", "```", "```j", "```json", "{"]
    return any(s.startswith(p[:len(s)]) and p.startswith(s) for p in prefixes) if len(s) < 20 else False

def repair_tool_arguments(args_str: str, schema: dict | None = None) -> str:
    if not args_str:
        return "{}"
    try:
        obj = json.loads(args_str)
        # if double-encoded (string containing JSON)
        if isinstance(obj, str):
            try:
                json.loads(obj)
                return obj
            except Exception:
                pass
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        # try to fix trailing commas, single quotes
        fixed = args_str.strip().replace("'", '"')
        fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
        try:
            json.loads(fixed)
            return fixed
        except Exception:
            return args_str
