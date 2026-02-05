# frontend/pages/simulador.py
import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import math

from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource, PointDrawTool, DataTable, TableColumn,
    StringFormatter, CustomJS, HTMLTemplateFormatter,
    NumeralTickFormatter, HoverTool, DatetimeTickFormatter,
    Legend, LegendItem
)
from bokeh.layouts import column, row
from bokeh.transform import dodge
from streamlit_bokeh import streamlit_bokeh

from utils_ext.css import make_stylesheet
from utils_ext.formatters import fmt_br
from utils_ext.series import (
    _norm_txt, _mes_to_num, _variacao_mensal, _ensure_cli_n, _mask_trailing_zeros
)
from utils_ext.constants import (
    MESES_FULL, MESES_NUM, MESES_ABR, MESES_ABR_LIST,
    COR_ANALITICA, COR_MERCADO, COR_AJUSTADA, COR_RLZD_BASE,
    COR_MERCADO_L, COR_ANALITICA_L, CAT_COLORS
)
from utils_ext.display import _badge_html_from_value, _build_var_disp_column

from services.aggregations import (
    _carregar_curvas_base, _obter_realizados_por_ano, _agregados_por_categoria,
    _carregar_ajustada_produto
)

from components.lines import _grafico_visao_anual_linhas, _grafico_serie_historica
from components.bars import _grafico_barras_categoria
from components.donut import _grafico_pizza_share_categoria, _grafico_pizza_share_por_projecao
from components.cards import _cards_categoria_html

from streamlit import components

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_manager import get_dados_upload

MASCARAR_ZEROS_FINAIS = True


