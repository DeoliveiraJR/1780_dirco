# frontend/components/cards.py
"""Cards de categoria com componentes nativos Streamlit (sem HTML custom)."""
import streamlit as st
import numpy as np
import pandas as pd
from utils_ext.constants import CAT_COLORS, CAT_ICONS
from utils_ext.formatters import fmt_compact


def _get_cat_color(cat: str) -> str:
    """Busca cor da categoria (case-insensitive)."""
    cat_upper = cat.strip().upper()
    for k, v in CAT_COLORS.items():
        if k.upper() == cat_upper:
            return v
    return "#64748b"  # Fallback cinza


def _get_cat_icon(cat: str) -> str:
    """Busca ícone da categoria (case-insensitive)."""
    cat_upper = cat.strip().upper()
    for k, v in CAT_ICONS.items():
        if k.upper() == cat_upper:
            return v
    return "📊"  # Fallback: gráfico de barras


def _pct_vs(base, val):
    """Calcula delta percentual de val vs base."""
    b = float(base) if base is not None else 0.0
    v = float(val) if val is not None else 0.0
    if b == 0.0:
        return None
    return (v - b) / abs(b)


def _badge(v):
    """Badge HTML para variação."""
    if v is None:
        return '<span class="badge badge-neu">—</span>'
    if v > 0:
        return f'<span class="badge badge-pos">▲{v:+.0%}</span>'
    elif v < 0:
        return f'<span class="badge badge-neg">▼{v:.0%}</span>'
    return '<span class="badge badge-neu">0%</span>'


def _safe_array(arr, size=12):
    """Garante que o array tenha exatamente 'size' elementos, substituindo NaN por 0."""
    if arr is None:
        return [0.0] * size
    arr = list(arr)
    # Remove NaN e substitui por 0
    arr = [0.0 if (v is None or (isinstance(v, float) and np.isnan(v))) else float(v) for v in arr]
    # Garante tamanho exato
    if len(arr) < size:
        arr = arr + [0.0] * (size - len(arr))
    return arr[:size]


def _cards_categoria_html(cat: str, d: dict) -> str:
    """
    Gera HTML do card de categoria (sem CSS — CSS está em styles.py).
    
    CSS deve ser renderizado uma única vez no topo da página usando styles.CSS_CUSTOM
    """
    prev = d.get("prev", {
        "ana": [0] * 12, "mer": [0] * 12,
        "ajs": [0] * 12, "rlzd": [0] * 12
    })
    
    # Garante arrays com 12 elementos
    rlzd = _safe_array(d.get("rlzd", []))
    ana = _safe_array(d.get("ana", []))
    mer = _safe_array(d.get("mer", []))
    ajs = _safe_array(d.get("ajs", []))
    
    prev_rlzd = _safe_array(prev.get("rlzd", []))
    prev_ana = _safe_array(prev.get("ana", []))
    prev_mer = _safe_array(prev.get("mer", []))
    prev_ajs = _safe_array(prev.get("ajs", []))
    rlzd_ref = _safe_array(d.get("rlzd_ref", []))
    rlzd_ref_ano = d.get("rlzd_ref_ano") or 2025

    ref_total_abs = float(np.nansum(rlzd_ref))
    ref_media_abs = float(np.nanmean(rlzd_ref)) if len(rlzd_ref) else 0.0

    linhas = [
        ("Realizado", rlzd, prev_rlzd, "text-real"),
        ("Proj. Analítica", ana, prev_ana, "text-ana"),
        ("Proj. Mercado", mer, prev_mer, "text-mer"),
        ("Proj. Ajustada", ajs, prev_ajs, "text-ajs"),
    ]

    cor = _get_cat_color(cat)
    icone = _get_cat_icon(cat)
    
    # Cabeçalho da tabela
    header = f'''
    <div class="table-header">
        <div class="th-serie">Série</div>
        <div class="th-total">Total</div>
        <div class="th-media">Média</div>
        <div class="th-ref-total">Ref. {rlzd_ref_ano} Tot.</div>
        <div class="th-ref-media">Ref. {rlzd_ref_ano} Méd.</div>
    </div>
    '''
    
    rows = ""
    for label, cur, pr, css in linhas:
        total_num = float(np.nansum(cur))
        media_num = float(np.nanmean(cur)) if len(cur) else 0.0
        total = fmt_compact(total_num)
        media = fmt_compact(media_num)

        if label == "Realizado":
            ref_total_cell = fmt_compact(ref_total_abs)
            ref_media_cell = fmt_compact(ref_media_abs)
        else:
            ref_total_cell = _badge(_pct_vs(ref_total_abs, total_num))
            ref_media_cell = _badge(_pct_vs(ref_media_abs, media_num))

        rows += f'''
        <div class="data-row">
            <div class="col-serie {css}">{label}</div>
            <div class="col-total">{total}</div>
            <div class="col-media">{media}</div>
            <div class="col-ref-total">{ref_total_cell}</div>
            <div class="col-ref-media">{ref_media_cell}</div>
        </div>
        '''

    # Retorna APENAS o card, sem CSS (CSS está centralizado em styles.py)
    return f'''<div class="card">
        <div class="card-header">
            <div class="card-icon" style="background:{cor};">{icone}</div>
            <div class="card-title">{cat}</div>
        </div>
        <div class="data-table">
            {header}
            {rows}
        </div>
    </div>'''
