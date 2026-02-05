# frontend/components/bars.py
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Legend, LegendItem, NumeralTickFormatter, HoverTool
from bokeh.transform import dodge
from utils_ext.constants import MESES_ABR_LIST, COR_ANALITICA, COR_MERCADO, COR_AJUSTADA, COR_RLZD_BASE, CAT_COLORS


def _get_cat_color(cat: str) -> str:
    """Busca cor da categoria (case-insensitive)."""
    cat_upper = cat.strip().upper()
    for k, v in CAT_COLORS.items():
        if k.upper() == cat_upper:
            return v
    return "#1e40af"  # Fallback azul


def _grafico_barras_categoria(cat: str, d: dict, stylesheet):
    """Gráfico de barras para uma categoria com 4 séries: Real, Analítica, Mercado e Ajustada."""
    months = MESES_ABR_LIST
    # Trunca nome da categoria se muito longo
    cat_short = cat[:12] + ".." if len(cat) > 12 else cat
    
    # Cor do título baseada na categoria (case-insensitive)
    cat_color = _get_cat_color(cat)

    p = figure(
        height=280,
        sizing_mode="stretch_width",
        x_range=months,
        stylesheets=[stylesheet],
        title=f"📊 {cat_short.upper()}",
        toolbar_location=None
    )
    p.background_fill_color = "#fafbfc"
    p.grid.grid_line_alpha = 0.25
    p.grid.grid_line_color = "#cbd5e1"
    p.min_border_top = 28
    p.min_border_bottom = 18
    p.min_border_left = 50
    p.min_border_right = 8
    p.yaxis.formatter = NumeralTickFormatter(format="0.00a")
    p.xaxis.major_label_text_font_size = "9pt"
    p.yaxis.major_label_text_font_size = "9pt"
    p.xaxis.major_label_text_color = "#334155"
    p.yaxis.major_label_text_color = "#334155"
    p.xaxis.axis_label = "Mês"
    p.yaxis.axis_label = "Valor (R$)"
    p.xaxis.axis_label_text_font_size = "10pt"
    p.yaxis.axis_label_text_font_size = "10pt"
    p.title.text_font_size = "11pt"
    p.title.text_color = cat_color
    p.title.align = "center"
    p.outline_line_color = "#e2e8f0"

    src = ColumnDataSource(dict(
        x=months,
        rlzd=[d["rlzd"][i] for i in range(12)],
        ana=[d["ana"][i] for i in range(12)],
        mer=[d["mer"][i] for i in range(12)],
        ajs=[d["ajs"][i] for i in range(12)],
    ))

    # 4 barras: largura ajustada para caber todas
    w = 0.18
    offsets = [-0.27, -0.09, 0.09, 0.27]
    
    r1 = p.vbar(x=dodge('x', offsets[0], range=p.x_range), top='rlzd',
                width=w, source=src, color=COR_RLZD_BASE, alpha=0.85)
    r2 = p.vbar(x=dodge('x', offsets[1], range=p.x_range), top='ana',
                width=w, source=src, color=COR_ANALITICA, alpha=0.9)
    r3 = p.vbar(x=dodge('x', offsets[2], range=p.x_range), top='mer',
                width=w, source=src, color=COR_MERCADO, alpha=0.9)
    r4 = p.vbar(x=dodge('x', offsets[3], range=p.x_range), top='ajs',
                width=w, source=src, color=COR_AJUSTADA, alpha=0.9)

    # Tooltip para hover
    p.add_tools(HoverTool(
        tooltips=[
            ("Mês", "@x"),
            ("Realizado", "@rlzd{0,0}"),
            ("Analítica", "@ana{0,0}"),
            ("Mercado", "@mer{0,0}"),
            ("Ajustada", "@ajs{0,0}"),
        ],
        mode="vline"
    ))

    legend = Legend(
        items=[
            LegendItem(label="Real", renderers=[r1]),
            LegendItem(label="Anal.", renderers=[r2]),
            LegendItem(label="Merc.", renderers=[r3]),
            LegendItem(label="Ajust.", renderers=[r4]),
        ],
        orientation="horizontal",
        label_text_font_size="9pt",
        label_text_color="#475569",
        spacing=12,
        padding=6,
        margin=6,
        glyph_width=14,
        glyph_height=14,
        location="top_center",
        background_fill_alpha=0.0,
        border_line_alpha=0.0,
    )
    p.add_layout(legend, 'above')

    return p