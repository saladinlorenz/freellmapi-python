from __future__ import annotations

def safe_header_value(v: str) -> str:
    out = []
    for ch in v[:256]:
        o = ord(ch)
        if 0x21 <= o <= 0x7E and ch != "%":
            out.append(ch)
        elif ch == " ":
            out.append(" ")
        elif ch == "%":
            out.append("%25")
        else:
            for b in ch.encode("utf-8"):
                out.append(f"%{b:02X}")
    return "".join(out)[:256]

def routed_via_value(platform: str, model_id: str) -> str:
    return safe_header_value(f"{platform}/{model_id}")
