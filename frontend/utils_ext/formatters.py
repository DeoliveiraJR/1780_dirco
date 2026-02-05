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


def fmt_compact(v: float, decimais: int = 2) -> str:
    """
    Formata número de forma compacta (T/B/M/K).
    Usa mais casas decimais para sensibilidade a alterações pequenas.
    """
    try:
        v = float(v)
        if abs(v) >= 1e12:
            return f"{v/1e12:.{decimais}f}T"
        if abs(v) >= 1e9:
            return f"{v/1e9:.{decimais}f}B"
        if abs(v) >= 1e6:
            return f"{v/1e6:.{decimais}f}M"
        if abs(v) >= 1e3:
            return f"{v/1e3:.{decimais}f}K"
        return f"{v:.{decimais}f}"
    except Exception:
        return "-"