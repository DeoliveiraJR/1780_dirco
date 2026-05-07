# frontend/components/cards.py
"""Cards de categoria com layout legível e cabeçalhos."""
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
    return "📊"  # Fallback: gráfico de barras


_CARD_CSS = """
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body, html { margin: 0; padding: 0; background: transparent; }

.card {
  border-radius: 12px;
  padding: 14px 16px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.06);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #1e293b;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f1f5f9;
}

.card-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: white;
  font-size: 16px;
}

.card-title {
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  color: #0f172a;
}

.data-table {
  width: 100%;
}

.table-header {
  display: flex;
  align-items: center;
  padding: 4px 0 6px 0;
  border-bottom: 2px solid #e2e8f0;
  margin-bottom: 4px;
}

.th-serie { flex: 0 0 95px; font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; }
.th-total { flex: 0 0 56px; font-size: 10px; font-weight: 700; color: #64748b; text-align: right; text-transform: uppercase; }
.th-media { flex: 0 0 54px; font-size: 10px; font-weight: 700; color: #64748b; text-align: right; text-transform: uppercase; }
.th-ref-total { flex: 0 0 72px; font-size: 9px; font-weight: 700; color: #64748b; text-align: right; text-transform: uppercase; }
.th-ref-media { flex: 0 0 72px; font-size: 9px; font-weight: 700; color: #64748b; text-align: right; text-transform: uppercase; }

.data-row {
  display: flex;
  align-items: center;
  padding: 5px 0;
  border-bottom: 1px solid #f8fafc;
}

.data-row:last-child {
  border-bottom: none;
}

.col-serie {
  flex: 0 0 95px;
  font-size: 12px;
  font-weight: 600;
}

.col-total {
  flex: 0 0 56px;
  font-size: 12px;
  font-weight: 700;
  text-align: right;
}

.col-media {
  flex: 0 0 54px;
  font-size: 11px;
  text-align: right;
  color: #475569;
}

.col-ref-total {
  flex: 0 0 72px;
  text-align: right;
}

.col-ref-media {
  flex: 0 0 72px;
  text-align: right;
}

.badge {
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 600;
}

.badge-pos { background: #dcfce7; color: #166534; }
.badge-neg { background: #fee2e2; color: #dc2626; }
.badge-neu { background: #f1f5f9; color: #64748b; }

.text-real { color: #475569; }
.text-ana { color: #1d4ed8; }
.text-mer { color: #d97706; }
.text-ajs { color: #059669; }
</style>
"""


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
    """Gera HTML do card de categoria com cabeçalhos."""
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

    return f'''
    {_CARD_CSS}
    <div class="card">
        <div class="card-header">
            <div class="card-icon" style="background:{cor};">{icone}</div>
            <div class="card-title">{cat}</div>
        </div>
        <div class="data-table">
            {header}
            {rows}
        </div>
    </div>
    '''
