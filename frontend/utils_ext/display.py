# frontend/utils_ext/display.py
import numpy as np

def _badge_html_from_value(v: float, show_value: bool = True) -> str:
    """
    Retorna HTML de badge (▲/▼/•) com classes 'uan-badge {pos|neg|neu}'.
    Mantém o mesmo visual que você já usa no CSS do Bokeh.
    """
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "<span class='uan-badge neu'>—</span>"
    try:
        v = float(v)
    except Exception:
        return "<span class='uan-badge neu'>—</span>"

    if v > 0:
        txt = f"{v:,.2%}" if show_value else ""
        return f"<span class='uan-badge pos'>{txt}</span>"
    if v < 0:
        txt = f"{v:,.2%}" if show_value else ""
        return f"<span class='uan-badge neg'>{txt}</span>"
    txt = f"{v:,.2%}" if show_value else ""
    return f"<span class='uan-badge neu'>{txt}</span>"

def _build_var_disp_column(var_values, is_media_row_index=12, is_cresc_row_index=13):
    """
    Constrói a coluna "…_Disp" com os badges HTML para cada célula da coluna de variação (%).
    - Nas linhas comuns: badge com valor (xx,xx%).
    - Na linha de 'CRESC. VOL' (última): badge apenas com o ícone (sem texto), usando +1, -1 ou 0.
    """
    disp = []
    for i, v in enumerate(var_values):
        if i == is_cresc_row_index:
            # Para a última linha, mostramos apenas o ícone, sem texto
            if isinstance(v, str):
                vnum = 1.0 if "▲" in v else (-1.0 if "▼" in v else 0.0)
            else:
                try:
                    vv = float(v)
                except Exception:
                    vv = 0.0
                vnum = 1.0 if vv > 0 else (-1.0 if vv < 0 else 0.0)
            disp.append(_badge_html_from_value(vnum, show_value=False))
        else:
            try:
                vv = float(v)
                if not np.isfinite(vv):
                    vv = 0.0
            except Exception:
                vv = 0.0
            disp.append(_badge_html_from_value(vv, show_value=True))
    return disp