def renderizar():
    st.markdown("# 🎯 Simulador de Projeções")

    # CSS para espaçamento compacto global - reduz gaps entre seções
    st.markdown("""
    <style>
      /* Container principal */
      section.main > div.block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
      }
      /* Reduz gap vertical entre blocos */
      div[data-testid="stVerticalBlock"] > div {
        gap: 0.5rem !important;
      }
      /* Remove margem inferior de elementos */
      div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0 !important;
      }
      /* Colunas do Streamlit - reduz gap */
      div[data-testid="column"] {
        padding: 0 0.25rem !important;
      }
      /* Elementos inside columns */
      div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
      }
      /* Bokeh widgets */
      .stBokeh {
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
      }
      /* Headers compactos */
      h1 { margin-bottom: 0.5rem !important; }
      h2 { margin: 0.75rem 0 0.5rem 0 !important; font-size: 1.3rem !important; }
      h3, h4 { margin: 0.5rem 0 0.25rem 0 !important; font-size: 1.1rem !important; }
      hr { margin: 0.5rem 0 !important; }
      /* iFrames */
      iframe { border: none !important; }
      /* Markdown headers na seção de categorias */
      .uan-sec { margin-top: 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("---")

    filtros = st.session_state.get("filtros", {}) or {}
    df_upload = get_dados_upload()

    if df_upload is None or df_upload.empty:
        st.warning("⚠️ Nenhum dado carregado. Vá em **Upload** e importe o Excel.")
        return

    cliente  = filtros.get("cliente", "Todos")
    categoria= filtros.get("categoria", "")
    produto  = filtros.get("produto", "")

    dff_check = _ensure_cli_n(df_upload)
    base_f = dff_check if cliente=="Todos" else dff_check[dff_check["CLI_N"] == _norm_txt(cliente)]
    if not categoria and not base_f.empty:
        categoria = str(base_f["CATEGORIA"].dropna().astype(str).unique()[0])
    base_fc = base_f[base_f["CATEGORIA"].astype(str) == str(categoria)]
    if not produto and not base_fc.empty:
        produto = str(base_fc["PRODUTO"].dropna().astype(str).unique()[0])

    analitica, mercado, ano_proj = _carregar_curvas_base(df_upload, cliente, categoria, produto)
    combo = f"{cliente}::{categoria}::{produto}"
    if st.session_state.get("last_combo") != combo:
        st.session_state["ajustada"] = analitica[:]
        st.session_state["last_combo"] = combo
    ajustada = st.session_state.get("ajustada", analitica[:])

    realizados_dict = _obter_realizados_por_ano(df_upload, cliente, categoria, produto, mascarar_zeros_finais=MASCARAR_ZEROS_FINAIS)
    anos_realizados = sorted(realizados_dict.keys())
    variacoes_rlzd = {ano: _variacao_mensal(realizados_dict[ano]) for ano in anos_realizados}

    style_top = make_stylesheet()

    # -------------------- GRÁFICO PRINCIPAL ----------------------------------
    src_ana = ColumnDataSource(dict(x=MESES_NUM, y=analitica))
    src_mer = ColumnDataSource(dict(x=MESES_NUM, y=mercado))
    src_ajs = ColumnDataSource(dict(
        x=MESES_NUM,
        xm=MESES_ABR_LIST,
        y=ajustada,
        y_br=[fmt_br(v, 0) for v in ajustada]
    ))

    p = figure(
        height=400, sizing_mode="stretch_width",
        x_range=(0.5,12.5), x_axis_label="Mês", y_axis_label="Valor (R$)",
        toolbar_location="right",
        title=f"📈 Curva de Projeção Ajustada • {cliente or 'Portfólio'} • {categoria} • {produto}",
        stylesheets=[style_top]
    )
    p.background_fill_color="#f7fbff"; p.grid.grid_line_alpha=0.22
    p.min_border_top = 4; p.min_border_bottom = 4
    p.yaxis.formatter = NumeralTickFormatter(format="0.00a")
    p.title.text_font_size = "14pt"
    p.xaxis.ticker = MESES_NUM
    p.xaxis.major_label_overrides = {i: MESES_ABR[i] for i in MESES_NUM}
    p.xaxis.major_label_text_font_size = "13px"
    p.yaxis.major_label_text_font_size = "13px"

    r_ana = p.line("x","y", source=src_ana, color=COR_ANALITICA, line_width=3, muted_alpha=0.15)
    r_mer = p.line("x","y", source=src_mer, color=COR_MERCADO, line_width=3, line_dash="dashed", muted_alpha=0.15)
    r_ajs = p.line("x","y", source=src_ajs, color=COR_AJUSTADA, line_width=4, line_dash="dotted", muted_alpha=0.15)
    pts = p.scatter("x","y", source=src_ajs, size=16, color=COR_AJUSTADA, line_color="white", line_width=2, marker="circle")

    draw = PointDrawTool(renderers=[pts], empty_value=np.nan)
    p.add_tools(draw); p.toolbar.active_drag = draw
    p.add_tools(HoverTool(renderers=[pts], tooltips=[("Mês","@xm"),("Ajustada","R$ @y_br")]))

    legend = Legend(items=[
        LegendItem(label="Projeção Analítica", renderers=[r_ana]),
        LegendItem(label="Projeção Mercado",  renderers=[r_mer]),
        LegendItem(label="Projeção Ajustada", renderers=[r_ajs]),
    ], click_policy="mute", orientation="horizontal", label_text_font_size="12pt")
    p.add_layout(legend, "above")

    # -------------------- TABELA ---------------------------------------------
    var_ana = _variacao_mensal(analitica)
    var_mer = _variacao_mensal(mercado)
    var_ajs = _variacao_mensal(ajustada)

    mes_display = MESES_ABR_LIST[:]
    mes_ord    = list(range(1,13))
    tbl_data = dict(Mes=mes_display, Mes_Ord=mes_ord)

    for ano in anos_realizados:
        tbl_data[f"Rlzd_{ano}"] = realizados_dict[ano]
        tbl_data[f"Var_{ano}"]  = variacoes_rlzd[ano]

    tbl_data["Analitica"] = analitica
    tbl_data["Var_Ana"]   = var_ana
    tbl_data["Mercado"]   = mercado
    tbl_data["Var_Mer"]   = var_mer
    tbl_data["Ajustada"]  = ajustada
    tbl_data["Var_Ajs"]   = var_ajs

    def _mean_safe(v):
        v = np.array(v, dtype=float)
        return float(np.nanmean(v)) if v.size else 0.0

    media_row = {"Mes": "MÉDIA / VAR%","Mes_Ord": 13}
    for ano in anos_realizados:
        media_row[f"Rlzd_{ano}"] = _mean_safe(tbl_data[f"Rlzd_{ano}"])
        media_row[f"Var_{ano}"]  = _mean_safe(tbl_data[f"Var_{ano}"])
    media_row["Analitica"] = _mean_safe(tbl_data["Analitica"])
    media_row["Var_Ana"]   = _mean_safe(tbl_data["Var_Ana"])
    media_row["Mercado"]   = _mean_safe(tbl_data["Mercado"])
    media_row["Var_Mer"]   = _mean_safe(tbl_data["Var_Mer"])
    media_row["Ajustada"]  = _mean_safe(tbl_data["Ajustada"])
    media_row["Var_Ajs"]   = _mean_safe(tbl_data["Var_Ajs"])

    def _delta_first_last(v):
        v = list(map(float, v))
        if not v: return 0.0
        return float(v[-1] - v[0])

    cres_row = {"Mes":"CRESC. VOL","Mes_Ord":14}
    for ano in anos_realizados:
        delta = _delta_first_last(tbl_data[f"Rlzd_{ano}"])
        cres_row[f"Rlzd_{ano}"] = delta
        cres_row[f"Var_{ano}"]  = 1.0 if delta > 0 else (-1.0 if delta < 0 else 0.0)
    for field_val, field_var in [("Analitica","Var_Ana"),("Mercado","Var_Mer"),("Ajustada","Var_Ajs")]:
        delta = _delta_first_last(tbl_data[field_val])
        cres_row[field_val] = delta
        cres_row[field_var] = 1.0 if delta > 0 else (-1.0 if delta < 0 else 0.0)

    for k in list(tbl_data.keys()):
        if k == "Mes":
            tbl_data[k] = tbl_data[k] + [media_row["Mes"], cres_row["Mes"]]
        elif k == "Mes_Ord":
            tbl_data[k] = tbl_data[k] + [media_row["Mes_Ord"], cres_row["Mes_Ord"]]
        else:
            tbl_data[k] = tbl_data[k] + [media_row.get(k, 0.0), cres_row.get(k, 0.0)]

    for ano in anos_realizados:
        tbl_data[f"Var_{ano}_Disp"] = _build_var_disp_column(tbl_data[f"Var_{ano}"])
    tbl_data["Var_Ana_Disp"] = _build_var_disp_column(tbl_data["Var_Ana"])
    tbl_data["Var_Mer_Disp"] = _build_var_disp_column(tbl_data["Var_Mer"])
    tbl_data["Var_Ajs_Disp"] = _build_var_disp_column(tbl_data["Var_Ajs"])

    tbl_src = ColumnDataSource(tbl_data)

    CURRENCY_TMPL = "<%= (value==null || isNaN(value)) ? '—' : new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL',maximumFractionDigits:0}).format(value) %>"

    columns = [
        TableColumn(field="Mes", title="Mês", formatter=StringFormatter(text_color="#0b1320"), sortable=False)
    ]
    for ano in anos_realizados:
        columns.append(TableColumn(
            field=f"Rlzd_{ano}", title=f"RLZD {ano}",
            formatter=HTMLTemplateFormatter(template=CURRENCY_TMPL)
        ))
        columns.append(TableColumn(
            field=f"Var_{ano}_Disp", title=f"VAR. % {ano}",
            formatter=HTMLTemplateFormatter(template="<%= value %>")
        ))
    columns.extend([
        TableColumn(field="Analitica",     title="Analítica",         formatter=HTMLTemplateFormatter(template=CURRENCY_TMPL)),
        TableColumn(field="Var_Ana_Disp",  title="Var. % Analítica",  formatter=HTMLTemplateFormatter(template="<%= value %>")),
        TableColumn(field="Mercado",       title="Mercado",           formatter=HTMLTemplateFormatter(template=CURRENCY_TMPL)),
        TableColumn(field="Var_Mer_Disp",  title="Var. % Mercado",    formatter=HTMLTemplateFormatter(template="<%= value %>")),
        TableColumn(field="Ajustada",      title="Ajustada",          formatter=HTMLTemplateFormatter(template=CURRENCY_TMPL)),
        TableColumn(field="Var_Ajs_Disp",  title="Var. % Ajustada",   formatter=HTMLTemplateFormatter(template="<%= value %>")),
    ])

    tbl = DataTable(
        source=tbl_src,
        columns=columns,
        index_position=None,
        sizing_mode="stretch_width",
        width=1400,
        height=420,
        stylesheets=[make_stylesheet()],
    )

    # ==== CustomJS (corrigido: parênteses) ====
    cb = CustomJS(args=dict(src=src_ajs, tbl=tbl_src), code="""
        function recomputeAll() {
            const y = src.data['y']; if (!y) return;
            const norm = Array.from(y, v => (Number.isFinite(v) ? v : 0.0));
            tbl.data['Ajustada'] = norm;

            const varr = new Array(norm.length).fill(0.0);
            for (let i=1;i<norm.length;i++){
                const prev = norm[i-1];
                varr[i] = (prev===0 || !Number.isFinite(prev)) ? 0.0 : (norm[i]-prev)/Math.abs(prev);
            }
            tbl.data['Var_Ajs'] = varr;

            const n = norm.length;
            const mean = norm.reduce((a,b)=>a+b,0)/n;
            tbl.data['Ajustada'][12] = mean;
            tbl.data['Var_Ajs'][12]  = varr.reduce((a,b)=>a+b,0)/n;
            const delta = norm[n-1] - norm[0];
            tbl.data['Ajustada'][13] = delta;
            tbl.data['Var_Ajs'][13]  = (delta>0) ? 1.0 : ((delta<0) ? -1.0 : 0.0);

            function badgeHTML(v, rowIndex){
                if (!Number.isFinite(v)) return `<span class="uan-badge neu">—</span>`;
                let cls = (v>0) ? 'pos' : ((v<0) ? 'neg' : 'neu');
                let txt = (rowIndex===13) ? '' : ((v*100).toFixed(2) + '%');
                return `<span class="uan-badge ${cls}">${txt}</span>`;
            }
            const disp = new Array(tbl.data['Var_Ajs'].length);
            for (let i=0;i<disp.length;i++){ disp[i] = badgeHTML(tbl.data['Var_Ajs'][i], i); }
            tbl.data['Var_Ajs_Disp'] = disp;

            src.data['y_br'] = norm.map(v => Number.isFinite(v) ? v.toLocaleString('pt-BR') : '—');
            tbl.change.emit();
        }

        function recomputeIndex(idx) {
            const y = src.data['y']; if (!y) return;
            const n = y.length;
            const norm = Array.from(y, v => (Number.isFinite(v) ? v : 0.0));
            tbl.data['Ajustada'][idx] = norm[idx];

            function varAt(i) {
                if (i<=0) return 0.0;
                const prev = Number.isFinite(norm[i-1]) ? norm[i-1] : 0.0;
                if (prev===0) return 0.0;
                return (norm[i]-prev)/Math.abs(prev);
            }
            tbl.data['Var_Ajs'][idx] = varAt(idx);
            if (idx+1 < n) tbl.data['Var_Ajs'][idx+1] = varAt(idx+1);

            const mean = norm.reduce((a,b)=>a+b,0)/n;
            tbl.data['Ajustada'][12] = mean;
            const varMean = tbl.data['Var_Ajs'].slice(0,n).reduce((a,b)=>a+(Number.isFinite(b)?b:0),0)/n;
            tbl.data['Var_Ajs'][12]  = varMean;
            const delta = norm[n-1] - norm[0];
            tbl.data['Ajustada'][13] = delta;
            tbl.data['Var_Ajs'][13]  = (delta>0) ? 1.0 : ((delta<0) ? -1.0 : 0.0);

            function badgeHTML(v, rowIndex){
                if (!Number.isFinite(v)) return `<span class="uan-badge neu">—</span>`;
                let cls = (v>0) ? 'pos' : ((v<0) ? 'neg' : 'neu');
                let txt = (rowIndex===13) ? '' : ((v*100).toFixed(2) + '%');
                return `<span class="uan-badge ${cls}">${txt}</span>`;
            }
            const disp = new Array(tbl.data['Var_Ajs'].length);
            for (let i=0;i<disp.length;i++){ disp[i] = badgeHTML(tbl.data['Var_Ajs'][i], i); }
            tbl.data['Var_Ajs_Disp'] = disp;

            if (!src.data['y_br']) src.data['y_br'] = new Array(n).fill('—');
            src.data['y_br'][idx] = Number.isFinite(norm[idx]) ? norm[idx].toLocaleString('pt-BR') : '—';

            tbl.change.emit();
        }

        if (typeof cb_obj !== 'undefined' && cb_obj === src && cb_data && cb_data.patch) {
            const inds = new Set();
            const p = cb_data.patch;
            const patches = Array.isArray(p) ? p : [p];
            for (const one of patches) {
                if (one && (one.column === 'y' || one['column'] === 'y')) {
                    (one.indices || []).forEach(i => inds.add(i));
                }
            }
            if (inds.size > 0) {
                inds.forEach(i => recomputeIndex(i));
            } else {
                recomputeAll();
            }
        } else {
            recomputeAll();
        }
    """)

    src_ajs.js_on_change("patching", cb)
    src_ajs.js_on_change("data", cb)

    # -------------------- GRÁFICOS AUXILIARES -------------------------
    g1 = _grafico_visao_anual_linhas(
        _obter_realizados_por_ano(df_upload, cliente, categoria, produto, mascarar_zeros_finais=MASCARAR_ZEROS_FINAIS),
        analitica, mercado, ajustada, ano_proj, style_top, src_ajs_ref=src_ajs
    )
    g2 = _grafico_serie_historica(df_upload, cliente, categoria, produto,
                                  analitica, mercado, ano_proj, style_top)

    layout_topo = column(
        p,
        tbl,
        row(g1, g2, sizing_mode="stretch_width"),
        sizing_mode="stretch_width",
    )
    
    # Captura o retorno do streamlit_bokeh para persistir mudanças do drag-and-drop
    bokeh_result = streamlit_bokeh(
        layout_topo, 
        use_container_width=True, 
        key=f"simulador_layout_topo::{combo}"
    )
    
    # Se houver dados retornados do Bokeh (drag-and-drop), atualiza o session_state
    if bokeh_result is not None:
        try:
            # O retorno pode conter os dados atualizados do ColumnDataSource
            if isinstance(bokeh_result, dict):
                # Tenta extrair os valores y do source ajustada
                if 'y' in bokeh_result:
                    novos_valores = bokeh_result['y']
                    if isinstance(novos_valores, list) and len(novos_valores) >= 12:
                        st.session_state["ajustada"] = novos_valores[:12]
        except Exception:
            pass  # Ignora erros de parsing

    # -------------------- Seção: Análises por Categoria ----------------------
    st.markdown("<h2 class='uan-sec' style='margin:8px 0 4px 0;padding:4px 0;font-size:1.2rem;border-top:1px solid #e2e8f0;'>🗂️ Análises por Categoria</h2>", unsafe_allow_html=True)

    agreg = _agregados_por_categoria(df_upload, cliente, ano_proj or 0, mascarar_zeros_finais=MASCARAR_ZEROS_FINAIS)

    # Ajuste em tempo real da série "Ajustada" da CATEGORIA selecionada
    # Aplica a diferença do drag-and-drop na categoria atual
    ajustada_atual = st.session_state.get("ajustada", analitica[:])
    
    if agreg and categoria in agreg:
        serie_cat_ajs = np.array(agreg[categoria]["ajs"], dtype=float)
        serie_drag    = np.array(ajustada_atual, dtype=float)
        serie_prod_orig = _carregar_ajustada_produto(df_upload, cliente, categoria, produto, ano_proj) or analitica[:]
        serie_prod_orig = np.array(serie_prod_orig, dtype=float)
        if serie_drag.size == 12 and serie_prod_orig.size == 12 and serie_cat_ajs.size == 12:
            # Calcula a nova série ajustada da categoria = original + diferença do drag
            diff = serie_drag - serie_prod_orig
            agreg[categoria]["ajs"] = list(serie_cat_ajs + diff)

    # Gera hash dos valores ajustados para forçar re-render dos cards
    ajustada_hash = hash(tuple(st.session_state.get("ajustada", [0]*12)))

    if agreg:
        # Define ordem das categorias principais
        principais = ["CAPTAÇÕES", "OPERAÇÕES CRÉDITO", "SERVIÇOS", "CRÉDITO"]
        ordem = [c for c in principais if c in agreg] + [c for c in agreg.keys() if c not in principais]
        ordem = ordem[:3]  # Limita a 3 categorias

        # ===== LINHA 1: Cards das categorias =====
        cols_cards = st.columns(3, gap="small")
        for i, cat in enumerate(ordem):
            with cols_cards[i]:
                components.v1.html(
                    _cards_categoria_html(cat, agreg[cat]),
                    height=260,
                    scrolling=False
                )

        # ===== LINHA 2: Gráficos de barras =====
        cols_barras = st.columns(3, gap="small")
        for i, cat in enumerate(ordem):
            with cols_barras[i]:
                barras = _grafico_barras_categoria(cat, agreg[cat], make_stylesheet())
                streamlit_bokeh(barras, use_container_width=True, key=f"simulador_cat_bar::{combo}::{cat}::{ajustada_hash}")

        # ===== LINHA 3: Gráficos de pizza - Share por tipo de projeção =====
        st.markdown("<h4 style='margin:0.5rem 0 0.25rem 0;'>🍩 Share por Tipo de Projeção</h4>", unsafe_allow_html=True)
        cols_pizza = st.columns(3, gap="small")
        tipos_projecao = [("ana", "Proj. Analítica"), ("mer", "Proj. Mercado"), ("ajs", "Proj. Ajustada")]
        
        for i, (tipo, nome) in enumerate(tipos_projecao):
            with cols_pizza[i]:
                pizza = _grafico_pizza_share_por_projecao(tipo, agreg, make_stylesheet())
                streamlit_bokeh(pizza, use_container_width=True, key=f"simulador_pizza_{tipo}::{combo}::{ajustada_hash}")