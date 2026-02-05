# frontend/utils_ext/css.py
from bokeh.models import InlineStyleSheet

BOKEH_CSS = """
:host, .bk, .bk-root {
  --uan-primary: #0c3a66;
  --uan-accent:  #06b6d4;
  --uan-muted:   #64748b;
  --uan-bg:      #f7fbff;
  --uan-grid:    rgba(12,58,102,0.08);

  --ok-bg:   #d1fae5; --ok-fg:#065f46; --ok-br: #10b981;
  --bad-bg:  #fee2e2; --bad-fg:#7f1d1d; --bad-br:#ef4444;
  --neu-bg:  #e5e7eb; --neu-fg:#0b1320; --neu-br:#9ca3af;

  --header-fg: #0b1320;
  --header-bg: #e8eef6;
  --row-even:  #ffffff;
  --row-odd:   #f9fbff;

  --sum1-bg:   #eaf6ff;   /* MÉDIA/VAR% */
  --sum2-bg:   #e8fff4;   /* CRESC. VOL */

  font-family: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 14px;
}

/* Títulos / eixos / legenda */
.bk-title { color: var(--uan-primary) !important; font-weight: 800 !important; margin: 2px 0 0 0 !important;}
.bk-axis .bk-axis-label { font-weight: 700; color: var(--uan-primary); }
.bk-axis .bk-tick-label { color: #0b1320; font-size: 13px; }
.bk-grid { stroke: var(--uan-grid) !important; }
.bk-legend { background-color: rgba(247,251,255,.96) !important; border-radius: 8px; padding: 4px 8px; margin: 0 !important;}
.bk-legend .bk-legend-item-label { font-size: 12pt; font-weight: 700; color:#0b1320; }

/* DataTable (SlickGrid) */
.bk-data-table { --row-h: 32px; }
.bk-data-table .slick-header-columns {
  background: var(--header-bg) !important;
  border: none !important; height: calc(var(--row-h) + 6px) !important;
}
.bk-data-table .slick-header-column {
  color: var(--header-fg) !important; font-weight: 900 !important; font-size: 14px !important;
  border-right: 1px solid rgba(15,23,42,0.08) !important;
}
.bk-data-table .slick-row { font-size: 14px !important; height: var(--row-h) !important; }
.bk-data-table .slick-row.even { background-color: var(--row-even) !important; }
.bk-data-table .slick-row.odd  { background-color: var(--row-odd) !important; }
.bk-data-table .bk-cell { padding: 8px 10px !important; color:#0b1320; }
.bk-data-table .bk-cell.bk-number { text-align: right !important; }

/* Destaque das duas últimas linhas */
.bk-data-table .slick-row:nth-last-child(2) .bk-cell {
  background: var(--sum1-bg) !important;
  font-weight: 900 !important;
  font-size: 15px !important;
  border-top: 2px solid rgba(12,58,102,0.20);
}
.bk-data-table .slick-row:last-child .bk-cell {
  background: var(--sum2-bg) !important;
  font-weight: 900 !important;
  font-size: 15px !important;
  border-top: 2px solid rgba(12,58,102,0.20);
}

/* Badges pastel */
.uan-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 10px; border-radius: 999px; font-weight: 800; font-size: 12.5px; line-height: 1;
  border:1px solid transparent;
}
.uan-badge.pos { background: var(--ok-bg);  color: var(--ok-fg);  border-color: var(--ok-br); }
.uan-badge.neg { background: var(--bad-bg); color: var(--bad-fg); border-color: var(--bad-br); }
.uan-badge.neu { background: var(--neu-bg); color: var(--neu-fg); border-color: var(--neu-br); }
.uan-badge::before { display:inline-block; width: 10px; text-align:center; }
.uan-badge.pos::before { content: "▲"; }
.uan-badge.neg::before { content: "▼"; }
.uan-badge.neu::before { content: "•"; }

/* Scrollbar */
.bk-data-table ::-webkit-scrollbar { height: 8px; width: 8px; }
.bk-data-table ::-webkit-scrollbar-thumb { background: rgba(12,58,102,.25); border-radius: 8px; }
"""

def make_stylesheet():
    return InlineStyleSheet(css=BOKEH_CSS)