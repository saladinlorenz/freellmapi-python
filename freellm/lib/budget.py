from __future__ import annotations
import re

def parse_budget(label: str | None) -> int | None:
    if not label or not label.strip():
        return None
    s = label.strip().lower()
    if s in ("unlimited", "inf", "infinite", "credits-based", "∞"):
        return None
    # extract first number + suffix like "50k", "1.5M", "~6M", "1-2M", "50-100M", "~18-45M"
    # take the largest number
    nums = re.findall(r"(\d+(?:\.\d+)?)\s*([kmb]?)", s)
    if not nums:
        return None
    max_val = 0
    for num_str, suffix in nums:
        try:
            n = float(num_str)
        except ValueError:
            continue
        mult = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000, "": 1}[suffix]
        val = int(n * mult)
        if val > max_val:
            max_val = val
    return max_val if max_val > 0 else None

def format_budget(tokens: int | None) -> str:
    if tokens is None:
        return "unlimited"
    if tokens >= 1_000_000_000:
        return f"{tokens/1_000_000_000:.1f}B"
    if tokens >= 1_000_000:
        return f"{tokens/1_000_000:.1f}M"
    if tokens >= 1_000:
        return f"{tokens/1_000:.0f}k"
    return str(tokens)
