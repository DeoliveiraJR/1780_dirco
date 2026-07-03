# frontend/components/cards_new.py
"""
Cards de categoria com HTML elegante + CSS inline.
Compatível com Streamlit 1.32.0 usando st.markdown(unsafe_allow_html=True).
"""
import streamlit as st
import numpy as np
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
    return "📊"  # Fallback


def _safe_array(arr, size=12):
    """Garante que o array tenha exatamente 'size' elementos."""
    if arr is None:
        return [0.0] * size
    arr = list(arr)
    arr = [0.0 if (v is None or (isinstance(v, float) and np.isnan(v))) else float(v) for v in arr]
    if len(arr) < size:
        arr = arr + [0.0] * (size - len(arr))
    return arr[:size]


def _pct_vs(base, val):
    """Calcula delta percentual de val vs base."""
    b = float(base) if base is not None else 0.0
    v = float(val) if val is not None else 0.0
    if b == 0.0:
        return None
    return (v - b) / abs(b)


def _badge_html(pct) -> str:
    """Cria HTML de badge com cor baseado em percentual."""
    if pct is None:
        return '<span style="color:#94a3b8;font-weight:600;font-size:0.9em;">—</span>'
    
    if pct >= 0:
        color = "#10b981"  # Verde
        symbol = "▲"
        text = f"{pct:+.1%}"
    else:
        color = "#ef4444"  # Vermelho
        symbol = "▼"
        text = f"{pct:.1%}"
    
    return f'<span style="color:{color};font-weight:700;font-size:0.95em;letter-spacing:0.3px;">{symbol} {text}</span>'


def render_card_streamlit(cat: str, card_data: dict) -> None:
    """
    Renderiza card elegante com HTML + CSS inline.
    
    Args:
        cat: Nome da categoria (ex: "CAPTAÇÃO")
        card_data: Dict com "rlzd", "ana", "mer", "ajs", "rlzd_ref"
    """
    # Extrair dados
    rlzd = _safe_array(card_data.get("rlzd", []))
    ana = _safe_array(card_data.get("ana", []))
    mer = _safe_array(card_data.get("mer", []))
    ajs = _safe_array(card_data.get("ajs", []))
    rlzd_ref = _safe_array(card_data.get("rlzd_ref", []))
    
    ref_total_abs = float(np.nansum(rlzd_ref))
    ref_media_abs = float(np.nanmean(rlzd_ref)) if len(rlzd_ref) else 0.0
    
    icone = _get_cat_icon(cat)
    cor = _get_cat_color(cat)
    
    # Dados das 4 linhas
    dados_linha = [
        {
            "label": "✓ Realizado",
            "valores": rlzd,
            "cor_label": "#64748b",
        },
        {
            "label": "📊 Proj. Analítica",
            "valores": ana,
            "cor_label": "#3b82f6",
        },
        {
            "label": "📈 Proj. Mercado",
            "valores": mer,
            "cor_label": "#f59e0b",
        },
        {
            "label": "✨ Proj. Ajustada",
            "valores": ajs,
            "cor_label": "#10b981",
        },
    ]
    
    # Construir HTML sem multiline f-strings
    header_html = f'<div style="border:1px solid #e2e8f0;border-radius:10px;padding:20px;background:linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);box-shadow:0 4px 12px rgba(0,0,0,0.08);font-family:\'Inter\',-apple-system,BlinkMacSystemFont,sans-serif;"><div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;padding-bottom:16px;border-bottom:3px solid {cor};"><div style="font-size:32px;line-height:1;">{icone}</div><h3 style="margin:0;color:#0f172a;font-size:1.2rem;font-weight:700;letter-spacing:-0.5px;">{cat.upper()}</h3></div>'
    
    table_header = '<div style="display:grid;grid-template-columns:1.3fr 0.95fr 0.95fr 0.95fr 0.95fr;gap:10px;padding:12px 0 10px 0;margin-bottom:4px;font-size:0.75rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;"><div>Projeção</div><div style="text-align:right;">Total</div><div style="text-align:right;">Média</div><div style="text-align:right;">vs Total</div><div style="text-align:right;">vs Média</div></div><div style="font-size:0.9rem;line-height:1.9;">'
    
    rows_html = ""
    for i, linha in enumerate(dados_linha):
        label = linha["label"]
        valores = linha["valores"]
        cor_label = linha["cor_label"]
        
        total = float(np.nansum(valores))
        media = float(np.nanmean(valores)) if len(valores) else 0.0
        
        # Calcular badges
        if label.startswith("✓"):
            badge_total = f'<span style="color:#64748b;font-weight:700;font-size:0.9rem;">{fmt_compact(ref_total_abs)}</span>'
            badge_media = f'<span style="color:#64748b;font-weight:700;font-size:0.9rem;">{fmt_compact(ref_media_abs)}</span>'
        else:
            pct_total = _pct_vs(ref_total_abs, total)
            pct_media = _pct_vs(ref_media_abs, media)
            badge_total = _badge_html(pct_total)
            badge_media = _badge_html(pct_media)
        
        # Alternating background
        bg_color = "#f9fafb" if i % 2 == 1 else "transparent"
        
        row_html = f'<div style="display:grid;grid-template-columns:1.3fr 0.95fr 0.95fr 0.95fr 0.95fr;gap:10px;align-items:center;padding:12px 10px;background-color:{bg_color};border-radius:6px;border-left:3px solid {cor_label};margin-bottom:4px;transition:all 0.2s ease;cursor:default;" onmouseover="this.style.backgroundColor=\'#f1f5f9\';this.style.boxShadow=\'0 2px 8px rgba(0,0,0,0.06)\';" onmouseout="this.style.backgroundColor=\'{bg_color}\';this.style.boxShadow=\'\';" ><span style="color:{cor_label};font-weight:700;font-size:0.95rem;">{label}</span><span style="color:#1e293b;font-weight:600;text-align:right;font-size:0.9rem;">{fmt_compact(total)}</span><span style="color:#1e293b;font-weight:600;text-align:right;font-size:0.9rem;">{fmt_compact(media)}</span><div style="text-align:right;">{badge_total}</div><div style="text-align:right;">{badge_media}</div></div>'
        rows_html += row_html
    
    footer_html = '</div></div></div>'
    
    html_card = header_html + table_header + rows_html + footer_html
    
    st.markdown(html_card, unsafe_allow_html=True)
