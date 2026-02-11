# frontend/components/donut.py
import math
import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, FullscreenTool
from utils_ext.constants import COR_ANALITICA, COR_MERCADO, COR_AJUSTADA, CAT_COLORS


def _get_cat_color(cat: str) -> str:
    """Busca cor da categoria (case-insensitive)."""
    cat_upper = cat.strip().upper()
    for k, v in CAT_COLORS.items():
        if k.upper() == cat_upper:
            return v
    return "#64748b"  # Fallback cinza


def _grafico_pizza_share_categoria(cat: str, d: dict, stylesheet):
    """
    DEPRECATED: Use _grafico_pizza_share_por_projecao para mostrar share de categorias.
    Este gráfico mostra share das projeções dentro de uma categoria.
    """
    tot_ana = float(np.nansum(d["ana"]))
    tot_mer = float(np.nansum(d["mer"]))
    tot_ajs = float(np.nansum(d["ajs"]))
    vals   = np.array([tot_ana, tot_mer, tot_ajs], dtype=float)
    labels = ["Analítica", "Mercado", "Ajustada"]
    colors = [COR_ANALITICA, COR_MERCADO, COR_AJUSTADA]

    total = float(vals.sum())
    shares = (vals / total * 100.0) if total > 0 else np.array([0.0,0.0,0.0])

    # Ângulos com fechamento exato (evita "fresta")
    if total > 0:
        angs = (vals / total) * (2*math.pi)
        diff = (2*math.pi) - float(angs.sum())
        if abs(diff) > 1e-9:
            angs[int(np.argmax(angs))] = float(angs[int(np.argmax(angs))] + diff)
    else:
        angs = np.array([0.0,0.0,0.0])

    starts = np.cumsum(np.insert(angs[:-1], 0, 0.0))
    ends   = np.cumsum(angs)

    src = ColumnDataSource(dict(
        start=starts, end=ends, color=colors, label=labels,
        valor=vals.tolist(), share=[float(x) for x in shares]
    ))

    p = figure(
        height=280,
        sizing_mode="stretch_width",
        x_range=(-1.25, 1.25), y_range=(-1.10, 1.10),
        title="🍩 Share das Projeções (%)",
        toolbar_location=None, stylesheets=[stylesheet],
        match_aspect=True
    )
    p.axis.visible=False; p.grid.visible=False
    p.min_border=10
    p.min_border_left=12; p.min_border_right=12
    p.min_border_top=8;   p.min_border_bottom=12
    p.outline_line_alpha=0.0

    p.annular_wedge(0, 0, inner_radius=0.58, outer_radius=0.98,
                    start_angle="start", end_angle="end",
                    color="color", line_color="#ffffff", line_width=2,
                    source=src)

    p.add_tools(HoverTool(tooltips=[
        ("Série", "@label"),
        ("Total", "@valor{0,0}"),
        ("Share", "@share{0.0}%")
    ]))

    # Legenda compacta
    y = 0.95
    for lab, color, pct in zip(labels, colors, shares):
        p.rect(x=-0.95, y=y, width=0.12, height=0.12, color=color)
        p.text(x=[-0.78], y=[y], text=[f"{lab}: {pct:0.1f}%"],
               text_font_size="10.5pt", text_color="#0b1320")
        y -= 0.20

    return p


def _grafico_pizza_share_por_projecao(tipo_projecao: str, agreg: dict, stylesheet):
    """
    Gráfico de pizza que mostra o % share de CADA CATEGORIA para um tipo de projeção específico.
    
    tipo_projecao: "ana" (Analítica), "mer" (Mercado) ou "ajs" (Ajustada)
    agreg: dicionário {categoria: {"ana":[12], "mer":[12], "ajs":[12], ...}}
    """
    titulos = {
        "ana": "Proj. Analítica",
        "mer": "Proj. Mercado",
        "ajs": "Proj. Ajustada"
    }
    
    # Calcula totais por categoria
    categorias = []
    valores = []
    cores = []
    
    for i, (cat, d) in enumerate(agreg.items()):
        total_cat = float(np.nansum(d.get(tipo_projecao, [0]*12)))
        if total_cat > 0:
            categorias.append(cat)
            valores.append(total_cat)
            # Usa lookup case-insensitive para cores
            cores.append(_get_cat_color(cat))
    
    vals = np.array(valores, dtype=float)
    total = float(vals.sum())
    shares = (vals / total * 100.0) if total > 0 else np.zeros(len(vals))
    
    # Ângulos
    if total > 0:
        angs = (vals / total) * (2*math.pi)
        diff = (2*math.pi) - float(angs.sum())
        if abs(diff) > 1e-9 and len(angs) > 0:
            angs[int(np.argmax(angs))] = float(angs[int(np.argmax(angs))] + diff)
    else:
        angs = np.zeros(len(vals))
    
    starts = np.cumsum(np.insert(angs[:-1], 0, 0.0)) if len(angs) > 0 else np.array([0.0])
    ends = np.cumsum(angs) if len(angs) > 0 else np.array([0.0])
    
    src = ColumnDataSource(dict(
        start=starts.tolist(), end=ends.tolist(), 
        color=cores, label=categorias,
        valor=valores, share=[float(x) for x in shares]
    ))
    
    # Dimensões com largura flexível e melhor proporção
    p = figure(
        height=280,
        sizing_mode="stretch_width",
        x_range=(-1.4, 1.4), y_range=(-1.15, 1.15),
        title=f"🍩 Share (%) - {titulos.get(tipo_projecao, '')}",
        toolbar_location="right", stylesheets=[stylesheet],
    )
    p.toolbar.logo = None  # Remove logo Bokeh
    p.axis.visible = False
    p.grid.visible = False
    p.min_border = 6
    p.min_border_left = 6
    p.min_border_right = 6
    p.min_border_top = 4
    p.min_border_bottom = 6
    p.outline_line_alpha = 0.0
    p.title.text_font_size = "11pt"
    p.title.text_color = "#1e293b"
    p.title.align = "center"
    p.background_fill_color = "#fafbfc"
    
    if len(categorias) > 0:
        p.annular_wedge(0, 0, inner_radius=0.45, outer_radius=0.88,
                        start_angle="start", end_angle="end",
                        color="color", line_color="#ffffff", line_width=2.5,
                        source=src)
        
        p.add_tools(HoverTool(tooltips=[
            ("Categoria", "@label"),
            ("Total", "R$ @valor{0,0}"),
            ("Share", "@share{0.1}%")
        ]))
    
    # Legenda dentro do donut (no centro) - texto mais legível
    y_start = 0.12 * (len(categorias) - 1) / 2
    for idx, (lab, color, pct) in enumerate(zip(categorias, cores, shares)):
        lab_short = lab[:10] if len(lab) > 10 else lab
        y_pos = y_start - (idx * 0.18)
        p.rect(x=-0.18, y=y_pos, width=0.10, height=0.10, color=color, line_color=None)
        p.text(x=[-0.09], y=[y_pos], text=[f"{pct:.1f}%"],
               text_font_size="10pt", text_color="#1e293b", text_font_style="bold",
               text_baseline="middle")
    
    p.add_tools(FullscreenTool())  # Tela cheia
    return p

