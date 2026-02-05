# frontend/utils_ext/formatters.py
def fmt_br(v: float, casas: int = 0) -> str:
    """
    Formata número em pt-BR (milhar '.' e decimal ',').
    """
    try:
        s = f"{float(v):,.{casas}f}"
    except Exception:
        return "-"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_compact(v: float) -> str:
    """
    Formata número de forma compacta (bi/mi/mil).
    """
    try:
        v = float(v)
        if abs(v) >= 1e12:
            return f"{v/1e12:.1f}T"
        if abs(v) >= 1e9:
            return f"{v/1e9:.1f}B"
        if abs(v) >= 1e6:
            return f"{v/1e6:.1f}M"
        if abs(v) >= 1e3:
            return f"{v/1e3:.1f}K"
        return f"{v:.0f}"
    except Exception:
        return "-"