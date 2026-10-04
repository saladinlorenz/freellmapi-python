from __future__ import annotations

# Per-platform allowed extended params (simplified from TS sampling-params.ts)
# Platforms not listed = allow all except logprobs quirks

def extended_body_params(platform: str, options: dict | None) -> dict:
    if not options:
        return {}
    out = {}
    # mapping from CompletionOptions keys to upstream keys
    mapping = {
        "top_k": "top_k",
        "seed": "seed",
        "repetition_penalty": "repetition_penalty",
        "frequency_penalty": "frequency_penalty",
        "presence_penalty": "presence_penalty",
        "logprobs": "logprobs",
        "top_logprobs": "top_logprobs",
        "n": "n",
        "logit_bias": "logit_bias",
        "response_format": "response_format",
        "reasoning_effort": "reasoning_effort",
        "user": "user",
    }
    for k, upstream in mapping.items():
        if k in options and options[k] is not None:
            out[upstream] = options[k]
    # platform-specific stripping
    if platform == "mistral":
        out.pop("top_k", None)
        out.pop("reasoning_effort", None)
    if platform in ("cohere", "cloudflare"):
        out.pop("response_format", None)
        out.pop("reasoning_effort", None)
    # clamp temperature/top_p
    return out

def resolve_max_tokens(platform: str, max_tokens: int | None) -> int | None:
    if max_tokens is None or max_tokens <= 0:
        return None
    # clamp per platform if needed
    return max_tokens
