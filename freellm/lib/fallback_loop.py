from __future__ import annotations
import time
from dataclasses import dataclass, field

FALLBACK_MAX_RETRIES = 20

@dataclass
class FallbackState:
    skip_keys: set[str] = field(default_factory=set)
    skip_models: set[int] = field(default_factory=set)
    skip_platforms: set[str] = field(default_factory=set)

def new_fallback_state() -> FallbackState:
    return FallbackState()

@dataclass
class AttemptRecord:
    ordinal: int
    platform: str
    model_id: str
    key_id: int | None
    outcome: str
    duration_ms: int
    error_summary: str = ""

def summarize_exhaustion(diagnostics: list[str], soonest_expiry_ms: int | None) -> str:
    total = len(diagnostics)
    if total == 0:
        return "All models exhausted: no routes available. Add API keys."
    # tally by category
    cats: dict[str, int] = {}
    for d in diagnostics:
        low = d.lower()
        if "no provider registered" in low:
            cats["unsupported"] = cats.get("unsupported", 0) + 1
        elif "no enabled" in low or "no usable key" in low or "decrypt" in low:
            cats["no_key"] = cats.get("no_key", 0) + 1
        elif "prompt too large" in low or "< estimated" in low:
            cats["too_large"] = cats.get("too_large", 0) + 1
        elif "no vision" in low:
            cats["no_vision"] = cats.get("no_vision", 0) + 1
        elif "no tool" in low:
            cats["no_tools"] = cats.get("no_tools", 0) + 1
        elif "drops response_format" in low:
            cats["no_json"] = cats.get("no_json", 0) + 1
        elif "already-failed" in low or "ruled out" in low:
            cats["failed"] = cats.get("failed", 0) + 1
        elif any(x in low for x in ("cooldown","rpm","rpd","tpm","tpd","daily-cap")):
            cats["rate_limited"] = cats.get("rate_limited", 0) + 1
        else:
            cats["unavailable"] = cats.get("unavailable", 0) + 1
    parts = []
    order = ["no_key","rate_limited","unsupported","too_large","no_vision","no_tools","no_json","failed","unavailable"]
    for k in order:
        if k in cats:
            parts.append(f"{cats[k]} {k}")
    detail = ", ".join(parts)
    eta = ""
    if soonest_expiry_ms:
        rem = max(0, soonest_expiry_ms - int(time.time()*1000))
        if rem < 90_000:
            eta = f" Soonest reset ~{max(1, rem//1000)}s"
        elif rem < 90*60*1000:
            eta = f" Soonest reset ~{max(1, rem//60000)}m"
        else:
            eta = f" Soonest reset ~{max(1, rem//3600000)}h"
    return f"All models exhausted: {total} routes checked ({detail}). Add more API keys or wait for rate limits to reset.{eta}"

def exhaustion_status(diagnostics: list[str]) -> int:
    # simplified taxonomy: all auth -> 502, all context -> 413, all rate_limited -> 429
    if not diagnostics:
        return 429
    lows = [d.lower() for d in diagnostics]
    if all("auth" in l or "decrypt" in l or "invalid" in l for l in lows):
        return 502
    if all("too large" in l or "< estimated" in l for l in lows):
        return 413
    if all(any(x in l for x in ("cooldown","rate","rpd","rpm","tpm","tpd")) for l in lows):
        return 429
    return 502
