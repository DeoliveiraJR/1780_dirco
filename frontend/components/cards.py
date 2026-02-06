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

.th-serie { flex: 0 0 100px; font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; }
.th-total { flex: 0 0 65px; font-size: 10px; font-weight: 700; color: #64748b; text-align: right; text-transform: uppercase; }
.th-media { flex: 0 0 60px; font-size: 10px; font-weight: 700; color: #64748b; text-align: right; text-transform: uppercase; }
.th-var { flex: 1; font-size: 10px; font-weight: 700; color: #64748b; text-align: right; text-transform: uppercase; }

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
  flex: 0 0 100px;
  font-size: 12px;
  font-weight: 600;
}

.col-total {
  flex: 0 0 65px;
  font-size: 13px;
  font-weight: 700;
  text-align: right;
}

.col-media {
  flex: 0 0 60px;
  font-size: 12px;
  text-align: right;
  color: #475569;
}

.col-var {
  flex: 1;
  text-align: right;
}

.badge {
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 11px;
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


def _var_pct(prev, cur):
    """Calcula variação percentual."""
    p = float(np.nansum(prev)) if prev else 0.0
    c = float(np.nansum(cur)) if cur else 0.0
    if p == 0.0:
        return None
    return (c - p) / abs(p)


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

    linhas = [
        ("Realizado", rlzd, prev_rlzd, "text-real"),
        ("Proj. Analítica", ana, prev_ana, "text-ana"),
        ("Proj. Mercado", mer, prev_mer, "text-mer"),
        ("Proj. Ajustada", ajs, prev_ajs, "text-ajs"),
    ]

    cor = _get_cat_color(cat)
    icone = _get_cat_icon(cat)
    
    # Cabeçalho da tabela
    header = '''
    <div class="table-header">
        <div class="th-serie">Série</div>
        <div class="th-total">Total</div>
        <div class="th-media">Média</div>
        <div class="th-var">Var. %</div>
    </div>
    '''
    
    rows = ""
    for label, cur, pr, css in linhas:
        total = fmt_compact(float(np.nansum(cur)))
        media = fmt_compact(float(np.nanmean(cur)) if len(cur) else 0.0)
        var = _var_pct(pr, cur)
        rows += f'''
        <div class="data-row">
            <div class="col-serie {css}">{label}</div>
            <div class="col-total">{total}</div>
            <div class="col-media">{media}</div>
            <div class="col-var">{_badge(var)}</div>
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
