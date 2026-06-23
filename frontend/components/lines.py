# frontend/components/lines.py
import numpy as np
import pandas as pd
from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource, Legend, LegendItem, NumeralTickFormatter,
    DatetimeTickFormatter, FullscreenTool
)

from utils_ext.constants import (
    MESES_NUM, MESES_ABR, COR_RLZD_BASE, COR_ANALITICA_L, COR_MERCADO_L, COR_AJUSTADA
)
from utils_ext.series import _norm_txt, _mes_to_num, _ensure_cli_n, _mask_trailing_zeros


def _grafico_visao_anual_linhas(realizados_dict: dict, ana: list, mer: list, ajs: list,
                                ano_proj: int, stylesheet, src_ajs_ref: ColumnDataSource | None = None):
    p = figure(height=380, sizing_mode="stretch_width",
               x_range=(0.5,12.5),
               title="📊 VISÃO ANUAL • Realizado vs Projeções",
               stylesheets=[stylesheet], toolbar_location="right")
    p.background_fill_color="#f7fbff"; p.grid.grid_line_alpha=0.22
    p.min_border_top = 2; p.min_border_bottom = 2
    p.yaxis.formatter = NumeralTickFormatter(format="0.00a")
    p.xaxis.axis_label = "Mês"; p.yaxis.axis_label = "Valor (R$)"
    p.title.text_font_size = "11pt"
    p.xaxis.major_label_text_font_size = "10px"
    p.yaxis.major_label_text_font_size = "10px"
    p.xaxis.ticker = MESES_NUM
    p.xaxis.major_label_overrides = {i: MESES_ABR[i] for i in MESES_NUM}

    renderers = []
    if realizados_dict:
        anos = sorted(realizados_dict.keys())
        alphas = np.linspace(0.30, 0.70, num=len(anos))
        for i, ano in enumerate(anos):
            y = realizados_dict[ano]
            src = ColumnDataSource(dict(x=MESES_NUM, y=y))
            r1 = p.line("x","y", source=src, color=COR_RLZD_BASE, alpha=float(alphas[i]), line_width=2.25)
            p.circle("x","y", source=src, color=COR_RLZD_BASE, alpha=float(alphas[i]), size=4)
            renderers.append((f"{ano} Realizado", [r1]))

    ano_lbl = f" {ano_proj}" if ano_proj else ""
    if ana:
        r_ana = p.line("x","y", source=ColumnDataSource(dict(x=MESES_NUM, y=ana)),
                       color=COR_ANALITICA_L, line_width=3, muted_alpha=0.15)
        renderers.append((f"{ano_lbl} Proj. Analítica", [r_ana]))
    if mer:
        r_mer = p.line("x","y", source=ColumnDataSource(dict(x=MESES_NUM, y=mer)),
                       color=COR_MERCADO_L, line_width=3, line_dash="dashed", muted_alpha=0.15)
        renderers.append((f"{ano_lbl} Proj. Mercado", [r_mer]))
    if src_ajs_ref is not None:
        r_ajs = p.line("x","y", source=src_ajs_ref,
                       color=COR_AJUSTADA, line_width=3, line_dash="dotted", muted_alpha=0.15)
        renderers.append((f"{ano_lbl} Proj. Ajustada", [r_ajs]))
    elif ajs:
        r_ajs = p.line("x","y", source=ColumnDataSource(dict(x=MESES_NUM, y=ajs)),
                       color=COR_AJUSTADA, line_width=3, line_dash="dotted", muted_alpha=0.15)
        renderers.append((f"{ano_lbl} Proj. Ajustada", [r_ajs]))

    legend = Legend(items=[LegendItem(label=lab, renderers=rens) for lab, rens in renderers],
                    click_policy="mute", orientation="horizontal", label_text_font_size="12pt")
    p.add_layout(legend, "above")
    p.add_tools(FullscreenTool())  # Tela cheia
    return p


