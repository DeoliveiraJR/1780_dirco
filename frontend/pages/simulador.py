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
    Legend, LegendItem, NumberEditor, Div, FullscreenTool
)
from bokeh.layouts import column, row
from bokeh.transform import dodge
from streamlit_bokeh import streamlit_bokeh
from components.bokeh_editable import (
    bokeh_editable, get_bokeh_update_packet, limpar_localStorage
)

from utils_ext.css import make_stylesheet
from utils_ext.formatters import fmt_br
from utils_ext.series import (
    _norm_txt, _mes_to_num, _variacao_mensal, _ensure_cli_n, _mask_trailing_zeros
)
from utils_ext.icons import render_page_header
from utils_ext.constants import (
    MESES_FULL, MESES_NUM, MESES_ABR, MESES_ABR_LIST,
    COR_ANALITICA, COR_MERCADO, COR_AJUSTADA, COR_RLZD_BASE,
    COR_MERCADO_L, COR_ANALITICA_L, CAT_COLORS
)
from utils_ext.display import _badge_html_from_value, _build_var_disp_column

from services.aggregations import (
    _carregar_curvas_base, _obter_realizados_por_ano, _agregados_por_categoria,
    _carregar_ajustada_produto, _carregar_proximos_12_meses,
    _aplicar_filtros_dimensao,
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
    resetar_simulacao_atual, carregar_curva_ajustada, existe_curva_salva,
    aplicar_todas_curvas_salvas, get_score_by_produto_nome
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
    # ==================== VALIDAÇÃO DE DADOS ====================
    df_upload = get_dados_upload()
    
    # Aplica todas as curvas salvas ao DataFrame (garante persistência)
    if df_upload is not None and not df_upload.empty:
        if not st.session_state.get("_curvas_aplicadas_sessao"):
            aplicar_todas_curvas_salvas()
            st.session_state["_curvas_aplicadas_sessao"] = True
    
    if df_upload is None or df_upload.empty:
        st.warning("⚠️ Nenhum dado carregado. Vá em **Upload** e importe o Excel.")
        return
    
    # Validar colunas essenciais para simulador
    colunas_requeridas = ["PROJETADO_ANALITICO", "PROJETADO_MERCADO", "CATEGORIA", "PRODUTO"]
    colunas_faltantes = [c for c in colunas_requeridas if c not in df_upload.columns]
    
    if colunas_faltantes:
        st.error(f"""
        ❌ **Dados Incompletos para Simulador**
        
        As seguintes colunas esperadas não foram encontradas: {', '.join(colunas_faltantes)}
        
        Por favor, verifique o upload de dados e tente novamente.
        """)
        return

    # ==================== SINCRONIZAÇÃO COM FILTROS DA SIDEBAR ====================
    # Os filtros agora estão na sidebar, vamos sincronizar com a lógica do simulador
    filtros = st.session_state.get("filtros", {})
    sim_cd_tip_agpd = filtros.get("cd_tip_agpd", "Todos")
    sim_tip_td = filtros.get("tip_td", "Todos")
    sim_cliente = filtros.get("cliente", "Todos")
    sim_categoria = filtros.get("categoria", "")
    sim_produto = filtros.get("produto", "")
    produto_todos_selecionado = sim_produto == "TODOS"
    
    # Valida se produto é "TODOS" e ajusta para vazio (usar todos os produtos)
    if produto_todos_selecionado:
        sim_produto = ""
    
    cliente_label = sim_cliente if sim_cliente else "Todos"
    categoria_label = sim_categoria if sim_categoria else "Selecione uma categoria"
    if produto_todos_selecionado:
        produto_label = "TODOS"
    else:
        produto_label = sim_produto if sim_produto else "Selecione um produto"

    # ==================== HEADER ELEGANTE COM FILTROS ====================
    render_page_header(
        "Simulador de Projeções",
        "fa-wand-magic-sparkles",
        "Projete cenários e simule variações nos componentes de resultado com flexibilidade",
        filters={
            'cliente': cliente_label,
            'categoria': categoria_label,
            'produto': produto_label
        }
    )
    
    # ==================== LÓGICA DO SIMULADOR ====================
    # Usa filtros da sidebar sincronizados em st.session_state["filtros"]
    cliente  = sim_cliente
    categoria= sim_categoria
    produto  = sim_produto if sim_produto else ""  # Se vazio ou "TODOS", usa vazio

    dff_check = _ensure_cli_n(df_upload)
    base_f = dff_check if cliente=="Todos" else dff_check[dff_check["CLI_N"] == _norm_txt(cliente)]
    base_f = _aplicar_filtros_dimensao(base_f, cd_tip_agpd=sim_cd_tip_agpd, tip_td=sim_tip_td)
    if not categoria and not base_f.empty:
        categoria = str(base_f["CATEGORIA"].dropna().astype(str).unique()[0])
    base_fc = base_f[base_f["CATEGORIA"].astype(str) == str(categoria)]
    if not produto_todos_selecionado and not produto and not base_fc.empty:
        produto = str(base_fc["PRODUTO"].dropna().astype(str).unique()[0])

    analitica, mercado, ano_proj = _carregar_curvas_base(
        df_upload,
        cliente,
        categoria,
        produto,
        cd_tip_agpd=sim_cd_tip_agpd,
        tip_td=sim_tip_td,
    )
    combo = f"{cliente}::{categoria}::{produto}::{sim_cd_tip_agpd}::{sim_tip_td}"
    
    # ==================== ATUALIZA PARÂMETROS NA SIDEBAR ====================
    st.session_state["sim_qtd_meses"] = 12
    primeiro_pjtd = analitica[0] if analitica and len(analitica) > 0 else 0
    st.session_state["sim_primeiro_pjtd"] = primeiro_pjtd
    ultimo_pjtd = analitica[11] if analitica and len(analitica) > 11 else 0
    st.session_state["sim_ultimo_pjtd"] = ultimo_pjtd
    qtd_meses = 12
    if qtd_meses > 1:
        inclinacao = (ultimo_pjtd - primeiro_pjtd) / (qtd_meses - 1)
    else:
        inclinacao = 0
    st.session_state["sim_inclinacao"] = inclinacao
    
    # ==================== ESTADOS PARA AS 3 CURVAS ====================
    # IMPORTANTE: Aplicar pending_sync ANTES de checar combo_mudou
    # para que edições sincronizadas não sejam perdidas no reset do combo
    pending_sync_pre = st.session_state.pop("_pending_sync_ajustada12", None)
    print(f"[DEBUG] Salvou pending_sync_pre: {pending_sync_pre is not None}")
    
    combo_mudou = st.session_state.get("last_combo") != combo
    print(f"[DEBUG] combo_mudou={combo_mudou}, last_combo={st.session_state.get('last_combo')}, combo={combo}")
    
    if combo_mudou:
        old_combo = st.session_state.get("last_combo")
        if old_combo:
            limpar_localStorage(key=f"sim_bokeh_{old_combo}")
        
        st.session_state["curva_analitica"] = analitica[:]
        st.session_state["curva_mercado"] = mercado[:]
        
        curva_salva = carregar_curva_ajustada(
            cliente,
            categoria,
            produto,
            cd_tip_agpd=sim_cd_tip_agpd,
            tip_td=sim_tip_td,
        )
        if curva_salva is not None:
            st.session_state["ajustada"] = curva_salva[:]
            print(f"[PERSIST] Curva carregada do banco: {combo}")
            st.toast(f"📂 Carregada simulação salva para {produto}", icon="✅")
        else:
            st.session_state["ajustada"] = analitica[:]
            print(f"[DEBUG] COMBO MUDOU! Usando curva analítica: {combo}")
        
        st.session_state["last_combo"] = combo
        st.session_state["sync_counter"] = 0
        st.session_state["sync_fetch_retry"] = 0
        st.session_state["_last_auto_bokeh_vals"] = None
    
    # Verifica se precisa limpar localStorage (flag de reset)
    if st.session_state.get("_limpar_localStorage"):
        limpar_localStorage(key=f"sim_bokeh_{combo}")
        st.session_state["_limpar_localStorage"] = False
    
    # Inicializa contadores se não existir
    if "sync_counter" not in st.session_state:
        st.session_state["sync_counter"] = 0
    if "sync_fetch_retry" not in st.session_state:
        st.session_state["sync_fetch_retry"] = 0
    if "_last_auto_bokeh_vals" not in st.session_state:
        st.session_state["_last_auto_bokeh_vals"] = None
    if "_last_bokeh_sync_ts" not in st.session_state:
        st.session_state["_last_bokeh_sync_ts"] = {}

    sync_counter = st.session_state.get("sync_counter", 0)

    print(f"[DEBUG] Ciclo de render: combo={combo}, combo_mudou={combo_mudou}")

    # ==================== LEITURA DO LOCALSTORAGE (sempre no combo atual) ====================
    # O Enter já provoca rerender neste fluxo. Então lemos o browser em todo render do combo
    # para aplicar a edição sem depender de clique no botão Sincronizar.
    MAX_SYNC_RENDERS = 4
    if not combo_mudou:
        packet_localStorage = get_bokeh_update_packet(
            key=f"sim_bokeh_{combo}",
            sync_counter=sync_counter,
        )
        if packet_localStorage:
            valores_localStorage = packet_localStorage.get("values")
            ts_localStorage = int(packet_localStorage.get("timestamp") or 0)
            probe_localStorage = packet_localStorage.get("probe") if isinstance(packet_localStorage.get("probe"), dict) else None
            sync_probe_localStorage = packet_localStorage.get("sync_probe") if isinstance(packet_localStorage.get("sync_probe"), dict) else None
            last_ts_map = st.session_state.get("_last_bokeh_sync_ts", {})
            last_ts_combo = int(last_ts_map.get(combo, 0))
            last_vals = st.session_state.get("_last_auto_bokeh_vals")

            try:
                if isinstance(valores_localStorage, list) and len(valores_localStorage) == 12:
                    print(
                        f"[SYNC-TRACE] combo={combo} ts={ts_localStorage} last_ts={last_ts_combo} "
                        f"vals_head={[round(float(v), 2) for v in valores_localStorage[:3]]} "
                        f"vals_jul_idx6={round(float(valores_localStorage[6]), 2)} "
                        f"probe={probe_localStorage} sync_probe={sync_probe_localStorage}"
                    )
                else:
                    print(
                        f"[SYNC-TRACE] combo={combo} ts={ts_localStorage} last_ts={last_ts_combo} "
                        f"sem_vals probe={probe_localStorage} sync_probe={sync_probe_localStorage}"
                    )
            except Exception:
                pass

            is_new_revision = ts_localStorage > last_ts_combo
            same_as_last = (
                isinstance(last_vals, list)
                and len(last_vals) == 12
                and isinstance(valores_localStorage, list)
                and len(valores_localStorage) == 12
                and all(abs(float(a) - float(b)) <= 1e-9 for a, b in zip(last_vals, valores_localStorage))
            )

            # Aceita revisão por timestamp NOVO ou por diferença real de valores.
            # Isso evita perda de edição quando houver colisão de timestamp ou atraso de atualização do ts.
            if isinstance(valores_localStorage, list) and len(valores_localStorage) == 12 and (is_new_revision or not same_as_last):
                st.session_state["_pending_sync_ajustada12"] = [float(v) for v in valores_localStorage]
                st.session_state["_last_auto_bokeh_vals"] = [float(v) for v in valores_localStorage]
                if ts_localStorage > 0:
                    last_ts_map[combo] = ts_localStorage
                    st.session_state["_last_bokeh_sync_ts"] = last_ts_map
                print(f"[SYNC] ✓ localStorage novo (ts={ts_localStorage}): {[f'{v:.0f}' for v in valores_localStorage[:3]]}...")
            elif isinstance(valores_localStorage, list) and len(valores_localStorage) == 12:
                print(f"[SYNC] • localStorage ignorado (stale ts={ts_localStorage}, last_ts={last_ts_combo})")
        else:
            print(f"[SYNC-TRACE] combo={combo} sem_packet_localStorage")

        # Mantém o mecanismo de retry somente quando o usuário dispara ciclo manual.
        if sync_counter > 0:
            sync_fetch_retry = int(st.session_state.get("sync_fetch_retry", 0)) + 1
            st.session_state["sync_fetch_retry"] = sync_fetch_retry

            tem_pending_sync = isinstance(st.session_state.get("_pending_sync_ajustada12"), list)
            if tem_pending_sync:
                print(f"[SYNC] pending_sync já disponível no render {sync_fetch_retry}")
                st.session_state["sync_counter"] = 0
                st.session_state["sync_fetch_retry"] = 0
            elif sync_fetch_retry < MAX_SYNC_RENDERS:
                print(f"[SYNC] retry {sync_fetch_retry}/{MAX_SYNC_RENDERS} aguardando leitura do browser")
                st.session_state["sync_counter"] = sync_counter or 1
                st.rerun()
            else:
                print(f"[SYNC] esgotou retries ({MAX_SYNC_RENDERS}) sem obter valores")
                st.session_state["sync_counter"] = 0
                st.session_state["sync_fetch_retry"] = 0
        else:
            st.session_state["sync_fetch_retry"] = 0
    else:
        print(f"[SYNC-TRACE] polling inativo (combo_mudou={combo_mudou})")
        st.session_state["sync_counter"] = 0
        st.session_state["sync_fetch_retry"] = 0
    
    # Carrega os valores dos estados (FONTE DE VERDADE) - SERÁ REDEFINIDO DEPOIS COM OS DADOS CORRETOS
    
    realizados_dict = _obter_realizados_por_ano(
        df_upload,
        cliente,
        categoria,
        produto,
        mascarar_zeros_finais=MASCARAR_ZEROS_FINAIS,
        cd_tip_agpd=sim_cd_tip_agpd,
        tip_td=sim_tip_td,
    )
    anos_realizados = sorted(realizados_dict.keys())
    variacoes_rlzd = {ano: _variacao_mensal(realizados_dict[ano]) for ano in anos_realizados}

    # ==================== OBTER MÊS/ANO ATUAL ====================
    from datetime import datetime
    agora = datetime.now()
    mes_atual = agora.month  # 1-12
    ano_atual = agora.year   # 2026 em fevereiro de 2026
    
    # O próximo ano para projeção (2027 se estamos em 2026)
    ano_projecao_proxima = ano_atual + 1
    
    # Se 2027 (ou o próximo ano) ainda não está em realizados_dict, adicionar como lista vazia
    if ano_projecao_proxima not in realizados_dict:
        # Será substituído pelos dados de projeção (analítica) para meses futuros
        # e por dados de realizado quando o mês passar
        realizados_dict[ano_projecao_proxima] = [0.0] * 12
        anos_realizados = sorted(realizados_dict.keys())
        variacoes_rlzd = {ano: _variacao_mensal(realizados_dict[ano]) for ano in anos_realizados}

    style_top = make_stylesheet()

    # ==================== CARREGAR DADOS DOS PRÓXIMOS 12 MESES ====================
    # Carrega curvas para ambos os anos (ano_atual e ano_projecao_proxima)
    # Isso garante que se estivermos em mar/26, mostramos até mar/27 com dados corretos
    from services.aggregations import _carregar_curvas_por_ano
    ana_ano_atual, mer_ano_atual, ajs_ano_atual = _carregar_curvas_por_ano(
        df_upload,
        cliente,
        categoria,
        produto,
        ano_atual,
        cd_tip_agpd=sim_cd_tip_agpd,
        tip_td=sim_tip_td,
    )
    
    # Carrega dados de 2027
    ana_ano_proximo_temp, mer_ano_proximo_temp, ajs_ano_proximo_temp = _carregar_curvas_por_ano(
        df_upload,
        cliente,
        categoria,
        produto,
        ano_projecao_proxima,
        cd_tip_agpd=sim_cd_tip_agpd,
        tip_td=sim_tip_td,
    )
    
    # Sempre usar dados de ano_proximo, mesmo que sejam zeros
    # O usuário pode ajustar depois no painel
    ana_ano_proximo = ana_ano_proximo_temp
    mer_ano_proximo = mer_ano_proximo_temp
    ajs_ano_proximo = ajs_ano_proximo_temp

    # ==================== CÁLCULO DOS PRÓXIMOS 12 MESES (PARA GRÁFICO) ====================
    # SEMPRE mostra 12 meses (Mar/26 até Fev/27)
    # Dados de 2027 podem ser zeros, mas são sempre inclusos
    
    meses_rotulos = []
    analitica_grafico = []
    mercado_grafico = []
    ajustada_grafico = []
    
    # SEMPRE 12 meses completos
    num_meses = 12
    
    for i in range(num_meses):
        # Mês absoluto considerando o ano atual
        mes_abs = (mes_atual - 1 + i)  # 0-23 (pode ultrapassar 11)
        
        # Determina em qual ano este mês está
        if mes_abs < 12:
            ano_mes = ano_atual
            mes_idx = mes_abs  # índice 0-11 no ano atual
            ana_val = ana_ano_atual[mes_idx]
            mer_val = mer_ano_atual[mes_idx]
            ajs_val = ajs_ano_atual[mes_idx]
        else:
            # Sempre há ano_proximo agora (pode ter zeros, mas existe)
            ano_mes = ano_projecao_proxima
            mes_idx = mes_abs - 12  # índice 0-11 no próximo ano
            ana_val = ana_ano_proximo[mes_idx]
            mer_val = mer_ano_proximo[mes_idx]
            ajs_val = ajs_ano_proximo[mes_idx]
        
        # Determinando o número do mês (1-12) para este período
        mes_num = (mes_abs % 12) + 1
        
        # Construindo rótulo com ano (ex: Mar/26, Jan/27)
        rotulo = f"{MESES_ABR_LIST[mes_num - 1]}/{str(ano_mes)[-2:]}"
        
        meses_rotulos.append(rotulo)
        analitica_grafico.append(ana_val)
        mercado_grafico.append(mer_val)
        ajustada_grafico.append(ajs_val)
    
    # Completa com zeros para manter sempre 12 elementos (para compatibilidade com o painel de ajuste)
    while len(meses_rotulos) < 12:
        meses_rotulos.append("")
        analitica_grafico.append(0.0)
        mercado_grafico.append(0.0)
        ajustada_grafico.append(0.0)
    
    # IMPORTANTE: meses_numeros SEMPRE sequencial [1,2,3,...,12] para o gráfico
    # Os rótulos já estão em ordem correspondente aos índices dos dados (0-11)
    meses_numeros = list(range(1, 13))
    
    # ==================== DADOS PARA A TABELA ====================
    # SEMPRE expandir para 24 meses (Jan-Dez 2026 + Jan-Dez 2027)
    # Mesmo que 2027 tenha dados zerados, o usuário pode ajustar depois
    
    # DEBUG: Verificar tamanhos dos arrays de entrada
    # st.write(f"[DEBUG] ana_ano_atual: {len(ana_ano_atual)} elementos, ana_ano_proximo: {len(ana_ano_proximo)} elementos")
    # st.write(f"[DEBUG] mes_atual: {mes_atual}, ano_atual: {ano_atual}, ano_projecao_proxima: {ano_projecao_proxima}")
    
    analitica = ana_ano_atual[:] + ana_ano_proximo[:]  # 12 + 12 = 24
    mercado = mer_ano_atual[:] + mer_ano_proximo[:]
    ajustada_base = ajs_ano_atual[:] + ajs_ano_proximo[:]
    
    # st.write(f"[DEBUG] analitica tamanho: {len(analitica)}, num_meses_total será: 24")
    
    num_meses_total = 24
    
    # Session state para ajustada (pode ter sido modificada pelo painel)
    if "ajustada" not in st.session_state:
        st.session_state["ajustada"] = ajustada_base[:]
    else:
        # IMPORTANTE: Se a session_state tem tamanho diferente, resetar
        # Isso evita erro de índice quando mudar combo ou dados
        if len(st.session_state["ajustada"]) != len(ajustada_base):
            # st.write(f"[DEBUG] Resetando ajustada: session_state tem {len(st.session_state['ajustada'])}, base tem {len(ajustada_base)}")
            st.session_state["ajustada"] = ajustada_base[:]
    
    ajustada = st.session_state.get("ajustada", ajustada_base[:])
    
    # Carrega os valores dos estados (FONTE DE VERDADE)
    curva_analitica_state = st.session_state.get("curva_analitica", analitica[:])
    curva_mercado_state = st.session_state.get("curva_mercado", mercado[:])
    
    # ==================== MAPEAMENTO: Próximos 12 meses <-> Índices ====================
    # O painel mostra próximos 12 meses com nomenclatura dinâmica
    # Os índices podem ir de 0-23 se houver dados de 2027, ou 0-11 se só houver 2026
    
    indices_proximo_12m = []
    for i in range(12):
        mes_abs = (mes_atual - 1 + i)  # 0-based: mês absoluto
        # Se temos 24 meses, não precisa wrap (vai até 23)
        # Se temos 12 meses, faz wrap com modulo
        if num_meses_total == 24:
            # Para 24 meses, validar que não ultrapassa (máximo é 23)
            mes_idx = mes_abs if mes_abs < 24 else (mes_abs % 12)
        else:
            mes_idx = mes_abs % 12  # Wrap para 0-11
        indices_proximo_12m.append(mes_idx)

    # Aplica sincronização pendente (suporta pré-sync e sync do ciclo atual)
    def _aplicar_pending_sync(pending_vals, tag):
        if pending_vals is None or len(pending_vals) != 12:
            print(f"[SYNC-DEBUG] Nenhum pending_sync para aplicar ({tag})")
            return None

        print(f"[SYNC-DEBUG] Aplicando pending_sync ({tag}): {[f'{v:.0f}' for v in pending_vals[:3]]}...")
        cur = st.session_state.get("ajustada", ajustada_base[:])
        if len(cur) != len(ajustada_base):
            cur = ajustada_base[:]
        for i, v in enumerate(pending_vals):
            idx = indices_proximo_12m[i]
            try:
                print(f"[SYNC-DEBUG]   [{i}] pending_sync[{i}]={v:.0f} -> ajustada[{idx}]")
                cur[idx] = float(v)
            except Exception:
                pass
        print(f"[SYNC-DEBUG] Após aplicação: ajustada={[f'{x:.0f}' for x in cur]}")
        st.session_state["ajustada"] = cur
        return cur

    ajustada_sync = _aplicar_pending_sync(pending_sync_pre, "pre")
    if ajustada_sync is not None:
        ajustada = ajustada_sync

    # Aplica também o sync capturado NESTE ciclo de render
    pending_sync_now = st.session_state.pop("_pending_sync_ajustada12", None)
    if isinstance(pending_sync_now, list) and len(pending_sync_now) == 12:
        try:
            print(
                f"[SYNC-TRACE] pending_now recebido head={[round(float(v), 2) for v in pending_sync_now[:3]]} "
                f"jul_idx6={round(float(pending_sync_now[6]), 2)}"
            )
        except Exception:
            pass
    ajustada_sync_now = _aplicar_pending_sync(pending_sync_now, "now")
    if ajustada_sync_now is not None:
        ajustada = ajustada_sync_now
    
    # st.write(f"[DEBUG] indices_proximo_12m: {indices_proximo_12m}")
    # st.write(f"[DEBUG] len(ajustada): {len(ajustada)}, max(indices_proximo_12m): {max(indices_proximo_12m)}")
    
    # Extrai dados dos próximos 12 meses a partir dos arrays (Jan-Dez ou Jan-Dez + Jan-Dez 2027)
    analitica_proximos12 = [analitica[idx] for idx in indices_proximo_12m]
    mercado_proximos12 = [mercado[idx] for idx in indices_proximo_12m]
    ajustada_proximos12 = [ajustada[idx] for idx in indices_proximo_12m]
    
    # Calcula o incremento líquido para o painel
    incremento_liquido = [ajustada[indices_proximo_12m[i]] - analitica[indices_proximo_12m[i]] for i in range(12)]

    # **SERÁ ATUALIZADO APÓS CRIAR src_ajs** com estes dados

    def _fmt_delta_resumido(valor):
        try:
            vv = float(valor)
        except Exception:
            return "—"
        sinal = "+" if vv > 0 else ""
        abs_val = abs(vv)
        if abs_val >= 1e9:
            return f"{sinal}{vv / 1e9:.1f}B"
        if abs_val >= 1e6:
            return f"{sinal}{vv / 1e6:.1f}M"
        return f"{sinal}{vv:,.0f}".replace(",", ".")

    # ==================== HANDLER DO BOTÃO SALVAR ====================
    # Executado AQUI (após pending_sync aplicado e ajustada atualizado)
    # para que session_state["ajustada"] já contenha os valores mais recentes da tabela/gráfico.
    salvar_clicked = bool(st.session_state.pop("_trigger_save_simulador", False))
    if salvar_clicked:
        print(f"\n[SAVE-DEBUG] Botao SALVAR clicado")
        print(f"[SAVE-DEBUG] pending_sync_pre era: {pending_sync_pre is not None}")
        ajustadas_keys = [k for k in st.session_state.keys() if 'ajustada' in k.lower()]
        print(f"[SAVE-DEBUG] session_state keys com 'ajustada': {ajustadas_keys}")

        # Força leitura do localStorage no instante do save para capturar a última edição da tabela
        save_sync_counter = int(st.session_state.get("_save_sync_counter", 0)) + 1
        st.session_state["_save_sync_counter"] = save_sync_counter
        packet_save = get_bokeh_update_packet(
            key=f"sim_bokeh_{combo}",
            sync_counter=1_000_000 + save_sync_counter
        )
        valores_save = packet_save.get("values") if packet_save else None
        ts_save = int(packet_save.get("timestamp") or 0) if packet_save else 0
        probe_save = packet_save.get("probe") if packet_save and isinstance(packet_save.get("probe"), dict) else None

        try:
            if isinstance(valores_save, list) and len(valores_save) == 12:
                print(
                    f"[SAVE-TRACE] combo={combo} ts={ts_save} "
                    f"vals_head={[round(float(v), 2) for v in valores_save[:3]]} "
                    f"jul_idx6={round(float(valores_save[6]), 2)} probe={probe_save}"
                )
            else:
                print(f"[SAVE-TRACE] combo={combo} sem_vals ts={ts_save} probe={probe_save}")
        except Exception:
            pass

        if valores_save is not None and len(valores_save) == 12:
            cur_save = st.session_state.get("ajustada", ajustada_base[:])
            if len(cur_save) != len(ajustada_base):
                cur_save = ajustada_base[:]
            for i, v in enumerate(valores_save):
                idx = indices_proximo_12m[i]
                try:
                    cur_save[idx] = float(v)
                except Exception:
                    pass
            st.session_state["ajustada"] = cur_save
            print(f"[SAVE-DEBUG] ✓ localStorage capturado no save: {[f'{v:.0f}' for v in valores_save[:3]]}...")
            ajustada_para_salvar = cur_save
        else:
            print("[SAVE-DEBUG] ✗ Sem leitura de localStorage no save; usando session_state['ajustada']")
            ajustada_para_salvar = st.session_state.get("ajustada", [0.0] * 24)

        print(f"[SAVE-DEBUG] ajustada_para_salvar primeiros 12: {list(ajustada_para_salvar[:12])}")
        print(f"[SAVE-DEBUG] soma dos 12 primeiros: {sum(ajustada_para_salvar[:12])}")
        sim_salva = adicionar_simulacao(
            nome=st.session_state.get("filtros", {}).get("nome", "Simulação"),
            categoria=st.session_state.get("filtros", {}).get("categoria", ""),
            produto=st.session_state.get("filtros", {}).get("produto", ""),
            taxa_crescimento=st.session_state.get("sim_incremento_perc", 0),
            volatilidade=st.session_state.get("sim_rotacionar_curva", 1.0),
            cenarios={
                "Ajustada": True,
                "Cliente": st.session_state.get("filtros", {}).get("cliente", "Todos"),
                "CD_TIP_AGPD": st.session_state.get("filtros", {}).get("cd_tip_agpd", "Todos"),
                "TIP_TD": st.session_state.get("filtros", {}).get("tip_td", "Todos"),
                "ajuste_mensal": st.session_state.get("sim_ajuste_mensal_final", 0),
                "inclinacao": st.session_state.get("sim_inclinacao", 0),
            },
            dados_grafico={"Ajustada": ajustada_para_salvar},
        )
        try:
            usuario_id = st.session_state.get("usuario_id", "")
            cliente_sim = st.session_state.get("filtros", {}).get("cliente", "Todos")
            categoria_sim = st.session_state.get("filtros", {}).get("categoria", "")
            produto_sim = st.session_state.get("filtros", {}).get("produto", "")
            ano_sim = int(st.session_state.get("ano_simulacao", ano_atual))
            if usuario_id and cliente_sim and categoria_sim and produto_sim:
                from data_manager import sincronizar_curva_para_backend
                sincronizar_curva_para_backend(usuario_id, cliente_sim, categoria_sim,
                                              produto_sim, ano_sim, ajustada_para_salvar)
        except Exception as e:
            print(f"[SIMULADOR] Aviso: Não foi possível sincronizar com backend: {e}")
        # Feedback persistente após rerun para atualizar o bloco "Simulações Salvas" imediatamente
        st.session_state["_save_feedback_msg"] = (
            f"✅ Simulação '{sim_salva.get('nome', '')}' salva com sucesso! "
            f"ID: {sim_salva.get('id', '')[:20]}..."
        )
        st.rerun()
    
    # Função callback para ajustar mês (atualiza ajustada nos índices corretos)
    def _ajustar_mes(painel_idx: int, delta: float):
        mes_idx = indices_proximo_12m[painel_idx]
        cur = st.session_state.get("ajustada", ajustada[:])
        cur[mes_idx] = max(0, cur[mes_idx] + delta)
        st.session_state["ajustada"] = cur
    
    # Função callback para replicar ajuste para meses seguintes
    def _replicar_ajuste(painel_idx: int):
        """Replica o incremento do mês atual para todos os meses seguintes."""
        mes_idx = indices_proximo_12m[painel_idx]
        cur = st.session_state.get("ajustada", ajustada[:])
        inc_atual = cur[mes_idx] - analitica[mes_idx]
        
        # Aplica para os meses seguintes
        for i in range(painel_idx + 1, 12):
            mes_idx_seguinte = indices_proximo_12m[i]
            cur[mes_idx_seguinte] = max(0, analitica[mes_idx_seguinte] + inc_atual)
        
        st.session_state["ajustada"] = cur

    # ==================== PAINEL DE AJUSTE MANUAL POR MÊS ====================
    incremento_perc = st.session_state.get("sim_incremento_perc", 0.05)
    
    with st.expander("⚙️ Ajuste Manual por Mês", expanded=False):
        # CSS para cards e botões + JavaScript para estilizar botões
        st.markdown("""
        <style>
            /* Cards de mês */
            .mes-card {
                background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
                border-radius: 8px;
                padding: 8px 12px;
                text-align: center;
                border: 1px solid #e2e8f0;
                min-height: 48px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                transition: all 0.2s ease;
                margin-bottom: 8px;
            }
            .mes-card:hover {
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                border-color: #cbd5e1;
            }
            .mes-nome {
                font-weight: 700;
                color: #0c3a66;
                font-size: 13px;
                line-height: 1.2;
            }
            .mes-valor {
                color: #334155;
                font-size: 11px;
                line-height: 1.2;
            }
            .mes-delta {
                font-size: 10px;
                font-weight: 600;
                line-height: 1.1;
                margin-left: 4px;
            }
            .mes-delta.pos { color: #059669; }
            .mes-delta.neg { color: #dc2626; }
            
            /* Espaçador entre linhas */
            .spacer-row {
                height: 8px;
            }
            
            /* Botões base no expander - tamanho fixo */
            .stExpander button[kind="secondary"] {
                min-height: 38px !important;
                max-height: 38px !important;
                font-size: 16px !important;
                font-weight: 700 !important;
                border-radius: 8px !important;
                padding: 0 !important;
            }
        </style>
        <script>
        // Estiliza botões de + e - após carregamento
        const styleButtons = () => {
            document.querySelectorAll('.stExpander button').forEach(btn => {
                const text = btn.textContent.trim();
                if (text === '➕' || text === '+') {
                    btn.style.color = '#0c3a66';
                    btn.style.fontWeight = '800';
                    btn.style.fontSize = '20px';
                } else if (text === '➖' || text === '−' || text === '-') {
                    btn.style.color = '#0c3a66';
                    btn.style.fontWeight = '800';
                    btn.style.fontSize = '20px';
                } else if (text === '⬇️' || text.includes('⬇')) {
                    btn.style.color = '#0c3a66';
                    btn.style.fontWeight = '700';
                    btn.style.fontSize = '16px';
                    btn.style.background = 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)';
                    btn.style.border = 'none';
                }
            });
        };
        // Executa após um pequeno delay e também observa mudanças
        setTimeout(styleButtons, 100);
        setTimeout(styleButtons, 500);
        setTimeout(styleButtons, 1000);
        const observer = new MutationObserver(styleButtons);
        observer.observe(document.body, {childList: true, subtree: true});
        </script>
        """, unsafe_allow_html=True)
        
        # Header informativo
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0c3a66 0%, #1a5f7a 100%); 
                    padding: 10px 14px; border-radius: 8px; margin-bottom: 12px;">
            <span style="color: white; font-size: 12px;">
                📊 <b>Incremento:</b> {incremento_perc:.2%} | 
                <b>Fórmula:</b> valor ± (analítica × {incremento_perc:.2%})
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Grid por COLUNAS (vertical): 3 colunas x 4 linhas por coluna
        # Mostra os próximos 12 meses com nomenclatura dinâmica (Mar/26, Abr/26, etc.)
        cols = st.columns(3, gap="medium")
        
        for col_idx in range(3):
            with cols[col_idx]:
                for row_idx in range(4):
                    painel_idx = col_idx * 4 + row_idx
                    mes_nome = meses_rotulos[painel_idx]  # Rótulo: "Mar/26", "Abr/26", etc.
                    mes_idx_ano = indices_proximo_12m[painel_idx]  # Índice no array Jan-Dez
                    valor_atual = ajustada[mes_idx_ano]  # Valor do mês no ano
                    inc = incremento_liquido[painel_idx]
                    inc_step = analitica[mes_idx_ano] * incremento_perc  # Step baseado em analítica do ano
                    
                    # Delta display
                    delta_html = ""
                    if abs(inc) > 0:
                        delta_class = "pos" if inc > 0 else "neg"
                        delta_html = f'<span class="mes-delta {delta_class}">{_fmt_delta_resumido(inc)}</span>'
                    
                    # Layout: botão(-) - card - botão(+) - botão(⬇️ replicar)
                    c1, c2, c3, c4 = st.columns([1, 5, 1, 1])
                    
                    with c1:
                        st.button("➖", key=f"dec_{painel_idx}", 
                                on_click=lambda i=painel_idx, s=inc_step: _ajustar_mes(i, -s),
                                use_container_width=True)
                    
                    with c2:
                        st.markdown(f"""
                        <div class="mes-card">
                            <span class="mes-nome">{mes_nome}</span>
                            <span class="mes-valor">R$ {valor_atual/1e9:.2f}B {delta_html}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with c3:
                        st.button("➕", key=f"inc_{painel_idx}",
                                on_click=lambda i=painel_idx, s=inc_step: _ajustar_mes(i, s),
                                use_container_width=True)
                    
                    with c4:
                        # Botão de replicar (só aparece se não for o último mês)
                        if painel_idx < 11:
                            st.button("⬇️", key=f"rep_{painel_idx}",
                                    on_click=lambda i=painel_idx: _replicar_ajuste(i),
                                    use_container_width=True,
                                    help=f"Replicar ajuste de {mes_nome} para meses seguintes")
                    
                    # Espaçador entre linhas
                    if row_idx < 3:
                        st.markdown('<div class="spacer-row"></div>', unsafe_allow_html=True)
        
        # Resumo elegante
        total_inc = sum(incremento_liquido)
        sinal = "+" if total_inc > 0 else ""
        cor = "#059669" if total_inc >= 0 else "#dc2626"
        
        st.markdown(f"""
        <div style="background: #f1f5f9; border-radius: 8px; padding: 12px 16px; margin-top: 12px;
                    display: flex; justify-content: space-between; align-items: center; border: 1px solid #e2e8f0;">
            <span style="font-weight: 600; color: #334155; font-size: 14px;">
                📊 Ajuste Total: <span style="color: {cor}; font-weight: 700;">{sinal}R$ {total_inc/1e9:.2f}B</span>
            </span>
            <span style="color: #64748b; font-size: 12px;">
                Step: ~R$ {analitica_proximos12[0] * incremento_perc/1e9:.3f}B
            </span>
        </div>
        """, unsafe_allow_html=True)

    # -------------------- GRÁFICO PRINCIPAL ----------------------------------
    # O gráfico usa dados dos PRÓXIMOS 12 MESES, extraídos de analitica/mercado/ajustada (Jan-Dez)
    src_ana = ColumnDataSource(dict(x=meses_numeros, y=analitica_proximos12), name="src_ana_main")
    src_mer = ColumnDataSource(dict(x=meses_numeros, y=mercado_proximos12), name="src_mer_main")
    src_ajs = ColumnDataSource(dict(
        x=meses_numeros,
        xm=meses_rotulos,  # Usa rótulos dos próximos 12 meses
        y=ajustada_proximos12,  # Extrai dados dos próximos 12 meses
        y_br=[fmt_br(v, 0) for v in ajustada_proximos12]
    ), name="src_ajs_main")

    # Sempre atualizar src_ajs após recalcular ajustada_proximos12 (em caso de sincronização)
    src_ajs.data = dict(
        x=meses_numeros,
        xm=meses_rotulos,
        y=ajustada_proximos12,
        y_br=[fmt_br(v, 0) for v in ajustada_proximos12]
    )

    p = figure(
        height=400, sizing_mode="stretch_width",
        x_range=(0.5,12.5), x_axis_label="Mês", y_axis_label="Valor (R$)",
        toolbar_location="right",
        title="",  # Título removido (exibido via Streamlit acima)
        stylesheets=[style_top]
    )
    p.background_fill_color="#fafbfc"; p.grid.grid_line_alpha=0.18
    p.min_border_top = 8; p.min_border_bottom = 40  # Espaço para legenda embaixo
    p.yaxis.formatter = NumeralTickFormatter(format="0.00a")
    p.title.text_font_size = "0pt"  # Oculta título
    p.xaxis.ticker = MESES_NUM
    p.xaxis.major_label_overrides = {i: meses_rotulos[i-1] for i in MESES_NUM}
    p.xaxis.major_label_text_font_size = "12px"
    p.yaxis.major_label_text_font_size = "12px"
    p.outline_line_color = "#e2e8f0"
    p.border_fill_color = "#ffffff"

    r_ana = p.line("x","y", source=src_ana, color=COR_ANALITICA, line_width=3, muted_alpha=0.15)
    r_mer = p.line("x","y", source=src_mer, color=COR_MERCADO, line_width=3, line_dash="dashed", muted_alpha=0.15)
    r_ajs = p.line("x","y", source=src_ajs, color=COR_AJUSTADA, line_width=4, line_dash="dotted", muted_alpha=0.15)
    pts = p.scatter("x","y", source=src_ajs, size=16, color=COR_AJUSTADA, line_color="white", line_width=2, marker="circle")

    draw = PointDrawTool(renderers=[pts], empty_value=np.nan)
    p.add_tools(draw); p.toolbar.active_drag = draw
    p.add_tools(HoverTool(renderers=[pts], tooltips=[("Mês","@xm"),("Ajustada","R$ @y_br")]))
    p.add_tools(FullscreenTool())  # Ferramenta de tela cheia nativa do Bokeh

    legend = Legend(items=[
        LegendItem(label="Projeção Analítica", renderers=[r_ana]),
        LegendItem(label="Projeção Mercado",  renderers=[r_mer]),
        LegendItem(label="Projeção Ajustada", renderers=[r_ajs]),
    ], click_policy="mute", orientation="horizontal", label_text_font_size="11pt",
    location="bottom_center", background_fill_alpha=0.8, border_line_alpha=0.3)
    p.add_layout(legend, "below")
    
    # Configura toolbar mais completo (right side)
    p.toolbar_location = "right"

    # -------------------- DIV DE VALORES EM TEMPO REAL -----------------------
    # Exibe os valores da curva ajustada, atualizando em tempo real via JS
    # Usa os rótulos e valores dos PRÓXIMOS 12 MESES (não Jan-Dez)
    valores_html_inicial = " | ".join([
        f"<span style='color:#64748b'>{meses_rotulos[i]}:</span> <b style='color:#0f172a'>R$ {fmt_br(ajustada_proximos12[i], 0)}</b>" 
        for i in range(12)
    ])
    
    div_valores = Div(
        text=f"""<div style='font-size:11px; padding:10px 14px; 
                    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); 
                    border-radius:8px; border: 1px solid #e2e8f0;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
                <span style='color:#0c3a66; font-weight:600;'>📊 Curva Ajustada:</span> 
                {valores_html_inicial}</div>""",
        sizing_mode="stretch_width"
    )
    
    # Div para o Incremento em tempo real (atualizado via JS)
    # Usa dados dos próximos 12 meses para calcular incremento
    soma_ana_inicial = sum(analitica_proximos12) if analitica_proximos12 else 1
    soma_ajs_inicial = sum(ajustada_proximos12) if ajustada_proximos12 else 0
    incr_inicial_pct = ((soma_ajs_inicial / soma_ana_inicial) - 1) * 100 if soma_ana_inicial > 0 else 0
    incr_color = "#10b981" if incr_inicial_pct >= 0 else "#ef4444"
    incr_icon = "📈" if incr_inicial_pct >= 0 else "📉"
    
    div_incremento = Div(
        text=f"""<div id="div_incremento" style="
            background: linear-gradient(145deg, {'#ecfdf5' if incr_inicial_pct >= 0 else '#fef2f2'} 0%, #ffffff 100%);
            border: 2px solid {incr_color};
            border-radius: 12px;
            padding: 6px 16px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            min-width: 110px;
        ">
            <div style="font-size: 0.7rem; color: #64748b; font-weight: 500;">
                {incr_icon} Incremento
            </div>
            <div style="font-size: 1.3rem; font-weight: 700; color: {incr_color};">
                {incr_inicial_pct:+.2f}%
            </div>
        </div>""",
        sizing_mode="fixed",
        width=130
    )
    incr_inicial_pct = ((soma_ajs_inicial / soma_ana_inicial) - 1) * 100 if soma_ana_inicial > 0 else 0
    incr_color = "#10b981" if incr_inicial_pct >= 0 else "#ef4444"
    incr_icon = "📈" if incr_inicial_pct >= 0 else "📉"
    
    div_incremento = Div(
        text=f"""<div id="div_incremento" style="
            background: linear-gradient(145deg, {'#ecfdf5' if incr_inicial_pct >= 0 else '#fef2f2'} 0%, #ffffff 100%);
            border: 2px solid {incr_color};
            border-radius: 12px;
            padding: 6px 16px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            min-width: 110px;
        ">
            <div style="font-size: 0.7rem; color: #64748b; font-weight: 500;">
                {incr_icon} Incremento
            </div>
            <div style="font-size: 1.3rem; font-weight: 700; color: {incr_color};">
                {incr_inicial_pct:+.2f}%
            </div>
        </div>""",
        sizing_mode="fixed",
        width=130
    )
    
    # Callback JS para atualizar o Div de valores E o Div de incremento
    soma_analitica_js = sum(analitica) if analitica else 1
    cb_atualiza_div = CustomJS(
        args=dict(src=src_ajs, div=div_valores, div_incr=div_incremento, 
                meses=MESES_ABR_LIST, soma_ana=soma_analitica_js), 
        code="""
        const y = src.data['y'];
        if (!y || y.length < 12) return;
        
        function formatBR(v) {
            return v.toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 0});
        }
        
        // Atualiza div de valores
        let html = "<div style='font-size:11px; padding:10px 14px; ";
        html += "background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); ";
        html += "border-radius:8px; border: 1px solid #e2e8f0; ";
        html += "box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>";
        html += "<span style='color:#0c3a66; font-weight:600;'>📊 Curva Ajustada:</span> ";
        const parts = [];
        for (let i = 0; i < 12; i++) {
            parts.push("<span style='color:#64748b'>" + meses[i] + ":</span> <b style='color:#0f172a'>R$ " + formatBR(y[i]) + "</b>");
        }
        html += parts.join(" | ");
        html += "</div>";
        div.text = html;
        
        // Calcula e atualiza incremento
        let soma_ajs = 0;
        for (let i = 0; i < 12; i++) {
            soma_ajs += y[i];
        }
        const incr_pct = soma_ana > 0 ? ((soma_ajs / soma_ana) - 1) * 100 : 0;
        const incr_color = incr_pct >= 0 ? "#10b981" : "#ef4444";
        const incr_bg = incr_pct >= 0 ? "#ecfdf5" : "#fef2f2";
        const incr_icon = incr_pct >= 0 ? "📈" : "📉";
        const incr_sign = incr_pct >= 0 ? "+" : "";
        
        let html_incr = '<div style="';
        html_incr += 'background: linear-gradient(145deg, ' + incr_bg + ' 0%, #ffffff 100%);';
        html_incr += 'border: 2px solid ' + incr_color + ';';
        html_incr += 'border-radius: 12px; padding: 6px 16px; text-align: center;';
        html_incr += 'box-shadow: 0 2px 8px rgba(0,0,0,0.08); min-width: 110px;">';
        html_incr += '<div style="font-size: 0.7rem; color: #64748b; font-weight: 500;">';
        html_incr += incr_icon + ' Incremento</div>';
        html_incr += '<div style="font-size: 1.3rem; font-weight: 700; color: ' + incr_color + ';">';
        html_incr += incr_sign + incr_pct.toFixed(2) + '%</div></div>';
        div_incr.text = html_incr;
    """)
    src_ajs.js_on_change("data", cb_atualiza_div)

    # -------------------- TABELA : PRÓXIMOS 12 MESES ====================
    # A tabela mostra os próximos 12 meses (com rótulos dinâmicos: Mar/26, ..., Fev/27)
    var_ana = _variacao_mensal(analitica_proximos12)
    var_mer = _variacao_mensal(mercado_proximos12)
    var_ajs = _variacao_mensal(ajustada_proximos12)

    mes_display = meses_rotulos[:]  # ["Mar/26", "Abr/26", ..., "Jan/27", "Fev/27"]
    mes_ord    = list(range(1, 13))
    
    # ============ TABELA 1: RESUMO (próximos 12 meses) ============
    tbl_data = dict(Mes=mes_display, Mes_Ord=mes_ord)

    # Dados históricos (se houver)
    for ano in anos_realizados:
        tbl_data[f"Rlzd_{ano}"] = realizados_dict[ano]
        tbl_data[f"Var_{ano}"]  = variacoes_rlzd[ano]

    # Valores realizados para o ano atual (2026) - apenas para os meses dentro de 2026
    rlzd_ano_atual = realizados_dict.get(ano_atual, [0.0] * 12)
    
    # Construir dados para próximos 12 meses considerando realizado vs projeção
    ana_com_realizado = []
    mer_com_realizado = []
    ajs_com_realizado = []
    
    # Iterar sobre os próximos 12 meses
    for painel_idx in range(12):
        mes_idx = indices_proximo_12m[painel_idx]  # Índice no array maior (0-23 se houver 2027, ou 0-11)
        
        # Verificar se este mês é do ano atual (2026) e já passou
        # Para isso, precisamos saber se o índice está em 2026 ou 2027
        if mes_idx < 12:  # Está em 2026
            mes_numero_2026 = mes_idx + 1  # 1-12
            
            # Se o mês já passou em 2026 E tem realizado, usar realizado
            rlzd_val = rlzd_ano_atual[mes_idx]
            tem_realizado = rlzd_val is not None and not np.isnan(rlzd_val) if isinstance(rlzd_val, (float, int)) else rlzd_val
            tem_realizado = tem_realizado and rlzd_val != 0.0
            
            if mes_numero_2026 <= mes_atual and tem_realizado:
                # Usar valor realizado do ano atual (2026)
                ana_com_realizado.append(rlzd_val)
                mer_com_realizado.append(rlzd_val)
                ajs_com_realizado.append(rlzd_val)
            else:
                # Usar projeção
                ana_com_realizado.append(analitica[mes_idx])
                mer_com_realizado.append(mercado[mes_idx])
                ajs_com_realizado.append(ajustada[mes_idx])
        else:  # Está em 2027 ou além - sempre usar projeção (não tem realizado)
            ana_com_realizado.append(analitica[mes_idx])
            mer_com_realizado.append(mercado[mes_idx])
            ajs_com_realizado.append(ajustada[mes_idx])
    
    # Atribuir aos dados da tabela
    tbl_data["Analitica"] = ana_com_realizado
    tbl_data["Var_Ana"]   = _variacao_mensal(ana_com_realizado)
    tbl_data["Mercado"]   = mer_com_realizado
    tbl_data["Var_Mer"]   = _variacao_mensal(mer_com_realizado)
    tbl_data["Ajustada"]  = ajs_com_realizado
    tbl_data["Var_Ajs"]   = _variacao_mensal(ajs_com_realizado)
    
    # Coluna de Ajuste (incremento líquido = Ajustada - Analítica)
    tbl_data["Ajuste"] = [ajs_com_realizado[i] - ana_com_realizado[i] for i in range(12)]
    
    # ==================== INTEGRAR MESES PASSADOS = REALIZADO ====================
    # Marca quais meses já passaram (para formatação de cor)
    tbl_data["_eh_realizado"] = []
    
    # Para cada mês no painel, verificar se é do passado
    for painel_idx in range(12):
        mes_idx = indices_proximo_12m[painel_idx]
        
        # Apenas marcar como realizado se está em 2026 E o mês já passou
        if mes_idx < 12:  # Está em 2026
            mes_numero_2026 = mes_idx + 1  # 1-12
            if mes_numero_2026 <= mes_atual:
                tbl_data["_eh_realizado"].append(True)
            else:
                tbl_data["_eh_realizado"].append(False)
        else:  # Está em 2027 ou além - sempre futuro
            tbl_data["_eh_realizado"].append(False)

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
    media_row["Ajuste"]    = _mean_safe(tbl_data["Ajuste"])

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
    cres_row["Ajuste"] = _delta_first_last(tbl_data["Ajuste"])

    for k in list(tbl_data.keys()):
        if k == "Mes":
            tbl_data[k] = tbl_data[k] + [media_row["Mes"], cres_row["Mes"]]
        elif k == "Mes_Ord":
            tbl_data[k] = tbl_data[k] + [media_row["Mes_Ord"], cres_row["Mes_Ord"]]
        elif k == "_eh_realizado":
            # As linhas de média e crescimento não são realizado
            tbl_data[k] = tbl_data[k] + [False, False]
        else:
            tbl_data[k] = tbl_data[k] + [media_row.get(k, 0.0), cres_row.get(k, 0.0)]

    for ano in anos_realizados:
        if f"Var_{ano}" in tbl_data:
            tbl_data[f"Var_{ano}_Disp"] = _build_var_disp_column(tbl_data[f"Var_{ano}"])
    tbl_data["Var_Ana_Disp"] = _build_var_disp_column(tbl_data["Var_Ana"])
    tbl_data["Var_Mer_Disp"] = _build_var_disp_column(tbl_data["Var_Mer"])
    tbl_data["Var_Ajs_Disp"] = _build_var_disp_column(tbl_data["Var_Ajs"])

    tbl_src = ColumnDataSource(tbl_data)

    # Templates de formatação - FORMATO ABREVIADO (M = Milhões, B = Bilhões)
    CURRENCY_TMPL = """
    <% 
      function formatShort(val) {
        if (val == null || isNaN(val)) return '—';
        const absVal = Math.abs(val);
        if (absVal >= 1e9) return (val/1e9).toFixed(1) + 'B';
        if (absVal >= 1e6) return (val/1e6).toFixed(1) + 'M';
        return val.toLocaleString('pt-BR', {maximumFractionDigits:0});
      }
    %>
    <%= formatShort(value) %>
    """
    AJUSTADA_TMPL = """
    <span style="color:#1a5f7a;font-weight:600;cursor:pointer;" title="Clique duplo para editar">
    <% 
      function formatShort(val) {
        if (val == null || isNaN(val)) return '—';
        const absVal = Math.abs(val);
        if (absVal >= 1e9) return (val/1e9).toFixed(1) + 'B';
        if (absVal >= 1e6) return (val/1e6).toFixed(1) + 'M';
        return val.toLocaleString('pt-BR', {maximumFractionDigits:0});
      }
    %>
    <%= formatShort(value) %>
    </span>
    """
    
    # ==== CustomJS para sincronizar Gráfico <-> Tabela ====
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
        _obter_realizados_por_ano(
            df_upload,
            cliente,
            categoria,
            produto,
            mascarar_zeros_finais=MASCARAR_ZEROS_FINAIS,
            cd_tip_agpd=sim_cd_tip_agpd,
            tip_td=sim_tip_td,
        ),
        analitica, mercado, ajustada, ano_proj, style_top, src_ajs_ref=src_ajs
    )
    g2 = _grafico_serie_historica(df_upload, cliente, categoria, produto,
                                analitica, mercado, ajustada, ano_atual,
                                style_top,
                                src_ajs_ref=src_ajs,
                                mes_proj=mes_atual,
                                cd_tip_agpd=sim_cd_tip_agpd,
                                tip_td=sim_tip_td)

    layout_topo = column(
        row(div_valores, div_incremento, sizing_mode="stretch_width", height=100),
        p,
        row(g1, g2, sizing_mode="stretch_width", height=450),
        sizing_mode="stretch_width",
    )
    
    # ==================== BOTÕES DE CONTROLE (ACIMA DO GRÁFICO) ====================
    ajustada = st.session_state.get("ajustada", analitica[:])
    sync_counter = st.session_state.get("sync_counter", 0)
    
    # Buscar SCORE (MAPE) do modelo de ML para o produto
    mape_score = get_score_by_produto_nome(produto, df_upload)
    
    # Calcular Incremento: variação entre total Ajustada vs total Analítica
    soma_analitica = sum(analitica) if analitica else 0
    soma_ajustada = sum(ajustada) if ajustada else 0
    if soma_analitica > 0:
        incremento_pct = (soma_ajustada / soma_analitica) - 1
    else:
        incremento_pct = 0
    
    # Layout: Título à esquerda, SCORE, e botões à direita
    col_titulo, col_score, col_sync, col_reset = st.columns(
        [4, 1.2, 1.3, 1.3]
    )
    
    with col_titulo:
        st.markdown(f"""<div style="padding: 8px 0;">
            <span style="font-size: 1.1rem; font-weight: 600; color: #0c3a66;">📈 Curva de Projeção Ajustada</span>
            <span style="font-size: 0.85rem; color: #64748b;"> • {cliente or 'Portfólio'} • {categoria} • {produto}</span>
        </div>""", unsafe_allow_html=True)
    
    with col_score:
        # Card de SCORE (MAPE do modelo)
        if mape_score is not None:
            # MAPE válido - cor verde se baixo (<10%), amarelo se médio, vermelho se alto
            if mape_score < 0.10:
                score_color = "#10b981"  # Verde
                score_bg = "#ecfdf5"
            elif mape_score < 0.30:
                score_color = "#f59e0b"  # Amarelo
                score_bg = "#fffbeb"
            else:
                score_color = "#ef4444"  # Vermelho
                score_bg = "#fef2f2"
            score_display = f"{mape_score*100:.2f}%"
        else:
            score_color = "#94a3b8"
            score_bg = "#f1f5f9"
            score_display = "N/D"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {score_bg} 0%, #ffffff 100%);
            border: 2px solid {score_color};
            border-radius: 12px;
            padding: 6px 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        ">
            <div style="font-size: 0.7rem; color: #64748b; font-weight: 500;">
                🎯 SCORE
            </div>
            <div style="font-size: 1.3rem; font-weight: 700; color: {score_color};">
                {score_display}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_sync:
        # Botão Sincronizar com estilo elegante via HTML
        sync_clicked = st.button("🔄 Sincronizar", key=f"sync_{combo}", 
                                help="Aplicar alterações do drag-and-drop",
                                use_container_width=True)
        if sync_clicked:
            st.session_state["sync_counter"] = sync_counter + 1
            st.session_state["sync_fetch_retry"] = 0
            st.rerun()
    
    with col_reset:
        # Botão Resetar com estilo elegante
        reset_clicked = st.button("↩️ Resetar", key=f"reset_{combo}",
                                help="Voltar para curva analítica original",
                                use_container_width=True)
        if reset_clicked:
            resetar_simulacao_atual()
            limpar_localStorage(key=f"sim_bokeh_{combo}")
            st.toast("↩️ Curva resetada!", icon="🔄")
            st.rerun()
    
    # CSS para estilizar botões Sincronizar/Resetar
    st.markdown("""
    <style>
        /* Estilo elegante para botões de controle */
        div[data-testid="column"]:nth-child(4) button,
        div[data-testid="column"]:nth-child(5) button {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            font-weight: 500 !important;
            color: #334155 !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="column"]:nth-child(4) button:hover,
        div[data-testid="column"]:nth-child(5) button:hover {
            background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%) !important;
            border-color: #3b82f6 !important;
            box-shadow: 0 2px 6px rgba(59,130,246,0.15) !important;
            color: #0c3a66 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Renderiza o gráfico Bokeh (drag-and-drop salva valores no localStorage)
    st.markdown("""
    <style>
        /* Controlar altura do container Bokeh para evitar espaço em branco excessivo */
        [data-testid="stIFrame"]:has(iframe.bk-root) {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        
        /* Remover espaços em branco após o container Bokeh */
        div.stHorizontalBlock {
            margin: 0 !important;
            padding: 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # ====================== TABELA SÉRIE HISTÓRICA (COM TODOS OS ANOS) ========================
    # Montar dados da série histórica com meses fixos (JAN-DEZ)
    meses_fixos = [m.upper() for m in MESES_ABR_LIST]
    tbl_hist_data = dict(Mes=meses_fixos, Mes_Ord=list(range(1, 13)))
    
    # ============ FILTRAR: APENAS REALIZADO DE 2025 (ÚLTIMO ANO ANTERIOR AO ATUAL) ============
    # Encontrar o último ano realizado (que seria 2025)
    ano_realizado_ultimo = max([a for a in anos_realizados if a < ano_atual], default=None)
    
    def _safe_year(arr):
        arr = [] if arr is None else list(arr)
        out = []
        for i in range(12):
            v = arr[i] if i < len(arr) else 0.0
            try:
                vv = float(v)
                if not np.isfinite(vv):
                    vv = 0.0
            except Exception:
                vv = 0.0
            out.append(vv)
        return out

    def _tem_realizado(v):
        try:
            vv = float(v)
            return np.isfinite(vv) and vv != 0.0
        except Exception:
            return False

    def _aplicar_realizado_em_projecao(base_proj, rlzd_ano):
        proj = []
        flags = []
        for i in range(12):
            rv = rlzd_ano[i]
            if _tem_realizado(rv):
                proj.append(float(rv))
                flags.append(True)
            else:
                proj.append(base_proj[i])
                flags.append(False)
        return proj, flags

    if ano_realizado_ultimo is not None:
        tbl_hist_data[f"Rlzd_{ano_realizado_ultimo}"] = _safe_year(realizados_dict.get(ano_realizado_ultimo, [0.0] * 12))
        tbl_hist_data[f"Var_{ano_realizado_ultimo}"] = _variacao_mensal(tbl_hist_data[f"Rlzd_{ano_realizado_ultimo}"])
    
    # ============ REALIZADOS E PROJEÇÕES (ANO ATUAL E PRÓXIMO ANO) ============
    ano_atual_str = str(ano_atual)
    ano_prox_str = str(ano_projecao_proxima)

    rlzd_ano_atual = _safe_year(realizados_dict.get(ano_atual, [0.0] * 12))
    rlzd_ano_prox = _safe_year(realizados_dict.get(ano_projecao_proxima, [0.0] * 12))
    tbl_hist_data[f"Rlzd_{ano_atual}"] = rlzd_ano_atual
    tbl_hist_data[f"Var_{ano_atual}"] = _variacao_mensal(rlzd_ano_atual)
    tbl_hist_data[f"Rlzd_{ano_projecao_proxima}"] = rlzd_ano_prox
    tbl_hist_data[f"Var_{ano_projecao_proxima}"] = _variacao_mensal(rlzd_ano_prox)

    ana_atual_base = _safe_year(analitica[:12])
    mer_atual_base = _safe_year(mercado[:12])
    ajs_atual_base = _safe_year(ajustada[:12])
    ana_prox_base = _safe_year(analitica[12:24])
    mer_prox_base = _safe_year(mercado[12:24])
    ajs_prox_base = _safe_year(ajustada[12:24])

    ana_atual_eff, flags_rlzd_atual = _aplicar_realizado_em_projecao(ana_atual_base, rlzd_ano_atual)
    mer_atual_eff, _ = _aplicar_realizado_em_projecao(mer_atual_base, rlzd_ano_atual)
    ajs_atual_eff, _ = _aplicar_realizado_em_projecao(ajs_atual_base, rlzd_ano_atual)

    ana_prox_eff, flags_rlzd_prox = _aplicar_realizado_em_projecao(ana_prox_base, rlzd_ano_prox)
    mer_prox_eff, _ = _aplicar_realizado_em_projecao(mer_prox_base, rlzd_ano_prox)
    ajs_prox_eff, _ = _aplicar_realizado_em_projecao(ajs_prox_base, rlzd_ano_prox)

    tbl_hist_data[f"Analitica_{ano_atual_str}"] = ana_atual_eff
    tbl_hist_data[f"Var_Ana_{ano_atual_str}"] = _variacao_mensal(ana_atual_eff)
    tbl_hist_data[f"Mercado_{ano_atual_str}"] = mer_atual_eff
    tbl_hist_data[f"Var_Mer_{ano_atual_str}"] = _variacao_mensal(mer_atual_eff)
    tbl_hist_data[f"Ajustada_{ano_atual_str}"] = ajs_atual_eff
    tbl_hist_data[f"Var_Ajs_{ano_atual_str}"] = _variacao_mensal(ajs_atual_eff)
    tbl_hist_data[f"Ajuste_{ano_atual_str}"] = [ajs_atual_eff[i] - ana_atual_eff[i] for i in range(12)]

    tbl_hist_data[f"Analitica_{ano_prox_str}"] = ana_prox_eff
    tbl_hist_data[f"Var_Ana_{ano_prox_str}"] = _variacao_mensal(ana_prox_eff)
    tbl_hist_data[f"Mercado_{ano_prox_str}"] = mer_prox_eff
    tbl_hist_data[f"Var_Mer_{ano_prox_str}"] = _variacao_mensal(mer_prox_eff)
    tbl_hist_data[f"Ajustada_{ano_prox_str}"] = ajs_prox_eff
    tbl_hist_data[f"Var_Ajs_{ano_prox_str}"] = _variacao_mensal(ajs_prox_eff)
    tbl_hist_data[f"Ajuste_{ano_prox_str}"] = [ajs_prox_eff[i] - ana_prox_eff[i] for i in range(12)]

    tbl_hist_data[f"_eh_realizado_{ano_atual_str}"] = flags_rlzd_atual
    tbl_hist_data[f"_eh_realizado_{ano_prox_str}"] = flags_rlzd_prox
    
    # Calcular linhas de MÉDIA e CRESCIMENTO para série histórica
    def _mean_safe(v):
        v = np.array(v, dtype=float)
        return float(np.nanmean(v)) if v.size else 0.0

    def _delta_first_last(v):
        v = list(map(float, v))
        if not v: return 0.0
        return float(v[-1] - v[0])

    media_row_hist = {"Mes": "MÉDIA / VAR%", "Mes_Ord": 13}
    
    # MÉDIA: último ano realizado (2025)
    if ano_realizado_ultimo is not None:
        media_row_hist[f"Rlzd_{ano_realizado_ultimo}"] = _mean_safe(tbl_hist_data[f"Rlzd_{ano_realizado_ultimo}"])
        media_row_hist[f"Var_{ano_realizado_ultimo}"]  = _mean_safe(tbl_hist_data[f"Var_{ano_realizado_ultimo}"])
    
    # MÉDIA: realizado do ano atual (2026)
    media_row_hist[f"Rlzd_{ano_atual}"] = _mean_safe(tbl_hist_data[f"Rlzd_{ano_atual}"])
    media_row_hist[f"Var_{ano_atual}"]  = _mean_safe(tbl_hist_data[f"Var_{ano_atual}"])
    
    # MÉDIA: realizado do próximo ano (2027)
    media_row_hist[f"Rlzd_{ano_projecao_proxima}"] = _mean_safe(tbl_hist_data[f"Rlzd_{ano_projecao_proxima}"])
    media_row_hist[f"Var_{ano_projecao_proxima}"] = _mean_safe(tbl_hist_data[f"Var_{ano_projecao_proxima}"])

    # MÉDIA: projeções do ano atual e próximo ano
    for year_suf in [ano_atual_str, ano_prox_str]:
        media_row_hist[f"Analitica_{year_suf}"] = _mean_safe(tbl_hist_data[f"Analitica_{year_suf}"])
        media_row_hist[f"Var_Ana_{year_suf}"] = _mean_safe(tbl_hist_data[f"Var_Ana_{year_suf}"])
        media_row_hist[f"Mercado_{year_suf}"] = _mean_safe(tbl_hist_data[f"Mercado_{year_suf}"])
        media_row_hist[f"Var_Mer_{year_suf}"] = _mean_safe(tbl_hist_data[f"Var_Mer_{year_suf}"])
        media_row_hist[f"Ajustada_{year_suf}"] = _mean_safe(tbl_hist_data[f"Ajustada_{year_suf}"])
        media_row_hist[f"Var_Ajs_{year_suf}"] = _mean_safe(tbl_hist_data[f"Var_Ajs_{year_suf}"])
        media_row_hist[f"Ajuste_{year_suf}"] = _mean_safe(tbl_hist_data[f"Ajuste_{year_suf}"])

    cres_row_hist = {"Mes": "CRESC. VOL", "Mes_Ord": 14}
    
    # CRESCIMENTO: último ano realizado (2025)
    if ano_realizado_ultimo is not None:
        delta = _delta_first_last(tbl_hist_data[f"Rlzd_{ano_realizado_ultimo}"])
        cres_row_hist[f"Rlzd_{ano_realizado_ultimo}"] = delta
        cres_row_hist[f"Var_{ano_realizado_ultimo}"]  = 1.0 if delta > 0 else (-1.0 if delta < 0 else 0.0)
    
    # CRESCIMENTO: realizado do ano atual (2026)
    delta = _delta_first_last(tbl_hist_data[f"Rlzd_{ano_atual}"])
    cres_row_hist[f"Rlzd_{ano_atual}"] = delta
    cres_row_hist[f"Var_{ano_atual}"]  = 1.0 if delta > 0 else (-1.0 if delta < 0 else 0.0)
    
    # CRESCIMENTO: realizado do próximo ano
    delta = _delta_first_last(tbl_hist_data[f"Rlzd_{ano_projecao_proxima}"])
    cres_row_hist[f"Rlzd_{ano_projecao_proxima}"] = delta
    cres_row_hist[f"Var_{ano_projecao_proxima}"] = 1.0 if delta > 0 else (-1.0 if delta < 0 else 0.0)

    # CRESCIMENTO: projeções
    for year_suf in [ano_atual_str, ano_prox_str]:
        for field_val, field_var in [
            (f"Analitica_{year_suf}", f"Var_Ana_{year_suf}"),
            (f"Mercado_{year_suf}", f"Var_Mer_{year_suf}"),
            (f"Ajustada_{year_suf}", f"Var_Ajs_{year_suf}")
        ]:
            delta = _delta_first_last(tbl_hist_data[field_val])
            cres_row_hist[field_val] = delta
            cres_row_hist[field_var] = 1.0 if delta > 0 else (-1.0 if delta < 0 else 0.0)
        cres_row_hist[f"Ajuste_{year_suf}"] = _delta_first_last(tbl_hist_data[f"Ajuste_{year_suf}"])

    # Adicionar linhas de média e crescimento
    for k in list(tbl_hist_data.keys()):
        if k == "Mes":
            tbl_hist_data[k] = tbl_hist_data[k] + [media_row_hist["Mes"], cres_row_hist["Mes"]]
        elif k == "Mes_Ord":
            tbl_hist_data[k] = tbl_hist_data[k] + [media_row_hist["Mes_Ord"], cres_row_hist["Mes_Ord"]]
        elif k.startswith("_eh_realizado"):
            # Marcar linhas de média/crescimento como não-realizado
            tbl_hist_data[k] = tbl_hist_data[k] + [False, False]
        else:
            tbl_hist_data[k] = tbl_hist_data[k] + [media_row_hist.get(k, 0.0), cres_row_hist.get(k, 0.0)]

    # ============ COLUNAS DE DISPLAY (SEM BADGE CIRCULAR) ============
    COLOR_2025 = "#475569"
    COLOR_2026 = "#b45309"
    COLOR_2027 = "#0369a1"
    BG_2025 = "#f1f5f9"
    BG_2026 = "#fff7ed"
    BG_2027 = "#f0f9ff"

    def _fmt_short(v):
        if v is None or (isinstance(v, float) and not np.isfinite(v)):
            return "—"
        abs_val = abs(v)
        if abs_val >= 1e9:
            return f"{v/1e9:.1f}B"
        if abs_val >= 1e6:
            return f"{v/1e6:.1f}M"
        return f"{int(round(v))}"

    def _build_value_disp(values, color_hex, bg_hex, eh_realizado=None):
        out = []
        for i, v in enumerate(values):
            txt = _fmt_short(v)
            if txt == "—":
                out.append("—")
                continue
            is_real = bool(eh_realizado[i]) if eh_realizado is not None and i < len(eh_realizado) else False
            if is_real and i < 12:
                out.append(
                    f'<span style="background:#fef08a;padding:1px 5px;border-radius:3px;font-weight:700;color:#92400e;">{txt}</span>'
                )
            else:
                out.append(f'<span style="background:{bg_hex};padding:1px 5px;border-radius:3px;color:{color_hex};font-weight:700;">{txt}</span>')
        return out

    def _build_var_text_disp(values):
        out = []
        for i, v in enumerate(values):
            try:
                vv = float(v)
                if not np.isfinite(vv):
                    out.append("—")
                    continue
            except Exception:
                out.append("—")
                continue
            color = "#059669" if vv > 0 else ("#dc2626" if vv < 0 else "#334155")
            txt = f"{vv*100:+.2f}%"
            if i == 13:
                txt = "▲" if vv > 0 else ("▼" if vv < 0 else "•")
            out.append(f'<span style="color:{color};font-weight:700;">{txt}</span>')
        return out

    if ano_realizado_ultimo is not None:
        tbl_hist_data[f"Rlzd_{ano_realizado_ultimo}_Disp"] = _build_value_disp(tbl_hist_data[f"Rlzd_{ano_realizado_ultimo}"], COLOR_2025, BG_2025)
        tbl_hist_data[f"Var_{ano_realizado_ultimo}_Disp"] = _build_var_text_disp(tbl_hist_data[f"Var_{ano_realizado_ultimo}"])

    tbl_hist_data[f"Rlzd_{ano_atual}_Disp"] = _build_value_disp(tbl_hist_data[f"Rlzd_{ano_atual}"], COLOR_2026, BG_2026)
    tbl_hist_data[f"Var_{ano_atual}_Disp"] = _build_var_text_disp(tbl_hist_data[f"Var_{ano_atual}"])
    tbl_hist_data[f"Rlzd_{ano_projecao_proxima}_Disp"] = _build_value_disp(tbl_hist_data[f"Rlzd_{ano_projecao_proxima}"], COLOR_2027, BG_2027)
    tbl_hist_data[f"Var_{ano_projecao_proxima}_Disp"] = _build_var_text_disp(tbl_hist_data[f"Var_{ano_projecao_proxima}"])

    for year_suf, color_hex, bg_hex in [(ano_atual_str, COLOR_2026, BG_2026), (ano_prox_str, COLOR_2027, BG_2027)]:
        flags = tbl_hist_data[f"_eh_realizado_{year_suf}"]
        tbl_hist_data[f"Analitica_{year_suf}_Disp"] = _build_value_disp(tbl_hist_data[f"Analitica_{year_suf}"], color_hex, bg_hex, flags)
        tbl_hist_data[f"Mercado_{year_suf}_Disp"] = _build_value_disp(tbl_hist_data[f"Mercado_{year_suf}"], color_hex, bg_hex, flags)
        tbl_hist_data[f"Ajustada_{year_suf}_Disp"] = _build_value_disp(tbl_hist_data[f"Ajustada_{year_suf}"], color_hex, bg_hex, flags)
        tbl_hist_data[f"Var_Ana_{year_suf}_Disp"] = _build_var_text_disp(tbl_hist_data[f"Var_Ana_{year_suf}"])
        tbl_hist_data[f"Var_Mer_{year_suf}_Disp"] = _build_var_text_disp(tbl_hist_data[f"Var_Mer_{year_suf}"])
        tbl_hist_data[f"Var_Ajs_{year_suf}_Disp"] = _build_var_text_disp(tbl_hist_data[f"Var_Ajs_{year_suf}"])
        tbl_hist_data[f"Ajuste_{year_suf}_Disp"] = [
            (
                f'<span style="background:{"#ecfdf5" if float(v) >= 0 else "#fef2f2"};'
                f'border:1px solid {"#86efac" if float(v) >= 0 else "#fca5a5"};'
                f'padding:2px 6px;border-radius:4px;color:{"#059669" if float(v) >= 0 else "#dc2626"};font-weight:700;">'
                f'{("+" if float(v) >= 0 else "") + fmt_br(float(v), 0)}</span>'
            )
            for v in tbl_hist_data[f"Ajuste_{year_suf}"]
        ]

    # Colunas que devem permanecer somente leitura (restauradas se o usuário editar)
    protected_non_ajuste_cols = ["Mes"]  # Sempre protege a coluna de mês
    if ano_realizado_ultimo is not None:
        protected_non_ajuste_cols.extend([
            f"Rlzd_{ano_realizado_ultimo}", f"Var_{ano_realizado_ultimo}",
            f"Rlzd_{ano_realizado_ultimo}_Disp", f"Var_{ano_realizado_ultimo}_Disp"
        ])

    for year_suf in [ano_atual_str, ano_prox_str]:
        protected_non_ajuste_cols.extend([
            f"Rlzd_{year_suf}", f"Var_{year_suf}",
            f"Analitica_{year_suf}", f"Var_Ana_{year_suf}",
            f"Mercado_{year_suf}", f"Var_Mer_{year_suf}",
            f"Rlzd_{year_suf}_Disp", f"Var_{year_suf}_Disp",
            f"Analitica_{year_suf}_Disp", f"Var_Ana_{year_suf}_Disp",
            f"Mercado_{year_suf}_Disp", f"Var_Mer_{year_suf}_Disp"
        ])

    for col in protected_non_ajuste_cols:
        if col in tbl_hist_data:
            tbl_hist_data[f"_orig_{col}"] = list(tbl_hist_data[col])

    tbl_hist_src = ColumnDataSource(tbl_hist_data)

    # Template simples para renderizar HTML previamente formatado
    SIMPLE_HTML_TMPL = """<%= value %>"""

    # Construir colunas para série histórica
    columns_hist = [
        TableColumn(field="Mes", title="Mês", formatter=StringFormatter(text_color="#0b1320"), sortable=False)
    ]
    
    # ============ APENAS ÚLTIMO ANO REALIZADO (2025) ============
    if ano_realizado_ultimo is not None:
        columns_hist.append(TableColumn(
            field=f"Rlzd_{ano_realizado_ultimo}_Disp", title=f"RLZD {ano_realizado_ultimo}",
            formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)
        ))
        columns_hist.append(TableColumn(
            field=f"Var_{ano_realizado_ultimo}_Disp", title=f"VAR. % {ano_realizado_ultimo}",
            formatter=HTMLTemplateFormatter(template="<%= value %>")
        ))
    
    # ============ REALIZADO DO ANO ATUAL (2026) ============
    columns_hist.extend([
        TableColumn(field=f"Rlzd_{ano_atual}_Disp", title=f"RLZD {ano_atual}",
            formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Var_{ano_atual}_Disp", title=f"VAR. % {ano_atual}",
            formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL))
    ])
    
    # ============ PROJEÇÕES 2026 ============
    # Separador visual
    columns_hist.extend([
        TableColumn(field=f"Analitica_{ano_atual_str}_Disp", title=f"🟧 {ano_atual} ANALÍT", formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Var_Ana_{ano_atual_str}_Disp", title="VAR % ANAL", formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Mercado_{ano_atual_str}_Disp", title="MERCADO", formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Var_Mer_{ano_atual_str}_Disp", title="VAR % MERC", formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Ajustada_{ano_atual_str}_Disp", title="AJUSTADA", formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Var_Ajs_{ano_atual_str}_Disp", title="VAR % AJS", formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Ajuste_{ano_atual_str}", title="✨ AJUSTE (+/-)", formatter=HTMLTemplateFormatter(template='\
            <%\
            function fmtShortSigned(val){\
                if (val == null || isNaN(val)) return "—";\
                const n = Number(val);\
                const s = n >= 0 ? "+" : "";\
                const a = Math.abs(n);\
                if (a >= 1e9) return s + (n/1e9).toFixed(1) + "B";\
                if (a >= 1e6) return s + (n/1e6).toFixed(1) + "M";\
                return s + n.toLocaleString("pt-BR", {maximumFractionDigits:0});\
            }\
            %>\
            <span style="background:<%= value >= 0 ? "#ecfdf5" : "#fef2f2" %>;border:1px solid <%= value >= 0 ? "#86efac" : "#fca5a5" %>;padding:2px 6px;border-radius:4px;color:<%= value >= 0 ? "#059669" : "#dc2626" %>;font-weight:700;"><%= fmtShortSigned(value) %></span>'), editor=NumberEditor(step=1))
    ])
    
    # ============ PROJEÇÕES 2027 ============
    columns_hist.extend([
        TableColumn(field=f"Rlzd_{ano_projecao_proxima}_Disp", title=f"RLZD {ano_projecao_proxima}",
            formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Var_{ano_projecao_proxima}_Disp", title=f"VAR. % {ano_projecao_proxima}",
            formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Analitica_{ano_prox_str}_Disp", title=f"🟦 {ano_projecao_proxima} ANALÍT", formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Var_Ana_{ano_prox_str}_Disp", title="VAR % ANAL", formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Mercado_{ano_prox_str}_Disp", title="MERCADO", formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Var_Mer_{ano_prox_str}_Disp", title="VAR % MERC", formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Ajustada_{ano_prox_str}_Disp", title="AJUSTADA", formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Var_Ajs_{ano_prox_str}_Disp", title="VAR % AJS", formatter=HTMLTemplateFormatter(template=SIMPLE_HTML_TMPL)),
        TableColumn(field=f"Ajuste_{ano_prox_str}", title="✨ AJUSTE (+/-)", formatter=HTMLTemplateFormatter(template='\
            <%\
            function fmtShortSigned(val){\
                if (val == null || isNaN(val)) return "—";\
                const n = Number(val);\
                const s = n >= 0 ? "+" : "";\
                const a = Math.abs(n);\
                if (a >= 1e9) return s + (n/1e9).toFixed(1) + "B";\
                if (a >= 1e6) return s + (n/1e6).toFixed(1) + "M";\
                return s + n.toLocaleString("pt-BR", {maximumFractionDigits:0});\
            }\
            %>\
            <span style="background:<%= value >= 0 ? "#ecfdf5" : "#fef2f2" %>;border:1px solid <%= value >= 0 ? "#86efac" : "#fca5a5" %>;padding:2px 6px;border-radius:4px;color:<%= value >= 0 ? "#059669" : "#dc2626" %>;font-weight:700;"><%= fmtShortSigned(value) %></span>'), editor=NumberEditor(step=1))
    ])

    tbl_hist = DataTable(
        source=tbl_hist_src,
        columns=columns_hist,
        index_position=None,
        sizing_mode="stretch_width",  # Expande para ocupar toda a largura disponível   
        width=10000,  # Mantém fallback, mas stretched width é prioritário
        height=500,  # Altura suficiente para 14 linhas sem gerar gap extra
        editable=True,
        reorderable=False,
        stylesheets=[make_stylesheet()],
    )

    # Callback da tabela histórica: edição de AJUSTE -> recalcula AJUSTADA/VAR e sincroniza gráfico
    cb_hist_sync = CustomJS(
        args=dict(
            tbl=tbl_hist_src,
            src=src_ajs,
            mes_atual=mes_atual,
            ano_atual=ano_atual,
            ano_prox=ano_projecao_proxima,
            protected_cols=protected_non_ajuste_cols,
            storage_key=f"bokeh_update_sim_bokeh_{combo}",
        ),
        code="""
        const d = tbl.data;

        function triggerSafeSync() {
            try {
                const parentWindow = window.parent;
                parentWindow.clearInterval(parentWindow.__uanHistSyncTimer);
                let attempts = 0;
                const maxAttempts = 25;

                const tryClick = () => {
                    attempts += 1;
                    try {
                        const buttons = Array.from(parentWindow.document.querySelectorAll('button'));
                        const syncBtn = buttons.find((btn) => {
                            const label = (btn.textContent || '').replace(/\\s+/g, ' ').trim();
                            return label.includes('Sincronizar');
                        });

                        if (syncBtn) {
                            try {
                                parentWindow.localStorage.setItem(storage_key + '_sync_probe', JSON.stringify({
                                    ts: Date.now(),
                                    status: 'found_and_click',
                                    attempt: attempts,
                                    label: (syncBtn.textContent || '').trim()
                                }));
                            } catch (_e) {}

                            try {
                                syncBtn.dispatchEvent(new MouseEvent('click', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: parentWindow
                                }));
                                syncBtn.click();
                            } catch (_clickErr) {
                                try {
                                    syncBtn.click();
                                } catch (_e) {}
                            }

                            parentWindow.clearInterval(parentWindow.__uanHistSyncTimer);
                            console.log('[HIST->SYNC] Botão Sincronizar acionado automaticamente');
                            return;
                        }

                        try {
                            parentWindow.localStorage.setItem(storage_key + '_sync_probe', JSON.stringify({
                                ts: Date.now(),
                                status: 'not_found',
                                attempt: attempts
                            }));
                        } catch (_e) {}

                        if (attempts >= maxAttempts) {
                            parentWindow.clearInterval(parentWindow.__uanHistSyncTimer);
                            console.warn('[HIST->SYNC] Botão Sincronizar não encontrado após várias tentativas');
                        }
                    } catch (err) {
                        try {
                            parentWindow.localStorage.setItem(storage_key + '_sync_probe', JSON.stringify({
                                ts: Date.now(),
                                status: 'query_error',
                                attempt: attempts,
                                error: String(err)
                            }));
                        } catch (_e) {}
                        if (attempts >= maxAttempts) {
                            parentWindow.clearInterval(parentWindow.__uanHistSyncTimer);
                        }
                        console.warn('[HIST->SYNC] Falha ao acionar sincronização automática:', err);
                    }
                };

                tryClick();
                parentWindow.__uanHistSyncTimer = parentWindow.setInterval(tryClick, 120);
            } catch (err) {
                console.warn('[HIST->SYNC] Não foi possível agendar sincronização automática:', err);
            }
        }

        const allowedCols = new Set([`Ajuste_${String(ano_atual)}`, `Ajuste_${String(ano_prox)}`]);
        const protectedCols = protected_cols || [];

        // Restaura INCONDICIONALMENTE todas as colunas protegidas para seus valores originais.
        // Isso garante que o usuário não possa editar Mes, Rlzd, Analitica, etc.
        for (let ci = 0; ci < protectedCols.length; ci++) {
            const col = protectedCols[ci];
            const origKey = '_orig_' + col;
            if (d[origKey]) {
                for (let ri = 0; ri < d[col].length; ri++) {
                    d[col][ri] = d[origKey][ri];
                }
            }
        }

        function safe(v) {
            const n = Number(v);
            return Number.isFinite(n) ? n : 0;
        }
        function avg(arr) {
            if (!arr || arr.length === 0) return 0;
            let s = 0;
            for (let i = 0; i < arr.length; i++) s += safe(arr[i]);
            return s / arr.length;
        }
        function varArray(values) {
            const out = new Array(values.length).fill(0);
            for (let i = 1; i < values.length; i++) {
                const prev = safe(values[i - 1]);
                const cur = safe(values[i]);
                out[i] = prev === 0 ? 0 : (cur - prev) / Math.abs(prev);
            }
            return out;
        }
        function fmtShort(v) {
            const vv = safe(v);
            const a = Math.abs(vv);
            if (a >= 1e9) return (vv / 1e9).toFixed(1) + 'B';
            if (a >= 1e6) return (vv / 1e6).toFixed(1) + 'M';
            return Math.round(vv).toLocaleString('pt-BR');
        }
        function valueDisp(v, color, bg, isReal) {
            const txt = fmtShort(v);
            if (isReal) {
                return `<span style="background:#fef08a;padding:1px 5px;border-radius:3px;font-weight:700;color:#92400e;">${txt}</span>`;
            }
            return `<span style="background:${bg};padding:1px 5px;border-radius:3px;color:${color};font-weight:700;">${txt}</span>`;
        }
        function varDisp(v, rowIndex) {
            const vv = safe(v);
            const color = vv > 0 ? '#059669' : (vv < 0 ? '#dc2626' : '#334155');
            let txt = `${vv >= 0 ? '+' : ''}${(vv * 100).toFixed(2)}%`;
            if (rowIndex === 13) txt = vv > 0 ? '▲' : (vv < 0 ? '▼' : '•');
            return `<span style="color:${color};font-weight:700;">${txt}</span>`;
        }

        const configs = {
            [String(ano_atual)]: { color: '#b45309', bg: '#fff7ed' },
            [String(ano_prox)]: { color: '#0369a1', bg: '#f0f9ff' }
        };

        const startAbs = (Number(ano_atual) * 12) + (Number(mes_atual) - 1);
        let srcChanged = false;

        // Cria NOVOS arrays para y e y_br (evita mutação in-place que Bokeh não detecta)
        const newY   = src.data['y'].slice();
        const newYBr = (src.data['y_br'] || src.data['y']).map(v => String(v));

        for (const y of [String(ano_atual), String(ano_prox)]) {
            const kAna = `Analitica_${y}`;
            const kAjs = `Ajustada_${y}`;
            const kAjt = `Ajuste_${y}`;
            const kVarAjs = `Var_Ajs_${y}`;
            const kAjsDisp = `Ajustada_${y}_Disp`;
            const kVarAjsDisp = `Var_Ajs_${y}_Disp`;
            const kAjtDisp = `Ajuste_${y}_Disp`;
            const kFlags = `_eh_realizado_${y}`;

            for (let i = 0; i < 12; i++) {
                d[kAjt][i] = safe(d[kAjt][i]);
                d[kAjs][i] = safe(d[kAna][i]) + d[kAjt][i];

                const absIdx = (Number(y) * 12) + i;
                const chartIdx = absIdx - startAbs;
                if (chartIdx >= 0 && chartIdx < 12) {
                    newY[chartIdx]   = d[kAjs][i];
                    newYBr[chartIdx] = d[kAjs][i].toLocaleString('pt-BR');
                    srcChanged = true;
                }
            }

            const varVals = varArray(d[kAjs].slice(0, 12));
            for (let i = 0; i < 12; i++) d[kVarAjs][i] = varVals[i];

            d[kAjs][12] = avg(d[kAjs].slice(0, 12));
            d[kVarAjs][12] = avg(d[kVarAjs].slice(0, 12));
            d[kAjt][12] = avg(d[kAjt].slice(0, 12));

            d[kAjs][13] = safe(d[kAjs][11]) - safe(d[kAjs][0]);
            d[kVarAjs][13] = d[kAjs][13] > 0 ? 1 : (d[kAjs][13] < 0 ? -1 : 0);
            d[kAjt][13] = safe(d[kAjt][11]) - safe(d[kAjt][0]);

            for (let i = 0; i < d[kAjs].length; i++) {
                const isReal = i < 12 ? Boolean(d[kFlags][i]) : false;
                d[kAjsDisp][i] = valueDisp(d[kAjs][i], configs[y].color, configs[y].bg, isReal);
                d[kVarAjsDisp][i] = varDisp(d[kVarAjs][i], i);
                const aj = safe(d[kAjt][i]);
                d[kAjtDisp][i] = `<span style="background:${aj >= 0 ? '#ecfdf5' : '#fef2f2'};border:1px solid ${aj >= 0 ? '#86efac' : '#fca5a5'};padding:2px 6px;border-radius:4px;color:${aj >= 0 ? '#059669' : '#dc2626'};font-weight:700;">${aj >= 0 ? '+' : ''}${fmtShort(aj)}</span>`;
            }
        }

        // Atribui novos arrays → Bokeh detecta mudança de referência → re-renderiza
        if (srcChanged) {
            src.data = Object.assign({}, src.data, { y: newY, y_br: newYBr });
            src.change.emit();
        }
        
        // SEMPRE escrever localStorage com novo timestamp para cada edição (patching event)
        // Mesmo que srcChanged=false, o timestamp precisa ser atualizado para Python detectar a mudança
        try {
            const now = Date.now();
            window.parent.localStorage.setItem(storage_key, JSON.stringify(newY));
            window.parent.localStorage.setItem(storage_key + '_timestamp', now.toString());
            window.parent.localStorage.setItem(storage_key + '_probe', JSON.stringify({
                ts: now,
                srcChanged: srcChanged,
                y0: newY[0],
                y6: newY[6],
                y11: newY[11],
                ajuste_2026: d['Ajuste_2026'],
                ajuste_2027: d['Ajuste_2027']
            }));
            triggerSafeSync();
            console.log('[HIST->SYNC] localStorage persistido com timestamp novo (srcChanged=' + srcChanged + ')');
        } catch(e) {
            console.warn('[HIST->SYNC] Falha ao gravar localStorage:', e);
        }
        tbl.change.emit();
    """
    )
    tbl_hist_src.js_on_change("patching", cb_hist_sync)
    # NOTA: NÃO registrar js_on_change("data") aqui — causaria loop:
    # cb_hist_sync modifica tbl.data → emite "data" → cb_hist_sync dispara novamente.
    
    # CSS apenas para estabilidade visual da barra horizontal
    st.markdown("""
    <style>
        /* Scrollbar apenas horizontal */
        .bk-root .bk-data-table::-webkit-scrollbar {
            height: 10px;
            width: 0px;
        }
        
        .bk-root .bk-data-table::-webkit-scrollbar-track {
            background: #f1f5f9;
        }
        
        .bk-root .bk-data-table::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 5px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    hist_title_div = Div(
        text="""
        <div style='margin: 16px 0 8px 0; padding-top: 14px; border-top: 2px solid #e2e8f0;
                    font-size: 1.1rem; font-weight: 700; color: #0c3a66;'>
            📊 SÉRIE HISTÓRICA • Realizado vs Projeções
        </div>
        """,
        sizing_mode="stretch_width"
    )

    layout_principal = column(
        layout_topo,
        hist_title_div,
        tbl_hist,
        sizing_mode="stretch_width",
    )

    bokeh_editable(
        layout_principal,
        height=1500,
        key=f"sim_bokeh_{combo}",
        enable_storage_monitor=False,
    )

    st.markdown("<h2 class='uan-sec' style='margin:8px 0 4px 0;padding:4px 0;font-size:1.2rem;border-top:1px solid #e2e8f0;'>🗂️ Análises por Categoria</h2>", unsafe_allow_html=True)
    
    # Cards usam o ano da simulação corrente.
    ano_cards = int(ano_proj or 0)
    agreg_cards = _agregados_por_categoria(
        df_upload,
        cliente,
        ano_cards,
        mascarar_zeros_finais=MASCARAR_ZEROS_FINAIS,
    )

    # Gráficos de barras com filtro explícito por ano.
    dff_anos = _ensure_cli_n(df_upload.copy())
    if cliente and cliente != "Todos":
        dff_anos = dff_anos[dff_anos["CLI_N"] == _norm_txt(cliente)]
    if "ANO_NUM" not in dff_anos.columns:
        dff_anos["ANO_NUM"] = pd.to_numeric(dff_anos.get("ANO", 0), errors="coerce").fillna(0).astype(int)

    anos_disponiveis_barras = sorted(
        [int(a) for a in dff_anos["ANO_NUM"].dropna().astype(int).unique().tolist() if int(a) >= 2022]
    )
    if not anos_disponiveis_barras:
        anos_disponiveis_barras = [ano_cards] if ano_cards else [2025]

    ano_barras_default = st.session_state.get("sim_ano_barras", ano_cards)
    if ano_barras_default not in anos_disponiveis_barras:
        ano_barras_default = anos_disponiveis_barras[-1]

    ano_barras = st.session_state.get("sim_ano_barras", ano_barras_default)
    if ano_barras not in anos_disponiveis_barras:
        ano_barras = ano_barras_default
    
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
    def _aplicar_diff_categoria(agreg_dict, ano_base):
        if not agreg_dict or categoria not in agreg_dict:
            return
        # O vetor ajustada em memória corresponde ao ano de simulação corrente.
        if int(ano_base or 0) != int(ano_cards or 0):
            return

        serie_prod_orig = _carregar_ajustada_produto(df_upload, cliente, categoria, produto, ano_proj) or analitica[:]
        serie_prod_orig = np.array(_safe_array_12(serie_prod_orig), dtype=float)
        serie_drag = np.array(_safe_array_12(ajustada), dtype=float)
        
        diff = serie_drag - serie_prod_orig
        serie_cat_ajs = np.array(_safe_array_12(agreg_dict[categoria].get("ajs", [])), dtype=float)
        agreg_dict[categoria]["ajs"] = list(serie_cat_ajs + diff)

    _aplicar_diff_categoria(agreg_cards, ano_cards)
    
    agreg_base_ordem = agreg_cards if agreg_cards else agreg_barras
    if agreg_base_ordem:
        principais = ["CAPTAÇÕES", "OPERAÇÕES CRÉDITO", "SERVIÇOS", "CRÉDITO"]
        ordem = [c for c in principais if c in agreg_base_ordem] + [c for c in agreg_base_ordem.keys() if c not in principais]
        ordem = ordem[:3]

        # ===== LINHA 1: Cards das categorias =====
        cols_cards = st.columns(3, gap="small")
        for i, cat in enumerate(ordem):
            with cols_cards[i]:
                card_data = agreg_cards.get(cat) or agreg_base_ordem.get(cat, {})
                card_html = _cards_categoria_html(cat, card_data)
                st_components.html(card_html, height=260, scrolling=False)

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        
        # Layout compacto do filtro de ano
        col_filter_label, col_filter_select, col_filter_spacer = st.columns([0.45, 1.4, 4.15])
        
        with col_filter_label:
            st.markdown(
                "<div style='padding:8px 0 8px 0;font-size:0.9rem;color:#475569;font-weight:600;'>📅 Ano:</div>",
                unsafe_allow_html=True
            )
        
        with col_filter_select:
            ano_barras = st.selectbox(
                "Ano - Barras",
                options=anos_disponiveis_barras,
                index=anos_disponiveis_barras.index(ano_barras),
                key="sim_ano_barras",
                label_visibility="collapsed",
            )
        
        st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)

        agreg_barras = _agregados_por_categoria(
            df_upload,
            cliente,
            int(ano_barras),
            mascarar_zeros_finais=MASCARAR_ZEROS_FINAIS,
        )
        _aplicar_diff_categoria(agreg_barras, int(ano_barras))

        # ===== LINHA 2: Gráficos de barras =====
        cols_barras = st.columns(3, gap="small")
        for i, cat in enumerate(ordem):
            with cols_barras[i]:
                barras_data = agreg_barras.get(cat) or agreg_base_ordem.get(cat, {})
                barras = _grafico_barras_categoria(cat, barras_data, make_stylesheet(), ano=ano_barras)
                streamlit_bokeh(barras, use_container_width=True, key=f"bar_{cat}_{combo}_{ano_barras}")

        # ===== LINHA 3: Gráficos de pizza =====
        st.markdown("<h4 style='margin:0.5rem 0 0.25rem 0;'>🍩 Share por Tipo de Projeção</h4>", unsafe_allow_html=True)
        cols_pizza = st.columns(3, gap="small")
        tipos_projecao = [("ana", "Proj. Analítica"), ("mer", "Proj. Mercado"), ("ajs", "Proj. Ajustada")]
        
        for i, (tipo, nome) in enumerate(tipos_projecao):
            with cols_pizza[i]:
                pizza = _grafico_pizza_share_por_projecao(tipo, agreg_cards, make_stylesheet())
                streamlit_bokeh(pizza, use_container_width=True, key=f"pizza_{tipo}_{combo}")