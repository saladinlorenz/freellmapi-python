from __future__ import annotations
import re

TIMEOUT_MARKERS = ["timeout", "stalled", "etimedout", "aborted"]
RETRYABLE_STATUSES = {408, 409, 425, 429, 500, 502, 503, 504}
NETWORK_CODES = {"ECONNRESET", "ECONNREFUSED", "ENOTFOUND", "ETIMEDOUT", "EAI_AGAIN"}

def is_timeout_error(msg: str) -> bool:
    low = msg.lower()
    return any(m in low for m in TIMEOUT_MARKERS)

def is_retryable_status(status: int | None) -> bool:
    if status is None:
        return False
    if status in RETRYABLE_STATUSES:
        return True
    if 500 <= status <= 599:
        return True
    return False

def classify_error(status: int | None, message: str) -> str:
    low = message.lower()
    if status == 401 or "unauthorized" in low or "invalid" in low and "key" in low:
        return "auth_invalid"
    if status == 402 or "out of credits" in low or "insufficient balance" in low or "payment required" in low:
        return "out_of_credits"
    if status == 403 and ("tier" in low or "forbidden" in low):
        return "forbidden"
    if status == 403:
        return "forbidden"
    if status == 404 or "not found" in low or "unknown model" in low:
        return "model_not_found"
    if status == 413 or "context" in low and "too large" in low or "maximum context" in low:
        return "context_length"
    if status == 400 and "content_filter" in low:
        return "content_filter"
    if is_timeout_error(message):
        return "timeout"
    if status == 429 or "rate" in low and "limit" in low or "too many" in low or "quota" in low:
        s = "daily_quota_exhausted" if "daily" in low or "rpd" in low or "per day" in low else "rate_limited"
        return s
    if is_retryable_status(status):
        return "server_error"
    if status and 400 <= status < 500:
        return "bad_request"
    return "unknown"

UNAVAILABLE_UNTIL_KNOWN = {"rate_limited", "daily_quota_exhausted", "out_of_credits", "forbidden"}

def is_retryable(category: str) -> bool:
    return category in ("rate_limited", "daily_quota_exhausted", "timeout", "server_error") or category == "unknown"

def is_auth_error(category: str) -> bool:
    return category == "auth_invalid"

def sanitize_message(msg: str) -> str:
    # redact possible keys
    return re.sub(r"(sk-[a-zA-Z0-9_\-]{8,})", "sk-***", msg)[:500]