def _grafico_serie_historica(df_upload: pd.DataFrame, cliente: str,
                             categoria: str, produto: str,
                             ana: list, mer: list, ajs: list,
                             ano_proj: int, stylesheet,
                             src_ajs_ref: ColumnDataSource | None = None,
                             mes_proj: int = 1,
                             cd_tip_agpd: str = "Todos",
                             tip_td: str = "Todos"):
    p = figure(height=380, sizing_mode="stretch_width", x_axis_type="datetime",
               title="🕒 SÉRIE HISTÓRICA • Realizado vs Projeções",
               stylesheets=[stylesheet], toolbar_location="right")
    p.background_fill_color="#f7fbff"; p.grid.grid_line_alpha=0.22
    p.min_border_top = 2; p.min_border_bottom = 2
    p.yaxis.formatter = NumeralTickFormatter(format="0.00a")
    p.xaxis.formatter = DatetimeTickFormatter(months="%b %Y", years="%Y")
    p.yaxis.axis_label = "Valor (R$)"
    p.title.text_font_size = "11pt"
    p.xaxis.major_label_text_font_size = "10px"
    p.yaxis.major_label_text_font_size = "10px"

    renderers = []

    dff = _ensure_cli_n(df_upload)
    if cliente and cliente != "Todos":
        dff = dff[dff["CLI_N"] == _norm_txt(cliente)]
    if "CAT_N" not in dff.columns:
        dff["CAT_N"] = dff["CATEGORIA"].astype(str).apply(_norm_txt)
    if "PROD_N" not in dff.columns:
        dff["PROD_N"] = dff["PRODUTO"].astype(str).apply(_norm_txt)
    dff = dff[dff["CAT_N"] == _norm_txt(categoria)]
    produto_norm = _norm_txt(produto)
    if produto_norm and produto_norm != "todos":
        dff = dff[dff["PROD_N"] == produto_norm]

    if "CD_TIP_AGPD" in dff.columns and cd_tip_agpd and cd_tip_agpd != "Todos":
        dff = dff[dff["CD_TIP_AGPD"].astype(str).apply(_norm_txt) == _norm_txt(cd_tip_agpd)]
    if "TIP_TD" in dff.columns and tip_td and tip_td != "Todos":
        dff = dff[dff["TIP_TD"].astype(str).apply(_norm_txt) == _norm_txt(tip_td)]

    if dff.empty:
        return p

    if "MES_NUM" not in dff.columns:
        dff["MES_NUM"] = dff["MES"].apply(_mes_to_num) if "MES" in dff.columns else np.nan
    if "ANO_NUM" not in dff.columns and "ANO" in dff.columns:
        dff["ANO_NUM"] = pd.to_numeric(dff["ANO"], errors="coerce").fillna(0).astype(int)
    elif "ANO_NUM" not in dff.columns:
        dff["ANO_NUM"] = 0
    dff["MES_NUM"] = pd.to_numeric(dff["MES_NUM"], errors="coerce")
    dff = dff[dff["MES_NUM"].between(1,12)]
    dff = dff[pd.to_numeric(dff["ANO_NUM"], errors="coerce") >= 2022]

    col_realizado = "CURVA_REALIZADO" if "CURVA_REALIZADO" in dff.columns else ("REALIZADO" if "REALIZADO" in dff.columns else None)
    if col_realizado:
        dff["TS"] = pd.to_datetime(dict(year=dff["ANO_NUM"].astype(int), month=dff["MES_NUM"].astype(int), day=1))
        grp = dff.groupby(["TS"], as_index=False)[col_realizado].sum().sort_values("TS")
        y_vals = grp[col_realizado].astype(float).tolist()
        y_vals = _mask_trailing_zeros(y_vals)  # evita “queda” no fim
        src_r = ColumnDataSource(dict(x=grp["TS"], y=y_vals))
        r_rl = p.line("x","y", source=src_r, color=COR_RLZD_BASE, line_width=3)
        p.circle("x","y", source=src_r, color=COR_RLZD_BASE, size=4)
        renderers.append(("Realizado", [r_rl]))

    if ano_proj:
        ano_base = int(ano_proj)
        idx = pd.date_range(f"{ano_base}-01-01", periods=24, freq="MS")

        def _safe24(vals):
            base = list(vals) if isinstance(vals, list) else []
            return (base + [0.0] * 24)[:24]

        def _tem_realizado(v):
            try:
                vv = float(v)
                return np.isfinite(vv) and vv != 0.0
            except Exception:
                return False

        ana24 = _safe24(ana)
        mer24 = _safe24(mer)
        ajs24 = _safe24(ajs)

        rlzd_years = (
            dff.groupby(["ANO_NUM", "MES_NUM"], as_index=False)[col_realizado]
               .sum()
            if col_realizado
            else pd.DataFrame()
        )

        for i in range(24):
            ano_i = ano_base if i < 12 else ano_base + 1
            mes_i = (i % 12) + 1
            if not rlzd_years.empty:
                fatia = rlzd_years[(rlzd_years["ANO_NUM"] == ano_i) & (rlzd_years["MES_NUM"] == mes_i)]
                if not fatia.empty:
                    rv = float(fatia[col_realizado].iloc[0])
                    if _tem_realizado(rv):
                        ana24[i] = rv
                        mer24[i] = rv
                        ajs24[i] = rv

        src_ana = ColumnDataSource(dict(x=idx, y=ana24))
        src_mer = ColumnDataSource(dict(x=idx, y=mer24))
        src_ajs = ColumnDataSource(dict(x=idx, y=ajs24))

        r_a = p.line("x", "y", source=src_ana,
                     color=COR_ANALITICA_L, line_width=3, muted_alpha=0.15)
        r_m = p.line("x", "y", source=src_mer,
                     color=COR_MERCADO_L, line_width=3,
                     line_dash="dashed", muted_alpha=0.15)
        r_aj = p.line("x", "y", source=src_ajs,
                      color=COR_AJUSTADA, line_width=3, muted_alpha=0.15)
        p.circle("x", "y", source=src_ajs, color=COR_AJUSTADA, size=5)

        renderers.append(("Proj. Analítica", [r_a]))
        renderers.append(("Proj. Mercado", [r_m]))
        renderers.append(("Proj. Ajustada", [r_aj]))

    legend = Legend(items=[LegendItem(label=lab, renderers=rens) for lab, rens in renderers],
                    click_policy="mute", orientation="horizontal", label_text_font_size="12pt")
    p.add_layout(legend, "above")
    p.add_tools(FullscreenTool())  # Tela cheia
    return p