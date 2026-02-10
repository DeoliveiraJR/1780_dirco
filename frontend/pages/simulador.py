# frontend/pages/simulador.py
import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource, PointDrawTool, DataTable, TableColumn,
    StringFormatter, CustomJS, HTMLTemplateFormatter,
    NumeralTickFormatter, HoverTool,
    Legend, LegendItem, NumberEditor, Div
)
from bokeh.layouts import column, row
from bokeh.transform import dodge
from streamlit_bokeh import streamlit_bokeh
from components.bokeh_editable import bokeh_editable, get_bokeh_updates, limpar_localStorage, salvar_localStorage

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

import streamlit.components.v1 as st_components

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_manager import (
    get_dados_upload, adicionar_simulacao, get_simulacoes_usuario,
    restaurar_simulacao, deletar_simulacao, get_simulacao_por_combo,
    resetar_simulacao_atual
)

MASCARAR_ZEROS_FINAIS = True


def _norm(s: str) -> str:
    import unicodedata
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.strip().lower()


def _recarregar_opcoes(df, cliente_escolhido):
    """Retorna (categorias, map_cat_prod, df_sub) com base no cliente."""
    dff = df.copy()
    if "CLI_N" not in dff.columns:
        if "TIPO_CLIENTE" in dff.columns:
            dff["CLI_N"] = dff["TIPO_CLIENTE"].astype(str).apply(_norm)
        elif "TP_CLIENTE" in dff.columns:
            dff["CLI_N"] = dff["TP_CLIENTE"].astype(str).apply(_norm)
        else:
            dff["CLI_N"] = ""

    if cliente_escolhido and cliente_escolhido != "Todos":
        dff = dff[dff["CLI_N"] == _norm(cliente_escolhido)]

    categorias = sorted(dff["CATEGORIA"].dropna().astype(str).unique())
    map_cat_prod = (
        dff.groupby("CATEGORIA")["PRODUTO"]
           .apply(lambda s: sorted(s.dropna().astype(str).unique().tolist()))
           .to_dict()
    )
    return categorias, map_cat_prod, dff


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

    # ==================== FILTROS NO TOPO DA PÁGINA ====================
    df_upload = get_dados_upload()
    
    if df_upload is None or df_upload.empty:
        st.warning("⚠️ Nenhum dado carregado. Vá em **Upload** e importe o Excel.")
        return

    # --- Carrega opções de clientes ---
    clientes_opcoes = ["Todos"]
    if isinstance(df_upload, pd.DataFrame) and not df_upload.empty:
        if "TIPO_CLIENTE" in df_upload.columns:
            clientes_opcoes += sorted([c for c in df_upload["TIPO_CLIENTE"].dropna().astype(str).unique() if c.strip() != ""])
        elif "TP_CLIENTE" in df_upload.columns:
            clientes_opcoes += sorted([c for c in df_upload["TP_CLIENTE"].dropna().astype(str).unique() if c.strip() != ""])

    # --- Layout filtros: 5 colunas (Nome | Cliente | Categoria | Produto | Botão) ---
    col_nome, col_cli, col_cat, col_prod, col_btn = st.columns([1.5, 1.2, 1.5, 1.5, 0.8])

    with col_nome:
        sim_nome_default = st.session_state.get("sim_nome", "Simulação 2026")
        sim_nome = st.text_input("📝 Nome da Simulação", value=sim_nome_default, key="sim_nome_page")

    with col_cli:
        cliente_mem = st.session_state.get("filtros", {}).get("cliente", "Todos")
        idx_cliente = clientes_opcoes.index(cliente_mem) if cliente_mem in clientes_opcoes else 0
        sim_cliente = st.selectbox("👤 Cliente", clientes_opcoes, index=idx_cliente, key="sim_cliente_page")

    # Recarrega categorias/produtos com base no cliente selecionado
    cats, map_cat_prod, df_subset = _recarregar_opcoes(df_upload, sim_cliente)

    with col_cat:
        categoria_mem = st.session_state.get("filtros", {}).get("categoria", "")
        idx_cat = cats.index(categoria_mem) if categoria_mem in cats else (0 if cats else None)
        sim_categoria = st.selectbox("📁 Categoria", cats, index=idx_cat, key="sim_categoria_page")

    with col_prod:
        prds = map_cat_prod.get(sim_categoria, [])
        produto_mem = st.session_state.get("filtros", {}).get("produto", "")
        idx_prd = prds.index(produto_mem) if produto_mem in prds else (0 if prds else None)
        sim_produto = st.selectbox("📦 Produto", prds, index=idx_prd, key="sim_produto_page")

    with col_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        salvar_clicked = st.button("💾 Salvar", type="primary", use_container_width=True)

    # --- Linha de simulações salvas (SEMPRE VISÍVEL) ---
    simulacoes_usuario = get_simulacoes_usuario()
    
    # Container para simulações salvas - sempre aparece
    with st.expander(f"📂 Simulações Salvas ({len(simulacoes_usuario)})", expanded=len(simulacoes_usuario) > 0):
        if not simulacoes_usuario:
            st.info("ℹ️ Nenhuma simulação salva ainda. Use o botão 💾 Salvar para guardar sua simulação.")
        else:
            cols_sim = st.columns([3, 2, 2, 1, 1])
            cols_sim[0].markdown("**Nome**")
            cols_sim[1].markdown("**Categoria**")
            cols_sim[2].markdown("**Produto**")
            cols_sim[3].markdown("**Ação**")
            cols_sim[4].markdown("**Excluir**")
            
            for sim in simulacoes_usuario:
                cols_sim = st.columns([3, 2, 2, 1, 1])
                cols_sim[0].write(sim.get("nome", "Sem nome"))
                cols_sim[1].write(sim.get("categoria", "-")[:20])
                cols_sim[2].write(sim.get("produto", "-")[:20])
                if cols_sim[3].button("🔄", key=f"rest_{sim.get('id')}", help="Restaurar"):
                    restaurar_simulacao(sim.get("id"))
                    st.rerun()
                if cols_sim[4].button("🗑️", key=f"del_{sim.get('id')}", help="Excluir"):
                    deletar_simulacao(sim.get("id"))
                    st.rerun()

    # Atualiza session_state com os filtros selecionados APENAS se mudou
    novo_filtro = {
        "cliente": sim_cliente,
        "categoria": sim_categoria if sim_categoria else "",
        "produto": sim_produto if sim_produto else "",
        "nome": sim_nome
    }
    if st.session_state.get("filtros") != novo_filtro:
        st.session_state["filtros"] = novo_filtro

    # Ação do botão salvar
    if salvar_clicked:
        ajustada_para_salvar = st.session_state.get("ajustada", [0.0]*12)
        sim_salva = adicionar_simulacao(
            nome=st.session_state["filtros"].get("nome", "Simulação"),
            categoria=st.session_state["filtros"].get("categoria", ""),
            produto=st.session_state["filtros"].get("produto", ""),
            taxa_crescimento=st.session_state.get("sim_incremento_perc", 0),
            volatilidade=st.session_state.get("sim_rotacionar_curva", 1.0),
            cenarios={
                "Ajustada": True, 
                "Cliente": st.session_state["filtros"].get("cliente", "Todos"),
                "ajuste_mensal": st.session_state.get("sim_ajuste_mensal_final", 0),
                "inclinacao": st.session_state.get("sim_inclinacao", 0),
            },
            dados_grafico={"Ajustada": ajustada_para_salvar},
        )
        st.toast(f"✅ Simulação '{sim_salva.get('nome', '')}' salva com sucesso!", icon="💾")
        st.success(f"✅ Simulação salva! ID: {sim_salva.get('id', '')[:20]}...")
        st.rerun()  # Força rerun para atualizar a lista de simulações

    st.markdown("---")

    # ==================== LÓGICA DO SIMULADOR ====================
    filtros = st.session_state.get("filtros", {}) or {}

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
    
    # ==================== ESTADOS PARA AS 3 CURVAS ====================
    # Reinicia estados quando combo muda
    combo_mudou = st.session_state.get("last_combo") != combo
    if combo_mudou:
        # Limpa localStorage do combo anterior para evitar conflitos
        old_combo = st.session_state.get("last_combo")
        if old_combo:
            limpar_localStorage(key=f"sim_bokeh_{old_combo}")
        
        st.session_state["curva_analitica"] = analitica[:]
        st.session_state["curva_mercado"] = mercado[:]
        st.session_state["ajustada"] = analitica[:]  # Ajustada inicia igual à analítica
        st.session_state["last_combo"] = combo
        st.session_state["sync_counter"] = 0
        print(f"[DEBUG] COMBO MUDOU! Resetando curvas para: {combo}")
    
    # Verifica se precisa limpar localStorage (flag de reset)
    if st.session_state.get("_limpar_localStorage"):
        limpar_localStorage(key=f"sim_bokeh_{combo}")
        st.session_state["_limpar_localStorage"] = False
    
    # Inicializa contador se não existir
    if "sync_counter" not in st.session_state:
        st.session_state["sync_counter"] = 0
    
    sync_counter = st.session_state.get("sync_counter", 0)
    
    # ==================== LEITURA DO LOCALSTORAGE (ANTES DE RENDERIZAR) ====================
    # Lê valores do localStorage ANTES de criar os sources do Bokeh
    # Isso garante que o gráfico é renderizado com os valores editados pelo usuário
    # NÃO lê se o combo acabou de mudar (para começar com curva analítica)
    valores_localStorage = None
    if not combo_mudou:
        valores_localStorage = get_bokeh_updates(key=f"sim_bokeh_{combo}", sync_counter=sync_counter)
    
    if valores_localStorage is not None and len(valores_localStorage) == 12:
        valores_atuais = [round(v, 2) for v in st.session_state.get("ajustada", [])]
        valores_novos = [round(v, 2) for v in valores_localStorage]
        
        if valores_novos != valores_atuais:
            st.session_state["ajustada"] = valores_localStorage
            print(f"[DEBUG] localStorage → session_state: {valores_localStorage[:3]}...")
    
    # Carrega os valores dos estados (FONTE DE VERDADE - agora já atualizada pelo localStorage)
    curva_analitica_state = st.session_state.get("curva_analitica", analitica[:])
    curva_mercado_state = st.session_state.get("curva_mercado", mercado[:])
    ajustada = st.session_state.get("ajustada", analitica[:])

    # ==================== PAINEL DE AJUSTE MANUAL POR MÊS ====================
    # Permite incrementar/decrementar valores da curva ajustada por mês
    # O valor do incremento será futuramente vinculado aos parâmetros da sidebar
    with st.expander("⚙️ Ajuste Manual por Mês", expanded=False):
        st.caption("O valor em tempo real aparece na barra azul acima do gráfico")
        incremento_base = st.session_state.get("sim_incremento_valor", 1_000_000_000)
        
        col_mes, col_inc, col_btn_menos, col_btn_mais = st.columns([2, 2, 1, 1])
        
        with col_mes:
            mes_selecionado = st.selectbox(
                "Mês",
                options=list(range(12)),
                format_func=lambda i: MESES_ABR_LIST[i],
                key=f"ajuste_mes_{combo}",
                label_visibility="collapsed"
            )
        
        with col_inc:
            incremento = st.number_input(
                "Incremento",
                value=incremento_base,
                step=100_000_000,
                format="%d",
                key=f"ajuste_inc_{combo}",
                label_visibility="collapsed"
            )
            st.session_state["sim_incremento_valor"] = incremento
        
        with col_btn_menos:
            if st.button("➖", key=f"btn_menos_{combo}", help="Reduzir valor", use_container_width=True):
                novo_valor = ajustada[mes_selecionado] - incremento
                ajustada[mes_selecionado] = max(0, novo_valor)
                st.session_state["ajustada"] = ajustada[:]
                salvar_localStorage(key=f"sim_bokeh_{combo}", valores=ajustada[:])
                st.toast(f"📉 {MESES_ABR_LIST[mes_selecionado]}: -R$ {fmt_br(incremento, 0)}")
                st.rerun()
        
        with col_btn_mais:
            if st.button("➕", key=f"btn_mais_{combo}", help="Aumentar valor", use_container_width=True):
                ajustada[mes_selecionado] = ajustada[mes_selecionado] + incremento
                st.session_state["ajustada"] = ajustada[:]
                salvar_localStorage(key=f"sim_bokeh_{combo}", valores=ajustada[:])
                st.toast(f"📈 {MESES_ABR_LIST[mes_selecionado]}: +R$ {fmt_br(incremento, 0)}")
                st.rerun()

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

    # -------------------- DIV DE VALORES EM TEMPO REAL -----------------------
    # Exibe os valores da curva ajustada, atualizando em tempo real via JS
    valores_html_inicial = " | ".join([
        f"<b>{MESES_ABR_LIST[i]}:</b> R$ {fmt_br(ajustada[i], 0)}" 
        for i in range(12)
    ])
    div_valores = Div(
        text=f"<div style='font-size:12px; padding:8px; background:#f0f8ff; border-radius:4px; margin-bottom:8px;'>"
             f"<b>📊 Curva Ajustada:</b> {valores_html_inicial}</div>",
        sizing_mode="stretch_width"
    )
    
    # Callback JS para atualizar o Div quando os dados mudam
    cb_atualiza_div = CustomJS(args=dict(src=src_ajs, div=div_valores, meses=MESES_ABR_LIST), code="""
        const y = src.data['y'];
        if (!y || y.length < 12) return;
        
        function formatBR(v) {
            return v.toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 0});
        }
        
        let html = "<div style='font-size:12px; padding:8px; background:#f0f8ff; border-radius:4px; margin-bottom:8px;'>";
        html += "<b>📊 Curva Ajustada:</b> ";
        const parts = [];
        for (let i = 0; i < 12; i++) {
            parts.push("<b>" + meses[i] + ":</b> R$ " + formatBR(y[i]));
        }
        html += parts.join(" | ");
        html += "</div>";
        div.text = html;
    """)
    src_ajs.js_on_change("data", cb_atualiza_div)

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
    
    # Template destacado para coluna Ajustada (editável via clique duplo)
    AJUSTADA_TMPL = '<span style="color:#1a5f7a;font-weight:600;cursor:pointer;" title="Clique duplo para editar"><%= (value==null || isNaN(value)) ? "—" : new Intl.NumberFormat("pt-BR",{style:"currency",currency:"BRL",maximumFractionDigits:0}).format(value) %></span>'

    # Editor para coluna Ajustada (step de 1 bilhão)
    ajustada_editor = NumberEditor(step=1_000_000_000)

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
        TableColumn(field="Ajustada",      title="Ajustada",          formatter=HTMLTemplateFormatter(template=AJUSTADA_TMPL), editor=ajustada_editor),
        TableColumn(field="Var_Ajs_Disp",  title="Var. % Ajustada",   formatter=HTMLTemplateFormatter(template="<%= value %>")),
    ])

    tbl = DataTable(
        source=tbl_src,
        columns=columns,
        index_position=None,
        sizing_mode="stretch_width",
        width=1400,
        height=420,
        editable=True,  # Habilita edição na tabela
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

    # ==== Callback reverso: Tabela -> Gráfico ====
    # Quando o usuário edita a coluna Ajustada na tabela, atualiza o gráfico
    cb_tbl_to_graph = CustomJS(args=dict(src=src_ajs, tbl=tbl_src), code="""
        // Pega os 12 primeiros valores de Ajustada (meses)
        const ajustada = tbl.data['Ajustada'];
        if (!ajustada || ajustada.length < 12) return;
        
        const newY = ajustada.slice(0, 12).map(v => Number.isFinite(v) ? v : 0);
        
        // Atualiza o gráfico apenas se houve mudança real
        const currentY = src.data['y'];
        let changed = false;
        for (let i = 0; i < 12; i++) {
            if (Math.abs(newY[i] - currentY[i]) > 0.01) {
                changed = true;
                break;
            }
        }
        
        if (changed) {
            src.data['y'] = newY;
            src.data['y_br'] = newY.map(v => v.toLocaleString('pt-BR'));
            src.change.emit();
            console.log('[TBL->GRAPH] Gráfico atualizado:', newY.slice(0,3));
        }
    """)
    tbl_src.js_on_change("data", cb_tbl_to_graph)
    tbl_src.js_on_change("patching", cb_tbl_to_graph)  # Edições de células

    # -------------------- GRÁFICOS AUXILIARES -------------------------
    g1 = _grafico_visao_anual_linhas(
        _obter_realizados_por_ano(df_upload, cliente, categoria, produto, mascarar_zeros_finais=MASCARAR_ZEROS_FINAIS),
        analitica, mercado, ajustada, ano_proj, style_top, src_ajs_ref=src_ajs
    )
    g2 = _grafico_serie_historica(df_upload, cliente, categoria, produto,
                                  analitica, mercado, ano_proj, style_top)

    layout_topo = column(
        div_valores,
        p,
        tbl,
        row(g1, g2, sizing_mode="stretch_width"),
        sizing_mode="stretch_width",
    )
    
    # Renderiza o gráfico Bokeh (drag-and-drop salva valores no localStorage)
    bokeh_editable(
        layout_topo, 
        height=1200,
        key=f"sim_bokeh_{combo}"
    )
    
    st.markdown("---")
    
    # ==================== BOTÃO DE SINCRONIZAÇÃO ====================
    # Fluxo:
    # 1. Usuário arrasta ponto → JS salva no localStorage (em tempo real)
    # 2. Usuário clica "Sincronizar" → incrementa contador → rerun
    # 3. No rerun, leitura do localStorage acontece NO INÍCIO (antes de renderizar)
    # 4. Gráfico e cards são renderizados com valores atualizados
    
    # Atualiza referência local (já foi atualizada no início, mas garantimos aqui também)
    ajustada = st.session_state.get("ajustada", analitica[:])
    sync_counter = st.session_state.get("sync_counter", 0)
    
    # Botões de Sincronizar e Resetar
    col_sync1, col_sync2, col_reset, col_sync3 = st.columns([1.5, 1, 1, 1.5])
    with col_sync2:
        if st.button(
            "🔄 Sincronizar Curva", 
            key=f"sync_{combo}",
            help="Aplicar alterações do drag-and-drop aos cards",
            use_container_width=True
        ):
            st.session_state["sync_counter"] = sync_counter + 1
            st.toast("🔄 Sincronizando...", icon="📈")
            st.rerun()
    
    with col_reset:
        if st.button(
            "↩️ Resetar Curva",
            key=f"reset_{combo}",
            help="Voltar curva ajustada para a analítica original",
            use_container_width=True
        ):
            resetar_simulacao_atual()
            limpar_localStorage(key=f"sim_bokeh_{combo}")
            st.toast("↩️ Curva resetada!", icon="🔄")
            st.rerun()
    
    # -------------------- Seção: Análises por Categoria ----------------------
    st.markdown("<h2 class='uan-sec' style='margin:8px 0 4px 0;padding:4px 0;font-size:1.2rem;border-top:1px solid #e2e8f0;'>🗂️ Análises por Categoria</h2>", unsafe_allow_html=True)
    
    # Carrega dados agregados por categoria
    agreg = _agregados_por_categoria(df_upload, cliente, ano_proj or 0, mascarar_zeros_finais=MASCARAR_ZEROS_FINAIS)
    
    # Função auxiliar para garantir arrays de 12 elementos
    def _safe_array_12(arr):
        if arr is None:
            return [0.0] * 12
        arr = list(arr)
        # Converte NaN para 0
        arr = [0.0 if (v is None or (isinstance(v, float) and np.isnan(v))) else float(v) for v in arr]
        if len(arr) < 12:
            arr = arr + [0.0] * (12 - len(arr))
        return arr[:12]
    
    # ==== APLICA AJUSTES DO DRAG-AND-DROP À CATEGORIA ATUAL ====
    if agreg and categoria in agreg:
        serie_prod_orig = _carregar_ajustada_produto(df_upload, cliente, categoria, produto, ano_proj) or analitica[:]
        serie_prod_orig = np.array(_safe_array_12(serie_prod_orig), dtype=float)
        serie_drag = np.array(_safe_array_12(ajustada), dtype=float)
        
        diff = serie_drag - serie_prod_orig
        serie_cat_ajs = np.array(_safe_array_12(agreg[categoria].get("ajs", [])), dtype=float)
        agreg[categoria]["ajs"] = list(serie_cat_ajs + diff)
    
    if agreg:
        principais = ["CAPTAÇÕES", "OPERAÇÕES CRÉDITO", "SERVIÇOS", "CRÉDITO"]
        ordem = [c for c in principais if c in agreg] + [c for c in agreg.keys() if c not in principais]
        ordem = ordem[:3]

        # ===== LINHA 1: Cards das categorias =====
        cols_cards = st.columns(3, gap="small")
        for i, cat in enumerate(ordem):
            with cols_cards[i]:
                card_html = _cards_categoria_html(cat, agreg[cat])
                st_components.html(card_html, height=260, scrolling=False)

        # ===== LINHA 2: Gráficos de barras =====
        cols_barras = st.columns(3, gap="small")
        for i, cat in enumerate(ordem):
            with cols_barras[i]:
                barras = _grafico_barras_categoria(cat, agreg[cat], make_stylesheet())
                streamlit_bokeh(barras, use_container_width=True, key=f"bar_{cat}_{combo}")

        # ===== LINHA 3: Gráficos de pizza =====
        st.markdown("<h4 style='margin:0.5rem 0 0.25rem 0;'>🍩 Share por Tipo de Projeção</h4>", unsafe_allow_html=True)
        cols_pizza = st.columns(3, gap="small")
        tipos_projecao = [("ana", "Proj. Analítica"), ("mer", "Proj. Mercado"), ("ajs", "Proj. Ajustada")]
        
        for i, (tipo, nome) in enumerate(tipos_projecao):
            with cols_pizza[i]:
                pizza = _grafico_pizza_share_por_projecao(tipo, agreg, make_stylesheet())
                streamlit_bokeh(pizza, use_container_width=True, key=f"pizza_{tipo}_{combo}")