"""
Página de DRE Gerencial (Demonstrativo de Resultado Gerencial)
Permite simular e editar variáveis da DRE com layout mês-a-mês
Suporta metodologias de cálculo automáticas

# v3.6.1 - 2026-06-02: Corrigido CSS headers DRE e padding sidebar
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import sys
import os
import json
import re
import ast
import html
from urllib.parse import quote, unquote
import operator as op
from datetime import datetime
from copy import deepcopy
from typing import Union, Dict, List, Optional

# Importar utilitários
from utils_ext.css import make_stylesheet
from utils_ext.formatters import fmt_br
from utils_ext.series import (
    _norm_txt, _mes_to_num, _variacao_mensal, _ensure_cli_n, _ensure_normalized_columns,
    _normalizar_codigo_produto, _extrair_descricao_produto, _normalizar_tokens_produto, _produto_eh_equivalente
)
from utils_ext.constants import (
    MESES_FULL, MESES_NUM, MESES_ABR, MESES_ABR_LIST, COR_ANALITICA, COR_MERCADO, 
    COR_AJUSTADA, COR_RLZD_BASE, CAT_COLORS
)
from utils_ext.calc_functions import (
    FUNCOES_NATIVAS, DESCRICOES_FUNCOES, EXEMPLOS_FUNCOES,
    evaluar_funcao_em_formula, obter_documentacao_funcoes,
    _preparar_contexto_com_indices
)
from utils_ext.icons import get_icon, render_icon_header, render_section_divider, render_info_box, render_page_header

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_manager import (
    get_dados_upload,
    carregar_curva_ajustada,
    get_base_dre_ativa,
    get_origem_base_dre_ativa,
    init_data_state,
)
from services.aggregations import _carregar_ajustada_produto

# ── Backend DRE (persistência de simulações por usuário) ──────────────────────
_backend_path = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)
try:
    from database import (
        salvar_simulacao_dre as _salvar_simulacao_dre_backend,
        carregar_simulacao_dre as _carregar_simulacao_dre_backend,
    )
    _DRE_BACKEND_OK = True
except Exception as _e:
    print(f"[DRE] Backend de persistência DRE não carregado: {_e}")
    _DRE_BACKEND_OK = False


try:
    from st_keyup import st_keyup
except Exception:
    st_keyup = None


_DIALOG_DECORATOR = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
if _DIALOG_DECORATOR is None:
    def _DIALOG_DECORATOR(*_args, **_kwargs):
        def _decorator(func):
            return func
        return _decorator


DEBUG_DRE_LOGS = False


def _log_dre(msg: str):
    if DEBUG_DRE_LOGS:
        print(msg)


def _normalizar_formula_usuario(formula: str) -> str:
    """Normaliza entrada da fórmula (ex: decimal com vírgula)."""
    if not formula:
        return ""
    formula = formula.strip()
    formula = re.sub(r"(?i)M[ÉE]DIA\.INTERNA", "MEDIA_INTERNA", formula)
    formula = re.sub(r"(?i)TRIMMEAN", "MEDIA_INTERNA", formula)
    # Converte somente vírgula decimal entre dígitos: 0,05 -> 0.05
    formula = re.sub(r"(?<=\d),(?=\d)", ".", formula)
    return formula


def _extrair_tokens_formula(formula: str) -> list:
    if not formula:
        return []
    return list(dict.fromkeys(re.findall(r"\b([A-Z][A-Z0-9_]*)\b", formula.upper())))


def _normalizar_nome_metodologia_var(nome: str) -> str:
    """Normaliza nome de metodologia para uso como variável em fórmula (ex: 'Minha Met' → 'MINHA_MET')."""
    return re.sub(r'[^A-Za-z0-9]', '_', nome).upper()


def _resolver_series_metodologias() -> dict:
    """
    Retorna séries de 12 valores de cada metodologia já aplicada ao menos uma vez.
    Viabiliza encadeamento: fórmulas podem referenciar o nome de outra metodologia como variável.
    A série é gravada em 'serie_computada' no momento em que a metodologia é aplicada.
    NOTA: só disponível após a metodologia ter sido aplicada pelo menos uma vez.
    """
    metodologias = st.session_state.get("dre_metodologias", {})
    ano_referencia = int(
        st.session_state.get(
            "dre_ano_filter",
            st.session_state.get("dre_filtros", {}).get("ano", datetime.now().year),
        )
    )
    series = {}
    for met_nome, met_dados in metodologias.items():
        serie = met_dados.get("serie_computada")
        if isinstance(serie, list) and len(serie) == 12:
            nome_var = _normalizar_nome_metodologia_var(met_nome)
            series[nome_var] = {
                "valores": [float(v) for v in serie],
                "tipo": "metodologia",
                "descricao": f"[Metodologia] {met_nome}",
                "eh_negrito": False,
                "formula": None,
                "metodologia": None,
                "serie_historica": [
                    {"ano": ano_referencia, "mes": idx + 1, "valor": float(v)}
                    for idx, v in enumerate(serie[:12])
                ],
            }
    return series


def _agrupar_serie_historica(df_base: pd.DataFrame, col_valor: str) -> list:
    """Agrupa uma base por ano/mês e retorna a série histórica ordenada."""
    if df_base is None or df_base.empty or col_valor not in df_base.columns:
        return []

    vals = _normalizar_valor_monetario_series(df_base[col_valor])
    hist = (
        pd.DataFrame(
            {
                "ANO_NUM": pd.to_numeric(df_base["ANO_NUM"], errors="coerce"),
                "MES_NUM": pd.to_numeric(df_base["MES_NUM"], errors="coerce"),
                "VAL": vals,
            }
        )
        .dropna(subset=["ANO_NUM", "MES_NUM"])
    )

    if hist.empty:
        return []

    hist = hist[hist["MES_NUM"].between(1, 12)]
    grp = (
        hist.groupby(["ANO_NUM", "MES_NUM"], as_index=False)["VAL"]
        .sum()
        .sort_values(["ANO_NUM", "MES_NUM"])
    )

    return [
        {"ano": int(row.ANO_NUM), "mes": int(row.MES_NUM), "valor": float(row.VAL)}
        for row in grp.itertuples(index=False)
    ]


def _mesclar_series_historicas(*series: Optional[list]) -> list:
    """Mescla múltiplas séries históricas mantendo o último valor por ano/mês."""
    mapa = {}
    for serie in series:
        for item in serie or []:
            if not isinstance(item, dict):
                continue
            try:
                chave = (int(item.get("ano")), int(item.get("mes")))
                valor = float(item.get("valor") or 0.0)
            except Exception:
                continue
            mapa[chave] = valor

    return [
        {"ano": ano, "mes": mes, "valor": valor}
        for (ano, mes), valor in sorted(mapa.items())
    ]


def _normalizar_flags_preenchimento(
    flags: Optional[list],
    valores: Optional[list] = None,
    mes_corte: int = 0,
    padrao_todos: bool = False,
) -> list:
    """Normaliza flags de preenchimento preservando zeros explicitamente informados."""
    if isinstance(flags, list) and len(flags) >= 12:
        return [bool(v) for v in flags[:12]]

    if padrao_todos:
        return [True] * 12

    valores = valores or [0.0] * 12
    flags_norm = [False] * 12
    for idx in range(12):
        if idx < int(mes_corte or 0):
            flags_norm[idx] = True
        else:
            try:
                flags_norm[idx] = abs(float(valores[idx] or 0.0)) > 0
            except Exception:
                flags_norm[idx] = False
    return flags_norm


def _mesclar_serie_historica_com_ano_corrente(
    serie_base: Optional[list],
    ano_referencia: int,
    linha_dados: Optional[dict],
) -> list:
    """Sobrescreve o ano corrente preservando vazio lógico vs zero explícito."""
    mapa = {}
    for item in serie_base or []:
        try:
            mapa[(int(item["ano"]), int(item["mes"]))] = float(item["valor"] or 0.0)
        except Exception:
            continue

    linha_dados = linha_dados or {}
    valores_ano_corrente = (linha_dados.get("valores") or [0.0] * 12)[:12]
    mes_corte = int(linha_dados.get("mes_corte", 0) or 0)

    if linha_dados.get("tipo") == "variavel":
        realizado = (linha_dados.get("realizado") or [0.0] * 12)[:12]
        projetado = (linha_dados.get("projetado") or [0.0] * 12)[:12]
        flags_proj = _normalizar_flags_preenchimento(
            linha_dados.get("projetado_preenchido"),
            valores=projetado,
            mes_corte=mes_corte,
        )

        for idx in range(12):
            mes = idx + 1
            if mes <= mes_corte:
                mapa[(int(ano_referencia), mes)] = float(realizado[idx] or 0.0)
            elif flags_proj[idx]:
                mapa[(int(ano_referencia), mes)] = float(projetado[idx] or 0.0)
            else:
                mapa.pop((int(ano_referencia), mes), None)
    else:
        flags = _normalizar_flags_preenchimento(
            linha_dados.get("valores_preenchidos"),
            valores=valores_ano_corrente,
            padrao_todos=True,
        )
        for idx, valor in enumerate(valores_ano_corrente, start=1):
            if flags[idx - 1]:
                mapa[(int(ano_referencia), idx)] = float(valor or 0.0)

    return [
        {"ano": ano, "mes": mes, "valor": valor}
        for (ano, mes), valor in sorted(mapa.items())
    ]


def _serie_historica_por_codigo(dff: pd.DataFrame, codigo: str) -> list:
    """Retorna série histórica multi-ano para um código da TD_DRE."""
    if dff is None or dff.empty or "CD_CPNT_RSTD" not in dff.columns:
        return []
    if "CURVA_REALIZADO" not in dff.columns:
        return []

    dff_com_componente = dff[dff["CD_CPNT_RSTD"].notna()]
    df_comp = dff_com_componente[dff_com_componente["CD_CPNT_RSTD"].astype(str).str.upper() == str(codigo).upper()]
    df_comp = df_comp[df_comp["CURVA_REALIZADO"].notna() & (df_comp["CURVA_REALIZADO"] != 0)]
    return _agrupar_serie_historica(df_comp, "CURVA_REALIZADO")


def _serie_historica_por_tip_td(dff: pd.DataFrame, codigo: str) -> list:
    """Retorna série histórica multi-ano a partir da guia DADOS por TIP_TD."""
    if dff is None or dff.empty or "TIP_TD" not in dff.columns:
        return []

    col_valor = "CURVA_REALIZADO" if "CURVA_REALIZADO" in dff.columns else None
    if not col_valor:
        return []

    df_comp = dff[dff["TIP_TD"].astype(str).str.upper() == str(codigo).upper()]
    return _agrupar_serie_historica(df_comp, col_valor)


def _obter_series_historicas_contexto() -> dict:
    """Monta e cacheia séries históricas reais para o contexto atual da DRE."""
    filtros = st.session_state.get("dre_filtros", {})
    cliente = filtros.get("cliente", "Todos")
    categoria = filtros.get("categoria", "")
    produto = filtros.get("produto", "")
    cache_key = (
        str(get_origem_base_dre_ativa()),
        str(cliente),
        str(categoria),
        str(produto),
    )

    if st.session_state.get("_dre_historico_cache_key") == cache_key:
        return st.session_state.get("_dre_historico_cache_val", {})

    dff_hist = _filtrar_base_dre(cliente=cliente, categoria=categoria, produto=produto, ano=None)
    series_historicas = {}

    for linha in ESTRUTURA_DRE:
        if linha.tipo == "variavel":
            series_historicas[linha.codigo] = _serie_historica_por_codigo(dff_hist, linha.codigo)

    for codigo in ("TD21", "TD62"):
        series_historicas[codigo] = _serie_historica_por_tip_td(dff_hist, codigo)

    st.session_state["_dre_historico_cache_key"] = cache_key
    st.session_state["_dre_historico_cache_val"] = series_historicas
    return series_historicas


def _extrair_serie_historica_linha_persistida(
    linha_dados: Optional[dict],
    ano_referencia: int,
) -> list:
    """Converte uma linha persistida da DRE em série histórica explícita para um ano."""
    if not isinstance(linha_dados, dict):
        return []

    valores = list((linha_dados.get("valores") or [0.0] * 12)[:12])
    if len(valores) < 12:
        valores.extend([0.0] * (12 - len(valores)))

    flags = _normalizar_flags_preenchimento(
        linha_dados.get("valores_preenchidos"),
        valores=valores,
        mes_corte=int(linha_dados.get("mes_corte", 0) or 0),
        padrao_todos=linha_dados.get("tipo") != "variavel",
    )

    serie = []
    for idx, valor in enumerate(valores):
        if idx >= len(flags) or not flags[idx]:
            continue
        serie.append(
            {"ano": int(ano_referencia), "mes": idx + 1, "valor": float(valor or 0.0)}
        )
    return serie


def _obter_serie_historica_escopos_anteriores(codigo: str, ano_referencia: int) -> list:
    """Busca valores persistidos de anos anteriores do mesmo escopo para manter continuidade."""
    filtros = st.session_state.get("dre_filtros", {})
    cliente = str(filtros.get("cliente", "Todos"))
    categoria = str(filtros.get("categoria", ""))
    produto = str(filtros.get("produto", ""))
    if not codigo or not cliente:
        return []

    series_por_ano: Dict[int, list] = {}

    for combo_key, registro in (st.session_state.get("dre_dados_persistidos", {}) or {}).items():
        if not isinstance(registro, dict):
            continue
        partes = str(combo_key).split("::")
        if len(partes) < 4:
            continue
        cliente_key, categoria_key, produto_key, ano_key = partes[-4:]
        try:
            ano_key_int = int(ano_key)
        except Exception:
            continue
        if ano_key_int >= int(ano_referencia):
            continue
        if cliente_key != cliente or categoria_key != categoria or produto_key != produto:
            continue

        linha_salva = (registro.get("dre_dados", {}) or {}).get(codigo)
        serie = _extrair_serie_historica_linha_persistida(linha_salva, ano_key_int)
        if serie:
            series_por_ano[ano_key_int] = serie

    return _mesclar_series_historicas(*[series_por_ano[ano] for ano in sorted(series_por_ano)])


def _obter_contexto_formula(dre_dados: Dict[str, dict] = None) -> Dict[str, dict]:
    """Combina DRE principal com volumes (TD21/TD62) e metodologias encadeadas para validação e cálculo."""
    base_dre = dre_dados if dre_dados is not None else st.session_state.get("dre_dados", {})
    contexto = deepcopy(base_dre)
    ano_referencia = int(
        st.session_state.get(
            "dre_ano_filter",
            st.session_state.get("dre_filtros", {}).get("ano", datetime.now().year),
        )
    )
    series_historicas = _obter_series_historicas_contexto()

    for codigo, dados in st.session_state.get("dre_volumes_dados", {}).items():
        if codigo not in contexto:
            contexto[codigo] = {
                "descricao": dados.get("descricao", codigo),
                "tipo": dados.get("tipo", "variavel"),
                "formula": dados.get("formula"),
                "valores": (dados.get("valores") or [0.0] * 12),
                "valores_preenchidos": list(dados.get("valores_preenchidos") or [True] * 12),
                "eh_negrito": dados.get("eh_negrito", False),
                "metodologia": None,
            }

    # Injetar séries de metodologias já aplicadas para encadeamento de fórmulas
    for nome_var, dados_met in _resolver_series_metodologias().items():
        if nome_var not in contexto:
            contexto[nome_var] = dados_met

    for codigo, dados in list(contexto.items()):
        if not isinstance(dados, dict):
            continue
        _obter_flags_valores_linha(dados)
        serie_base = dados.get("serie_historica") or series_historicas.get(codigo, [])
        serie_anos_anteriores = _obter_serie_historica_escopos_anteriores(codigo, ano_referencia)
        dados["serie_historica"] = _mesclar_serie_historica_com_ano_corrente(
            _mesclar_series_historicas(serie_base, serie_anos_anteriores),
            ano_referencia,
            dados,
        )

    contexto["__meta__"] = {"ano_referencia": ano_referencia}

    return contexto


def _classificar_tokens_formula(formula: str, dre_dados: dict):
    """Classifica tokens em funções, variáveis DRE, índices, referências a metodologias e desconhecidos."""
    tokens = _extrair_tokens_formula(formula)
    funcoes = {"SOMA", "MEDIA", "MEDIA_INTERNA", "TRIMMEAN", "MINIMO", "MAXIMO", "DESVIO_PADRAO"}
    contexto_formula = _obter_contexto_formula(dre_dados)
    contexto = _preparar_contexto_com_indices(contexto_formula)
    vars_dre = set(contexto_formula.keys())

    # Nomes normalizados das metodologias para detectar encadeamento na fórmula
    nomes_met_vars = {
        _normalizar_nome_metodologia_var(n)
        for n in st.session_state.get("dre_metodologias", {}).keys()
    }

    tokens_funcoes = []
    tokens_dre = []
    tokens_indices = []
    tokens_invalidos = []
    tokens_met = []

    for t in tokens:
        if t in funcoes:
            tokens_funcoes.append(t)
        elif t in nomes_met_vars:
            # Referência a metodologia encadeada — prioridade sobre vars_dre para distinção visual
            tokens_met.append(t)
        elif t in vars_dre:
            tokens_dre.append(t)
        elif t in contexto:
            tokens_indices.append(t)
        else:
            tokens_invalidos.append(t)

    return {
        "funcoes": tokens_funcoes,
        "dre": tokens_dre,
        "indices": tokens_indices,
        "metodologias": tokens_met,
        "invalidos": tokens_invalidos,
    }


def _renderizar_tags_formula(classificacao: dict):
    """Renderiza tags visuais dos elementos encontrados na fórmula."""
    blocos = []
    for tok in classificacao.get("funcoes", []):
        blocos.append(f'<span style="display:inline-block;margin:2px 4px 2px 0;padding:2px 7px;border-radius:999px;background:#dbeafe;color:#1e3a8a;font-size:11px;font-weight:600;">fn:{tok}</span>')
    for tok in classificacao.get("dre", []):
        blocos.append(f'<span style="display:inline-block;margin:2px 4px 2px 0;padding:2px 7px;border-radius:999px;background:#dcfce7;color:#166534;font-size:11px;font-weight:600;">dre:{tok}</span>')
    for tok in classificacao.get("indices", []):
        blocos.append(f'<span style="display:inline-block;margin:2px 4px 2px 0;padding:2px 7px;border-radius:999px;background:#cffafe;color:#0e7490;font-size:11px;font-weight:600;">idx:{tok}</span>')
    for tok in classificacao.get("metodologias", []):
        blocos.append(f'<span style="display:inline-block;margin:2px 4px 2px 0;padding:2px 7px;border-radius:999px;background:#fef3c7;color:#92400e;font-size:11px;font-weight:600;">met:{tok}</span>')
    for tok in classificacao.get("invalidos", []):
        blocos.append(f'<span style="display:inline-block;margin:2px 4px 2px 0;padding:2px 7px;border-radius:999px;background:#fee2e2;color:#991b1b;font-size:11px;font-weight:700;">inv:{tok}</span>')

    if blocos:
        st.markdown("**Tags da fórmula:**", unsafe_allow_html=True)
        st.markdown("".join(blocos), unsafe_allow_html=True)


def _renderizar_formula_inline(formula: str, classificacao: dict):
    """Mostra preview inline da fórmula destacando tokens reconhecidos."""
    if not formula:
        return

    estilo = {
        "funcoes": "background:#dbeafe;color:#1e3a8a;",
        "dre": "background:#dcfce7;color:#166534;",
        "indices": "background:#cffafe;color:#0e7490;",
        "metodologias": "background:#fef3c7;color:#92400e;",
        "invalidos": "background:#fee2e2;color:#991b1b;",
    }

    tipos = {}
    for k in ["funcoes", "dre", "indices", "metodologias", "invalidos"]:
        for tok in classificacao.get(k, []):
            tipos[tok.upper()] = k

    formula_safe = html.escape(formula)

    def _sub_token(match):
        token_original = match.group(1)
        tipo = tipos.get(token_original.upper())
        token_safe = html.escape(token_original)
        if not tipo:
            return token_safe
        return (
            f'<span style="display:inline-block;padding:1px 5px;border-radius:6px;'
            f'font-weight:600;{estilo[tipo]}">{token_safe}</span>'
        )

    formula_destacada = re.sub(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", _sub_token, formula_safe)
    st.markdown("**Preview inline da fórmula:**", unsafe_allow_html=True)
    st.markdown(
        f'<div style="padding:8px 10px;border:1px solid #e5e7eb;border-radius:8px;'
        f'background:#f8fafc;font-family:monospace;font-size:14px;">{formula_destacada}</div>',
        unsafe_allow_html=True,
    )


def _aplicar_sugestao_formula_criar():
    """Completa o último token da fórmula com a sugestão selecionada."""
    escolhida = st.session_state.get("met_criar_sugestao", "")
    if not escolhida:
        return
    formula_atual = st.session_state.get("met_criar_formula", "")
    st.session_state["met_criar_formula"] = re.sub(
        r"([A-Za-z_][A-Za-z0-9_]*)$",
        escolhida,
        formula_atual or ""
    )
    st.session_state["met_formula_pending_keyup"] = st.session_state["met_criar_formula"]
    st.session_state["met_formula_widget_rev"] = st.session_state.get("met_formula_widget_rev", 0) + 1
    st.session_state["met_skip_keyup_sync"] = True


def _inserir_token_formula_criar(token: str):
    """Insere rapidamente um token na fórmula atual (modo autocomplete rápido)."""
    formula_atual = st.session_state.get("met_criar_formula", "")
    if not token:
        return

    if re.search(r"([A-Za-z_][A-Za-z0-9_]*)$", formula_atual or ""):
        nova_formula = re.sub(r"([A-Za-z_][A-Za-z0-9_]*)$", token, formula_atual or "")
    else:
        separador = ""
        if formula_atual and not formula_atual.endswith(("=", "(", "+", "-", "*", "/", ";", " ")):
            separador = " "
        nova_formula = f"{formula_atual}{separador}{token}"

    st.session_state["met_criar_formula"] = nova_formula
    st.session_state["met_formula_pending_keyup"] = nova_formula
    st.session_state["met_formula_widget_rev"] = st.session_state.get("met_formula_widget_rev", 0) + 1
    st.session_state["met_skip_keyup_sync"] = True


# ============================================================================
# FUNÇÃO AUXILIAR: UI DE SAZONALIDADE
# ============================================================================

def criar_interface_sazonalidade(rotulo_prefix: str = "", valor_padrao: Union[Dict, int, list, None] = None):
    """Cria interface de sazonalidade (Fixo vs Variável) retorna dict normalizado."""
    
    # Importar normalizar_sazonalidade
    from utils_ext.calc_functions import normalizar_sazonalidade
    
    # Normalizar valor_padrao (pode vir como dict, int, list, ou None)
    valor_padrao = normalizar_sazonalidade(valor_padrao)
    
    tipo_saz = valor_padrao.get("tipo", "NENHUM")
    
    season_icon = get_icon("seasonal", size="sm", color="#06b6d4")
    st.markdown(f"**{season_icon} Sazonalidade (opcional)** - Período fixo ou variável:", unsafe_allow_html=True)
    
    # Criar mapping de mês 1-12 para nome (MESES_FULL é lista, então usar índice)
    meses_dict = {i: MESES_FULL[i-1] for i in range(1, 13)}
    
    col_tipo, col_info = st.columns([2, 1])
    
    with col_tipo:
        tipo_selecionado = st.radio(
            "Tipo de Período:",
            ["Nenhum", "Período Fixo", "Período Variável"],
            index=0 if tipo_saz == "NENHUM" else (1 if tipo_saz == "FIXO" else 2),
            key=f"{rotulo_prefix}_tipo_saz_radio",
            horizontal=True
        )
    
    # Inicializar resultado
    sazonalidade_resultado = {"tipo": "NENHUM"}
    
    # ===== RENDERIZAR CAMPOS BASEADO NA SELEÇÃO =====
    
    if tipo_selecionado == "Período Fixo":
        st.divider()
        st.markdown("**Período Fixo** - Mesmo período para todos os meses")
        
        # Linha 1: Mês Inicial
        col_mes_i, col_ano_i = st.columns(2)
        with col_mes_i:
            mes_inicio = st.selectbox(
                "Mês Inicial:",
                list(range(1, 13)),
                format_func=lambda m: meses_dict.get(m, f"Mês {m}"),
                index=valor_padrao.get("mes_inicio", 1) - 1,
                key=f"{rotulo_prefix}_mes_inicio_fixo"
            )
        with col_ano_i:
            ano_inicio = st.number_input(
                "Ano Inicial:",
                value=int(valor_padrao.get("ano_inicio", 2024)),
                min_value=2000,
                max_value=2099,
                step=1,
                key=f"{rotulo_prefix}_ano_inicio_fixo"
            )
        
        # Linha 2: Mês Final
        col_mes_f, col_ano_f = st.columns(2)
        with col_mes_f:
            mes_fim = st.selectbox(
                "Mês Final:",
                list(range(1, 13)),
                format_func=lambda m: meses_dict.get(m, f"Mês {m}"),
                index=valor_padrao.get("mes_fim", 12) - 1,
                key=f"{rotulo_prefix}_mes_fim_fixo"
            )
        with col_ano_f:
            ano_fim = st.number_input(
                "Ano Final:",
                value=int(valor_padrao.get("ano_fim", 2024)),
                min_value=2000,
                max_value=2099,
                step=1,
                key=f"{rotulo_prefix}_ano_fim_fixo"
            )
        
        sazonalidade_resultado = {
            "tipo": "FIXO",
            "mes_inicio": int(mes_inicio),
            "mes_fim": int(mes_fim),
            "ano_inicio": int(ano_inicio),
            "ano_fim": int(ano_fim),
        }
    
    elif tipo_selecionado == "Período Variável":
        st.divider()
        st.markdown("**Período Variável** - Janela móvel que se adapta a cada mês")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            quantidade = st.number_input(
                "Quantidade:",
                value=valor_padrao.get("quantidade", 7),
                min_value=1,
                max_value=12,
                help="Número de meses (1-12)",
                key=f"{rotulo_prefix}_quantidade_var"
            )
        
        with col2:
            tipo_periodo = st.selectbox(
                "Tipo:",
                ["MES", "ANO"],
                index=0 if valor_padrao.get("tipo_periodo") == "MES" else 1,
                key=f"{rotulo_prefix}_tipo_periodo_var"
            )
        
        with col3:
            periodoLinha = st.selectbox(
                "Período:",
                ["ULTIMO", "PRIMEIRO"],
                index=0 if valor_padrao.get("periodoLinha") == "ULTIMO" else 1,
                key=f"{rotulo_prefix}_periodoLinha_var"
            )
        
        sazonalidade_resultado = {
            "tipo": "VARIAVEL",
            "quantidade": int(quantidade),
            "tipo_periodo": tipo_periodo,
            "periodoLinha": periodoLinha,
        }
    
    # ===== INFO SECTION =====
    with col_info:
        if tipo_selecionado == "Nenhum":
            st.info("ℹ️ Usa todos os\n12 meses")
        elif tipo_selecionado == "Período Fixo":
            mes_inicio = sazonalidade_resultado.get("mes_inicio", 1)
            mes_fim = sazonalidade_resultado.get("mes_fim", 12)
            ano_inicio = sazonalidade_resultado.get("ano_inicio", 2024)
            ano_fim = sazonalidade_resultado.get("ano_fim", 2024)
            mes_info = meses_dict.get(mes_inicio, "Jan")
            mes_inicio_nome = mes_info.split()[-1] if " " in mes_info else mes_info
            mes_info_fim = meses_dict.get(mes_fim, "Dez")
            mes_fim_nome = mes_info_fim.split()[-1] if " " in mes_info_fim else mes_info_fim
            
            # Display: "Jan 2024 - Dez 2024" ou "Jan 2024 - Fev 2025"
            if ano_inicio == ano_fim:
                info_text = f" {mes_inicio_nome}\n{ano_inicio}"
            else:
                info_text = f" {mes_inicio_nome}\n{ano_inicio}\n–\n{mes_fim_nome}\n{ano_fim}"
            st.info(info_text)
        else:  # Período Variável
            qtd = sazonalidade_resultado.get("quantidade", 1)
            periodo = sazonalidade_resultado.get("periodoLinha", "ULTIMO")
            st.info(f"{periodo}\n{qtd}\nMES" + ("ES" if qtd > 1 else ""))
    
    return sazonalidade_resultado


# ============================================================================
# ESTRUTURA DA DRE
# ============================================================================

class EstruturaLinehaDRE:
    """Representa uma linha da DRE (variável ou totalizador)"""
    
    def __init__(self, codigo: str, descricao: str, tipo: str = "variavel", 
                 formula: str = None, valores: list = None, eh_negrito: bool = False):
        """
        Args:
            codigo: Código único (ex: 'TD71', 'MFB')
            descricao: Descrição legível
            tipo: 'variavel' (editável) ou 'totalizador' (calculado)
            formula: Fórmula de cálculo (ex: '=TD71+TD72' ou '=0.05*TD21')
            valores: Lista com 12 valores mensais [jan...dez]
            eh_negrito: Se True, a linha fica em negrito (totalizador/agrupador)
        """
        self.codigo = codigo
        self.descricao = descricao
        self.tipo = tipo  # 'variavel', 'totalizador', 'agrupador'
        self.formula = formula
        self.valores = valores or [0.0] * 12
        self.eh_negrito = eh_negrito
        self.metodologia = None  # Referência à metodologia aplicada


# ============================================================================
# ESTRUTURA DA DRE (baseado no PDF)
# ============================================================================

ESTRUTURA_VOLUMES = [
    # ===== VOLUMES FINANCEIROS =====
    EstruturaLinehaDRE("TD21", "MSD - Curva Ajustada (Faturamento)", tipo="variavel"),
    EstruturaLinehaDRE("TD62", "Componente TD62", tipo="variavel"),
]

ESTRUTURA_DRE = [
    # ===== RECEITA =====
    EstruturaLinehaDRE("TD71", "Receita Financeira", tipo="variavel", valores=[0.0]*12),
    EstruturaLinehaDRE("TD72", "Despesa Financeira", tipo="variavel"),
    EstruturaLinehaDRE("TD90", "Receita de Oportunidade", tipo="variavel"),
    EstruturaLinehaDRE("TD91", "Despesa de Oportunidade", tipo="variavel"),
    EstruturaLinehaDRE("TD70", "Variação Cambial", tipo="variavel"),
    
    # ===== SPREAD E AJUSTES =====
    EstruturaLinehaDRE("TD87", "Spread Contrato Câmbio", tipo="variavel", eh_negrito=False),
    EstruturaLinehaDRE("TD88", "Alienação Ativos Financeiros", tipo="variavel", eh_negrito=False),
    EstruturaLinehaDRE("TD95", "Resultado Descasamentos", tipo="variavel", eh_negrito=False),
    EstruturaLinehaDRE("TD96", "Ajuste Oportunidade", tipo="variavel", eh_negrito=False),
    EstruturaLinehaDRE("TD97", "Valor Justo", tipo="variavel", eh_negrito=False),
    
    # ===== MARGEM BRUTA =====
    EstruturaLinehaDRE("MFB", "Margem Financeira Bruta", tipo="totalizador", 
                       formula="=TD71+TD72+TD90+TD91+TD70+TD87+TD88+TD95+TD96+TD97", 
                       eh_negrito=True),
    
    # ===== RECEITA/CUSTO DIFERIDO =====
    EstruturaLinehaDRE("TD11", "Receita Diferida", tipo="variavel"),
    EstruturaLinehaDRE("TD12", "Custo Diferido", tipo="variavel"),
    
    # ===== MARGEM BRUTA EFETIVA =====
    EstruturaLinehaDRE("MFBE", "Margem Financeira Bruta Efetiva", tipo="totalizador",
                       formula="=MFB+TD11+TD12",
                       eh_negrito=True),
    
    # ===== PROVISÕES E AJUSTES =====
    EstruturaLinehaDRE("TD76", "Provisão Perda Esperada", tipo="variavel"),
    EstruturaLinehaDRE("TD16", "Provisão Perda Esperada - Crédito Liberar", tipo="variavel"),
    EstruturaLinehaDRE("TD92", "Recuperação de Perdas", tipo="variavel"),
    EstruturaLinehaDRE("TD81", "Abatimento Negocial", tipo="variavel"),
    EstruturaLinehaDRE("TD67", "Perda Permanente", tipo="variavel"),
    
    # ===== RISCO DE CRÉDITO E MARGEM LÍQUIDA =====
    EstruturaLinehaDRE("RCC", "Risco de Crédito Contábil", tipo="totalizador",
                       formula="=TD76+TD16+TD92+TD81+TD67",
                       eh_negrito=True),
    EstruturaLinehaDRE("MFL", "Margem Financeira Líquida", tipo="totalizador",
                       formula="=MFBE-RCC",
                       eh_negrito=True),
    
    # ===== RECEITAS/DESPESAS OPERACIONAIS =====
    EstruturaLinehaDRE("TD73", "Tarifas", tipo="variavel"),
    EstruturaLinehaDRE("TD68", "Outros Componentes de Resultado Gerencial", tipo="variavel"),
    EstruturaLinehaDRE("TD78", "Outros Componentes de Resultado", tipo="variavel"),
    EstruturaLinehaDRE("TD79", "Custos Variáveis", tipo="variavel"),
    EstruturaLinehaDRE("TD80", "Tributos", tipo="variavel"),
    EstruturaLinehaDRE("TD82", "Perdas Operacionais", tipo="variavel"),
    
    # ===== MARGEM DE CONTRIBUIÇÃO =====
    EstruturaLinehaDRE("MC", "Margem de Contribuição", tipo="totalizador",
                       formula="=MFL+TD73+TD68+TD78+TD79+TD80+TD82",
                       eh_negrito=True),
    
    # ===== RESULTADO GERENCIAL =====
    EstruturaLinehaDRE("TD74", "Custos Identificados", tipo="variavel"),
    EstruturaLinehaDRE("RGP", "Resultado Gerencial de Produtos", tipo="totalizador",
                       formula="=MC-TD74",
                       eh_negrito=True),
    
    # ===== DESPESAS ADMINISTRATIVAS =====
    EstruturaLinehaDRE("TD69", "Despesas Administrativas Gerenciais", tipo="variavel"),
    EstruturaLinehaDRE("TD75", "Despesas Administrativas", tipo="variavel"),
    EstruturaLinehaDRE("TD83", "Custos Alocados", tipo="variavel"),
    EstruturaLinehaDRE("TD84", "Serviços Internos - Dependências", tipo="variavel"),
    
    # ===== RESULTADO GERENCIAL DE UNIDADES =====
    EstruturaLinehaDRE("RGU", "Resultado Gerencial de Unidades", tipo="totalizador",
                       formula="=RGP-TD69-TD75-TD83-TD84",
                       eh_negrito=True),
]


# ============================================================================
# INICIALIZAR ESTADOS
# ============================================================================

def _init_dre_state():
    """Inicializa estados da página DRE no session_state"""
    
    if "dre_dados" not in st.session_state:
        # Carrega ou cria dados padrão da DRE
        st.session_state.dre_dados = {}
        for linha in ESTRUTURA_DRE:
            st.session_state.dre_dados[linha.codigo] = {
                "descricao": linha.descricao,
                "tipo": linha.tipo,
                "formula": linha.formula,
                "valores": linha.valores.copy(),
                "eh_negrito": linha.eh_negrito,
                "metodologia": linha.metodologia,
            }
    
    # Inicializar dados de volumes (TD21, TD62)
    if "dre_volumes_dados" not in st.session_state:
        st.session_state.dre_volumes_dados = {}
        for linha in ESTRUTURA_VOLUMES:
            st.session_state.dre_volumes_dados[linha.codigo] = {
                "descricao": linha.descricao,
                "tipo": linha.tipo,
                "valores": linha.valores.copy(),
                "eh_negrito": linha.eh_negrito,
            }
    
    if "dre_metodologias" not in st.session_state:
        st.session_state.dre_metodologias = {}
    
    if "dre_filtros" not in st.session_state:
        st.session_state.dre_filtros = {
            "cliente": "Todos",
            "categoria": "",
            "produto": "",
            "ano": int(st.session_state.get("dre_ano_filter", 2026)),
        }
    
    # Inicializar rastreamento de mudança de filtro
    if "dre_combo_filtro_anterior" not in st.session_state:
        st.session_state.dre_combo_filtro_anterior = ""
    
    # Inicializar dicionário de persistência de dados por escopo de filtro
    # Estrutura: {combo_chave: {codigo: {descricao, tipo, formula, valores, eh_negrito}}}
    if "dre_dados_persistidos" not in st.session_state:
        st.session_state.dre_dados_persistidos = {}
    
    # Inicializar dicionário de DREs salvas se não existir
    if "dre_salvas" not in st.session_state:
        st.session_state.dre_salvas = {}
    
    # ===== NOVO: Inicializar índices selecionados para o novo layout =====
    if "dre_indices_selecionados" not in st.session_state:
        st.session_state.dre_indices_selecionados = []  # Lista de índices adicionados pelo usuário
    
    # Inicializar dias úteis e dias corridos
    if "dre_dias_uteis" not in st.session_state:
        st.session_state.dre_dias_uteis = [0] * 12
    
    if "dre_dias_corridos" not in st.session_state:
        st.session_state.dre_dias_corridos = [0] * 12

    # Persistência mínima de cenários para testes de simulação
    if "dre_cenarios" not in st.session_state:
        st.session_state.dre_cenarios = {
            "Base": {
                "dre_dados": deepcopy(st.session_state.dre_dados),
                "dre_metodologias": deepcopy(st.session_state.dre_metodologias),
                "dre_dados_persistidos": deepcopy(st.session_state.dre_dados_persistidos),
                "data_salvo": datetime.now().isoformat(),
            }
        }

    if "dre_cenario_ativo" not in st.session_state:
        st.session_state.dre_cenario_ativo = "Base"


def _salvar_snapshot_cenario(nome_cenario: str):
    """Salva snapshot do cenário atual no session_state."""
    st.session_state.dre_cenarios[nome_cenario] = {
        "dre_dados": deepcopy(st.session_state.get("dre_dados", {})),
        "dre_metodologias": deepcopy(st.session_state.get("dre_metodologias", {})),
        "dre_dados_persistidos": deepcopy(st.session_state.get("dre_dados_persistidos", {})),
        "data_salvo": datetime.now().isoformat(),
    }


def _carregar_snapshot_cenario(nome_cenario: str) -> bool:
    """Carrega snapshot de um cenário para o estado atual."""
    snapshot = st.session_state.get("dre_cenarios", {}).get(nome_cenario)
    if not snapshot:
        return False

    st.session_state.dre_dados = deepcopy(snapshot.get("dre_dados", {}))
    st.session_state.dre_metodologias = deepcopy(snapshot.get("dre_metodologias", {}))
    st.session_state.dre_dados_persistidos = deepcopy(snapshot.get("dre_dados_persistidos", {}))
    st.session_state.dre_cenario_ativo = nome_cenario
    return True


_SAFE_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def _avaliar_expressao_segura(expr: str, variaveis: Dict[str, float]) -> float:
    """Avalia expressão aritmética com AST sem permitir execução arbitrária."""
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError("Constante inválida")

        if isinstance(node, ast.Name):
            if node.id in variaveis:
                return float(variaveis[node.id])
            raise ValueError(f"Variável não encontrada: {node.id}")

        if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.left), _eval(node.right))

        if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.operand))

        raise ValueError("Expressão não permitida")

    arvore = ast.parse(expr, mode="eval")
    return float(_eval(arvore))


def _normalizar_valor_monetario_series(serie: pd.Series) -> pd.Series:
    """Converte série monetária para float, aceitando formatos BR e placeholders."""
    base = pd.to_numeric(serie, errors="coerce")
    if base.notna().any():
        return base.fillna(0.0)

    txt = (
        serie.astype(str)
        .str.strip()
        .str.replace("-", "0", regex=False)
        .str.replace(r"[^0-9,.-]", "", regex=True)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(txt, errors="coerce").fillna(0.0)


def _filtrar_base_dre(
    cliente: str = "Todos",
    categoria: str = "",
    produto: str = "",
    ano: Optional[int] = 2026,
) -> pd.DataFrame:
    """Aplica recorte de filtros da DRE na base carregada via upload."""
    # A DRE deve usar a mesma base ativa exibida ao usuario: upload atual da sessao
    # quando existir; caso contrario, a base compartilhada real (nao a personalizada).
    df_upload = get_base_dre_ativa()
    if df_upload is None or df_upload.empty:
        return pd.DataFrame()

    dff = _ensure_normalized_columns(df_upload)

    def _serie_coluna(coluna: str, default=np.nan) -> pd.Series:
        if coluna in dff.columns:
            return dff[coluna]
        return pd.Series([default] * len(dff), index=dff.index)

    if "MES_NUM" not in dff.columns:
        if "MES" in dff.columns:
            dff["MES_NUM"] = dff["MES"].apply(_mes_to_num)
        else:
            dff["MES_NUM"] = np.nan

    if "ANO_NUM" not in dff.columns:
        ano_fonte = _serie_coluna("ANO")
        if pd.to_numeric(ano_fonte, errors="coerce").isna().all() and "DATA" in dff.columns:
            ano_fonte = pd.to_datetime(dff["DATA"], errors="coerce").dt.year
        dff["ANO_NUM"] = pd.to_numeric(ano_fonte, errors="coerce")

    if cliente and cliente != "Todos":
        alvo = _norm_txt(cliente).replace("_", " ")
        mask_cli = dff["CLI_N"].astype(str).apply(_norm_txt) == alvo
        if not mask_cli.any():
            tokens = [t for t in alvo.replace("cliente", "").split() if t]
            if tokens:
                mask_cli = dff["CLI_N"].astype(str).apply(
                    lambda v: all(tok in _norm_txt(v) for tok in tokens)
                )
        dff = dff[mask_cli]

    if categoria:
        alvo_cat = _norm_txt(categoria)
        dff = dff[dff["CATEGORIA"].astype(str).apply(_norm_txt) == alvo_cat]

    if produto:
        dff_prod = dff[dff["PRODUTO"].astype(str).apply(lambda v: _produto_eh_equivalente(v, produto))]

        if dff_prod.empty and ":" in str(produto) and "COD_PRODUTO" in dff.columns:
            cod = _normalizar_codigo_produto(produto)
            dff_prod = dff[dff["COD_PRODUTO"].astype(str).apply(_normalizar_codigo_produto) == cod]

        if dff_prod.empty and ":" in str(produto):
            desc = _extrair_descricao_produto(produto)
            dff_prod = dff[dff["PRODUTO"].astype(str).apply(lambda v: _extrair_descricao_produto(v) == desc)]

        dff = dff_prod

    ano_num = pd.to_numeric(_serie_coluna("ANO_NUM"), errors="coerce")
    mes_num = pd.to_numeric(_serie_coluna("MES_NUM"), errors="coerce")

    mask_mes = mes_num.between(1, 12)
    if ano is None:
        mask_final = mask_mes
    elif ano_num.notna().any():
        mask_final = (ano_num == int(ano)) & mask_mes
    else:
        mask_final = mask_mes

    dff = dff[mask_final]
    return dff


def _normalizar_codigo_produto(valor: str) -> str:
    texto = str(valor or "")
    if ":" in texto:
        texto = texto.split(":", 1)[0]
    return re.sub(r"\D", "", texto)


def _extrair_descricao_produto(valor: str) -> str:
    texto = str(valor or "")
    if ":" in texto:
        texto = texto.split(":", 1)[1]
    return _norm_txt(texto)


def _normalizar_tokens_produto(texto: str) -> set:
    if not texto:
        return set()

    tokens = set(re.findall(r"[a-z0-9]+", _norm_txt(texto)))
    norm_tokens = set()
    for token in tokens:
        token_norm = token
        # Regras de plural em português
        if len(token_norm) > 4 and token_norm.endswith("ais"):
            # especial → especiais: troca "ais" por "al"
            token_norm = token_norm[:-3] + "al"
        elif len(token_norm) > 4 and token_norm.endswith("eis"):
            # papel → papeis: troca "eis" por "el"
            token_norm = token_norm[:-3] + "el"
        elif len(token_norm) > 4 and token_norm.endswith("ois"):
            # caracol → caracois: troca "ois" por "ol"
            token_norm = token_norm[:-3] + "ol"
        elif len(token_norm) > 4 and token_norm.endswith("uis"):
            # azul → azuis: troca "uis" por "ul"
            token_norm = token_norm[:-3] + "ul"
        elif len(token_norm) > 4 and token_norm.endswith("es"):
            # Para palavras como "cheques", remover apenas o "s" (não os dois caracteres)
            # Checa se a letra antes do "e" é uma vogal
            vogais = {"a", "e", "i", "o", "u"}
            if len(token_norm) >= 3 and token_norm[-3] in vogais:
                token_norm = token_norm[:-1]
            else:
                token_norm = token_norm[:-2]
        elif len(token_norm) > 3 and token_norm.endswith("s"):
            token_norm = token_norm[:-1]
        norm_tokens.add(token_norm)
    return norm_tokens


def _produto_eh_equivalente(valor_base: str, valor_filtro: str) -> bool:
    if not valor_base or not valor_filtro:
        return False

    base_norm = _norm_txt(valor_base)
    filtro_norm = _norm_txt(valor_filtro)
    if base_norm == filtro_norm:
        return True

    base_cod = _normalizar_codigo_produto(valor_base)
    filtro_cod = _normalizar_codigo_produto(valor_filtro)
    if base_cod and filtro_cod and (
        base_cod == filtro_cod
        or base_cod.startswith(filtro_cod)
        or filtro_cod.startswith(base_cod)
    ):
        return True

    base_desc = _extrair_descricao_produto(valor_base)
    filtro_desc = _extrair_descricao_produto(valor_filtro)
    if base_desc and filtro_desc:
        if base_desc == filtro_desc:
            return True

        base_tokens = _normalizar_tokens_produto(base_desc)
        filtro_tokens = _normalizar_tokens_produto(filtro_desc)
        if base_tokens and filtro_tokens:
            if base_tokens == filtro_tokens:
                return True
            if base_tokens.issubset(filtro_tokens) or filtro_tokens.issubset(base_tokens):
                return True

    return False


def _selecionar_opcao_equivalente(opcoes: list, valor_atual: str) -> int:
    if valor_atual in opcoes:
        return opcoes.index(valor_atual)

    for idx, opcao in enumerate(opcoes):
        if _produto_eh_equivalente(opcao, valor_atual):
            return idx

    return 0


@st.cache_data(show_spinner=False)
def _obter_catalogo_filtros_dre(df: pd.DataFrame) -> dict:
    """Precalcula opcoes de filtros da DRE a partir da base ativa normalizada."""
    if df is None or df.empty:
        return {
            "clientes": ["Todos"],
            "categorias_por_cliente": {"Todos": [""]},
            "produtos_por_escopo": {},
        }

    dff = _ensure_normalized_columns(df)
    col_cliente = "TIPO_CLIENTE" if "TIPO_CLIENTE" in dff.columns else ("TP_CLIENTE" if "TP_CLIENTE" in dff.columns else None)

    clientes = ["Todos"]
    if col_cliente is not None:
        clientes += sorted([c for c in dff[col_cliente].dropna().astype(str).unique() if c.strip()])

    categorias_por_cliente = {"Todos": [""]}
    produtos_por_escopo = {}

    categorias_todos = sorted([c for c in dff.get("CATEGORIA", pd.Series(dtype=str)).dropna().astype(str).unique() if c.strip()])
    if categorias_todos:
        categorias_por_cliente["Todos"] = [""] + categorias_todos

    for cliente in clientes:
        if cliente == "Todos":
            df_cli = dff
        else:
            df_cli = dff[dff["CLI_N"] == _norm_txt(cliente)]

        categorias_cliente = sorted([c for c in df_cli.get("CATEGORIA", pd.Series(dtype=str)).dropna().astype(str).unique() if c.strip()])
        categorias_por_cliente[cliente] = [""] + categorias_cliente if categorias_cliente else [""]

        for categoria in categorias_cliente:
            df_cat = df_cli[df_cli["CAT_N"] == _norm_txt(categoria)]
            produtos = sorted([p for p in df_cat.get("PRODUTO", pd.Series(dtype=str)).dropna().astype(str).unique() if p.strip()])
            produtos_por_escopo[f"{cliente}::{categoria}"] = [""] + produtos if produtos else [""]

    return {
        "clientes": clientes,
        "categorias_por_cliente": categorias_por_cliente,
        "produtos_por_escopo": produtos_por_escopo,
    }


def _serie_realizada_por_codigo(dff: pd.DataFrame, codigo: str) -> list:
    """Retorna série [12] de realizado para um código TD no recorte filtrado."""
    if dff is None or dff.empty:
        return [0.0] * 12

    col_comp = "CD_CPNT_RSTD" if "CD_CPNT_RSTD" in dff.columns else None
    if not col_comp:
        return [0.0] * 12

    col_valor = "CURVA_REALIZADO" if "CURVA_REALIZADO" in dff.columns else None
    if not col_valor:
        return [0.0] * 12

    # Filtra apenas linhas com componente (exclui linhas da guia DADOS sem componente)
    dff_com_componente = dff[dff[col_comp].notna()]
    df_comp = dff_com_componente[dff_com_componente[col_comp].astype(str).str.upper() == str(codigo).upper()]
    # Filtra linhas com valor zero (provavelmente duplicatas da guia DADOS)
    df_comp = df_comp[df_comp[col_valor].notna() & (df_comp[col_valor] != 0)]
    
    if df_comp.empty:
        return [0.0] * 12

    vals = _normalizar_valor_monetario_series(df_comp[col_valor])
    grp = (
        pd.DataFrame({"MES_NUM": df_comp["MES_NUM"], "VAL": vals})
        .groupby("MES_NUM", as_index=True)["VAL"]
        .sum()
        .reindex(range(1, 13))
        .fillna(0.0)
    )
    return (grp.astype(float).tolist() + [0.0] * 12)[:12]


def _serie_realizada_por_tip_td(dff: pd.DataFrame, codigo: str) -> list:
    """Retorna série [12] a partir de TIP_TD (guia DADOS), usada para TD21/TD62."""
    if dff is None or dff.empty or "TIP_TD" not in dff.columns:
        return [0.0] * 12

    col_valor = "CURVA_REALIZADO" if "CURVA_REALIZADO" in dff.columns else None
    if not col_valor:
        return [0.0] * 12

    df_comp = dff[dff["TIP_TD"].astype(str).str.upper() == str(codigo).upper()]
    if df_comp.empty:
        return [0.0] * 12

    vals = _normalizar_valor_monetario_series(df_comp[col_valor])
    grp = (
        pd.DataFrame({"MES_NUM": df_comp["MES_NUM"], "VAL": vals})
        .groupby("MES_NUM", as_index=True)["VAL"]
        .sum()
        .reindex(range(1, 13))
        .fillna(0.0)
    )
    return (grp.astype(float).tolist() + [0.0] * 12)[:12]


def _mes_corte_da_serie(serie_12: list) -> int:
    """Retorna o último mês (1-based) com valor realizado não-zero.
    
    Regra: percorre do mês 12 para 1; o primeiro não-zero encontrado é o corte.
    0 = nenhum mês realizado (tudo futuro).
    """
    for i in range(11, -1, -1):
        try:
            if abs(float(serie_12[i] or 0)) > 0:
                return i + 1  # converte índice 0-based para mês 1-based
        except Exception:
            pass
    return 0


def _mesclar_realizado_projetado(linha: dict) -> list:
    """Retorna valores[12] = realizado onde existe, projetado nos demais."""
    realizado = linha.get("realizado", [0.0] * 12)
    projetado = linha.get("projetado", [0.0] * 12)
    mes_corte = int(linha.get("mes_corte", 0))
    merged = []
    for i in range(12):
        if i < mes_corte and abs(float(realizado[i] or 0)) > 0:
            merged.append(float(realizado[i]))
        else:
            merged.append(float(projetado[i] or 0))
    return merged


def _garantir_flags_projetado(linha: dict) -> list:
    """Garante a presença das flags de preenchimento do projetado."""
    flags = _normalizar_flags_preenchimento(
        linha.get("projetado_preenchido"),
        valores=linha.get("projetado", [0.0] * 12),
        mes_corte=int(linha.get("mes_corte", 0) or 0),
    )
    linha["projetado_preenchido"] = list(flags)
    return flags


def _obter_flags_valores_linha(linha: dict) -> list:
    """Calcula flags do array visível da linha preservando vazio vs zero."""
    if not isinstance(linha, dict):
        return [False] * 12

    if linha.get("tipo") == "variavel":
        mes_corte = int(linha.get("mes_corte", 0) or 0)
        flags_proj = _garantir_flags_projetado(linha)
        flags = [True if idx < mes_corte else bool(flags_proj[idx]) for idx in range(12)]
    else:
        flags = _normalizar_flags_preenchimento(
            linha.get("valores_preenchidos"),
            valores=linha.get("valores", [0.0] * 12),
            padrao_todos=True,
        )

    linha["valores_preenchidos"] = list(flags)
    return flags


def _valor_editado_grade_para_real(valor_editado: object, escala: float) -> Optional[float]:
    """Converte o valor digitado na grade para o valor monetário persistido."""
    if valor_editado is None:
        return None
    try:
        if pd.isna(valor_editado):
            return None
    except Exception:
        pass
    try:
        if isinstance(valor_editado, str):
            bruto = valor_editado.strip()
            if not bruto or bruto == "-":
                return None
            bruto = bruto.replace("R$", "").replace(" ", "")

            # Aceita entradas pt-BR e en-US com ou sem separador de milhar.
            if "," in bruto and "." in bruto:
                if bruto.rfind(",") > bruto.rfind("."):
                    bruto = bruto.replace(".", "").replace(",", ".")
                else:
                    bruto = bruto.replace(",", "")
            elif bruto.count(".") > 1:
                bruto = bruto.replace(".", "")
            elif bruto.count(",") > 1:
                bruto = bruto.replace(",", "")
            elif "," in bruto:
                bruto = bruto.replace(",", ".")

            valor_editado = bruto
        return float(valor_editado) * float(escala)
    except Exception:
        return None


def _aplicar_edicoes_grade_dre(df_editado: pd.DataFrame, colunas_meses: list, escala: float) -> None:
    """Aplica edições da grade preservando zero digitado e vazio lógico."""
    if df_editado is None or df_editado.empty:
        return

    dre_dados = st.session_state.get("dre_dados", {})
    widget_state = st.session_state.get("dre_grade_editavel", {})
    edited_rows = widget_state.get("edited_rows", {}) if isinstance(widget_state, dict) else {}

    for row_idx, linha_df in df_editado.iterrows():
        codigo = str(linha_df.get("TD", "") or "")
        linha = dre_dados.get(codigo)
        if not isinstance(linha, dict) or linha.get("tipo") != "variavel":
            continue

        campos_editados = edited_rows.get(row_idx) or edited_rows.get(str(row_idx)) or {}
        if not isinstance(campos_editados, dict):
            campos_editados = {}

        projetado = [float(v or 0.0) for v in (linha.get("projetado") or [0.0] * 12)[:12]]
        while len(projetado) < 12:
            projetado.append(0.0)

        proj_flags = list(_garantir_flags_projetado(linha))
        base = [float(v or 0.0) for v in (linha.get("valores_base") or projetado)[:12]]
        while len(base) < 12:
            base.append(0.0)

        base_flags = _normalizar_flags_preenchimento(
            linha.get("valores_base_preenchidos"),
            valores=base,
            mes_corte=int(linha.get("mes_corte", 0) or 0),
        )
        possui_metodologias = bool(linha.get("metodologias_aplicadas")) or isinstance(
            linha.get("metodologia"), dict
        )

        for idx, mes in enumerate(colunas_meses):
            if idx < int(linha.get("mes_corte", 0) or 0):
                continue
            if mes not in campos_editados:
                continue

            valor_real = _valor_editado_grade_para_real(campos_editados.get(mes), escala)
            if valor_real is None:
                projetado[idx] = 0.0
                proj_flags[idx] = False
                if not possui_metodologias:
                    base[idx] = 0.0
                    base_flags[idx] = False
            else:
                projetado[idx] = float(valor_real)
                proj_flags[idx] = True
                if not possui_metodologias:
                    base[idx] = float(valor_real)
                    base_flags[idx] = True

        linha["projetado"] = projetado
        linha["projetado_preenchido"] = proj_flags
        if not possui_metodologias:
            linha["valores_base"] = base
            linha["valores_base_preenchidos"] = base_flags
        linha["valores"] = _mesclar_realizado_projetado(linha)
        _obter_flags_valores_linha(linha)

    st.session_state["dre_dados"] = dre_dados


def _carregar_realizados_dre_linhas(
    cliente: str = "Todos",
    categoria: str = "",
    produto: str = "",
    ano: int = 2026,
    resetar_projetado: bool = False,
) -> bool:
    """Inicializa as linhas variáveis da DRE com valores realizados do upload.

    NOVO MODELO: separa realizado (imutável) de projetado (editável).
    - `realizado[12]`: carregado da TD_DRE — NUNCA será sobrescrito por metodologia.
    - `projetado[12]`: inicia zerado; preenchido por metodologias ou pelo usuário.
    - `mes_corte`: último mês com realizado ≠ 0.
    - `valores[12]`: merge dos dois — usado na exibição e nos cálculos.
    """
    dff = _filtrar_base_dre(cliente=cliente, categoria=categoria, produto=produto, ano=ano)
    if dff.empty:
        for linha_struct in ESTRUTURA_DRE:
            if linha_struct.tipo == "variavel":
                ln = st.session_state.dre_dados[linha_struct.codigo]
                ln["realizado"]  = [0.0] * 12
                ln["projetado"]  = [0.0] * 12
                ln["projetado_preenchido"] = [False] * 12
                ln["mes_corte"]  = 0
                ln["valores"]    = [0.0] * 12
                ln["valores_base"] = [0.0] * 12
                ln["valores_base_preenchidos"] = [False] * 12
        return False

    for linha_struct in ESTRUTURA_DRE:
        if linha_struct.tipo != "variavel":
            continue
        ln = st.session_state.dre_dados[linha_struct.codigo]
        serie_realizada = _serie_realizada_por_codigo(dff, linha_struct.codigo)
        mes_corte = _mes_corte_da_serie(serie_realizada)

        ln["realizado"]  = [float(v) for v in serie_realizada]
        ln["mes_corte"]  = mes_corte
        # Só inicializa projetado se ainda não houver (preserva simulação em andamento)
        if resetar_projetado or "projetado" not in ln:
            ln["projetado"] = [0.0] * 12
        if resetar_projetado:
            ln["projetado_preenchido"] = [False] * 12
        else:
            ln["projetado_preenchido"] = _normalizar_flags_preenchimento(
                ln.get("projetado_preenchido"),
                valores=ln["projetado"],
                mes_corte=mes_corte,
            )
        # valores_base = snapshot do projetado (para restauração quando metodologia é removida)
        if resetar_projetado or "valores_base" not in ln:
            ln["valores_base"] = list(ln["projetado"])
        if resetar_projetado or "valores_base_preenchidos" not in ln:
            ln["valores_base_preenchidos"] = list(ln["projetado_preenchido"])
        # valores = merge para exibição
        ln["valores"] = _mesclar_realizado_projetado(ln)
        _obter_flags_valores_linha(ln)
    return True


def _reaplicar_metodologias_no_escopo_atual(dre_dados: dict) -> None:
    """Recalcula metodologias já vinculadas às linhas ao trocar o ano/escopo."""
    if not isinstance(dre_dados, dict):
        return

    houve_recalculo = False
    for linha_struct in ESTRUTURA_DRE:
        if linha_struct.tipo != "variavel":
            continue

        codigo = linha_struct.codigo
        linha = dre_dados.get(codigo, {})
        if not isinstance(linha, dict):
            continue

        possui_metodologias = bool(linha.get("metodologias_aplicadas")) or isinstance(
            linha.get("metodologia"), dict
        )
        if not possui_metodologias:
            continue

        _recalcular_linha_por_metodologias(dre_dados, codigo)
        houve_recalculo = True

    if houve_recalculo:
        _calcular_totalizadores()


def _carregar_td21_volumes(cliente: str = "Todos", categoria: str = "", produto: str = "", ano: int = 2026):
    """
    Carrega valores de TD21 e TD62 para a seção de volumes financeiros.
    Os valores seguem a curva ajustada/simulada ativa quando disponível.
    """
    try:
        if "dre_volumes_dados" not in st.session_state:
            return

        dff = _filtrar_base_dre(cliente=cliente, categoria=categoria, produto=produto, ano=ano)

        df_upload = get_dados_upload()
        filtros_dre = st.session_state.get("dre_filtros", {})
        cd_tip_agpd_dre = filtros_dre.get("cd_tip_agpd", "Todos")
        tip_td_dre = filtros_dre.get("tip_td", "Todos")
        td_ajustada = _carregar_ajustada_produto(
            df_upload,
            cliente,
            categoria,
            produto,
            ano,
            cd_tip_agpd=cd_tip_agpd_dre,
            tip_td=tip_td_dre,
        )

        # Quando não houver curva ajustada persistida, preserva o legado baseado em TIP_TD.
        if td_ajustada is None:
            td_ajustada = _serie_realizada_por_tip_td(dff, "TD21")

        td62 = _serie_realizada_por_tip_td(dff, "TD62")

        for codigo, serie in (("TD21", td_ajustada), ("TD62", td62)):
            if st.session_state.dre_volumes_dados.get(codigo):
                st.session_state.dre_volumes_dados[codigo]["valores"] = list(serie)
            if st.session_state.get("dre_dados", {}).get(codigo):
                st.session_state.dre_dados[codigo]["valores"] = list(serie)
    except Exception as e:
        print(f"[DRE] Erro ao carregar TD21: {e}")


def _carregar_td71_simulacao(cliente: str = "Todos", categoria: str = "", produto: str = "", ano: int = 2026):
    """
    Nome legado mantido por compatibilidade.
    Comportamento atual: TD71 é carregado apenas com realizado da base filtrada.
    """
    try:
        dff = _filtrar_base_dre(cliente=cliente, categoria=categoria, produto=produto, ano=ano)
        st.session_state.dre_dados["TD71"]["valores"] = _serie_realizada_por_codigo(dff, "TD71")
    except Exception as e:
        print(f"[DRE] Erro ao carregar TD71: {e}")


# ============================================================================
# CÁLCULOS
# ============================================================================

def _calcular_totalizadores():
    """Calcula linhas do tipo 'totalizador' baseado nas fórmulas"""
    dre_dados = st.session_state.dre_dados
    
    for linha in ESTRUTURA_DRE:
        if linha.tipo == "totalizador" and linha.formula:
            # Avaliar a fórmula
            valores_novos = _avaliar_formula(linha.formula, dre_dados)
            dre_dados[linha.codigo]["valores"] = valores_novos
    
    st.session_state.dre_dados = dre_dados


def _avaliar_formula(
    formula: str,
    dre_dados: dict,
    sazonalidade: Union[Dict, int, None] = None,
    linha_destino_codigo: Optional[str] = None,
) -> list:
    """
    Avalia uma fórmula como '=TD71+TD72' ou '=0.05*TD71' ou '=SOMA(TD71)'
    Retorna lista com 12 valores mensais
    
    Suporta:
    - Operações matemáticas: =0.05*TD71, =TD71+TD72
    - Funções nativas: =SOMA(TD71), =MEDIA(TD71;TD72), =MINIMO(TD71:TD90)
    - Sazonalidade dinâmica: MEDIA(TD71) com período variável/fixo
    
    Args:
        formula: String com fórmula (ex: '=TD71+TD72')
        dre_dados: Dicionário com dados da DRE
        sazonalidade: Sazonalidade (dict novo, int legacy, ou None)
        
    Returns:
        Lista com 12 valores calculados
    """
    if not formula or not formula.startswith("="):
        return [0.0] * 12
    
    formula_limpa = formula[1:]  # Remove '='
    
    # Preparar contexto completo (DRE + volumes + índices)
    contexto_formula = _obter_contexto_formula(dre_dados)
    contexto_completo = _preparar_contexto_com_indices(contexto_formula)
    contexto_simples = {}
    for codigo, dados in contexto_completo.items():
        valores = dados.get("valores", [0.0] * 12)
        contexto_simples[codigo] = valores
    
    _log_dre(f"[DRE] Processando fórmula: {formula}")
    _log_dre(f"[DRE] Sazonalidade: {sazonalidade}")
    _log_dre(f"[DRE] Variáveis disponíveis: {list(contexto_formula.keys())}")
    
    # ===== PROCESSAR FUNÇÕES NATIVAS =====
    # Padrão regex para encontrar funções: SOMA(ARGS), MEDIA(ARGS), etc
    padrao_funcoes = r'(DESVIO_PADRAO|MEDIA_INTERNA|TRIMMEAN|SOMA|MEDIA|MINIMO|MAXIMO)\((.*?)\)'
    
    # Mapeamento de placeholders para resultados das funções
    # ex: __FUNC_0__ → [valores dos 12 meses]
    funcoes_dinamicas = {}
    formula_processada = formula_limpa
    
    matches = list(re.finditer(padrao_funcoes, formula_limpa, re.IGNORECASE))
    
    for idx, match in enumerate(matches):
        nome_funcao = match.group(1).upper()
        argumentos = match.group(2)
        
        _log_dre(f"[DRE] Encontrada função nativa: {nome_funcao}({argumentos})")
        
        # 🔑 NOVO: Chamar função dinâmica por mês
        from utils_ext.calc_functions import evaluar_funcao_dinamica_por_mes
        
        valores_dinamicos = evaluar_funcao_dinamica_por_mes(
            nome_funcao, 
            argumentos, 
            contexto_formula,
            saz=sazonalidade,
            linha_destino_codigo=linha_destino_codigo,
        )
        
        # Armazenar resultado
        placeholder = f"__FUNC_{idx}__"
        funcoes_dinamicas[placeholder] = valores_dinamicos
        
        # Substituir na fórmula com placeholder
        funcao_str = f"{nome_funcao}({argumentos})"
        formula_processada = formula_processada.replace(funcao_str, placeholder)
        
        _log_dre(f"[DRE] → Resultado (12 meses): {valores_dinamicos[:3]}...")
    
    _log_dre(f"[DRE] Fórmula final (antes do mês-a-mês): {formula_processada}")
    
    # ===== AVALIAR FÓRMULA PARA CADA MÊS =====
    valores_resultado = []
    
    for mes_idx in range(12):
        # Construir expressão para este mês específico
        expr = formula_processada
        
        variaveis_mes = {}

        for placeholder, valores_12 in funcoes_dinamicas.items():
            valor_mes = valores_12[mes_idx] if mes_idx < len(valores_12) else 0.0
            variaveis_mes[placeholder] = float(valor_mes)

        for codigo, valores in contexto_simples.items():
            valor_mes_var = valores[mes_idx] if mes_idx < len(valores) else 0.0
            variaveis_mes[codigo] = float(valor_mes_var)
        
        try:
            resultado = _avaliar_expressao_segura(expr, variaveis_mes)
            valores_resultado.append(float(resultado))
            if mes_idx == 0:  # Log apenas do primeiro mês para não poluir
                _log_dre(f"[DRE] Mês 0 resultado: {resultado}")
        except Exception as e:
            _log_dre(f"[DRE] ❌ Erro ao avaliar fórmula '{formula}' mês {mes_idx}: {e}")
            _log_dre(f"[DRE] Expressão era: {expr}")
            valores_resultado.append(0.0)

    _log_dre(f"[DRE] Resultado final (12 meses): {valores_resultado[:3]}... (primeiros 3)")
    return valores_resultado


def _aplicar_metodologia_em_linha(
    dre_dados: dict,
    codigo: str,
    met_nome: str,
    met_dados: dict,
    modo_periodo: str = "Todos",
    mes_inicio: int = 1,
    mes_fim: int = 12,
) -> tuple[bool, str, bool]:
    """Aplica metodologia em uma linha e retorna (ok, mensagem, alterou_valor).

    Regra atual: aplicações na mesma linha são acumulativas (somatório de efeitos) em ordem.
    """
    if codigo not in dre_dados:
        return False, f"Linha {codigo} não encontrada.", False

    formula_aplicar = _normalizar_formula_usuario(met_dados.get("formula", ""))
    classif = _classificar_tokens_formula(formula_aplicar, dre_dados)
    if classif.get("invalidos"):
        return False, f"Referências inválidas: {', '.join(classif['invalidos'])}", False

    valores_antes = list(dre_dados[codigo].get("valores", [0.0] * 12))

    # Migração de estado legado: metodologia única -> lista acumulativa
    linha = dre_dados[codigo]
    if "metodologias_aplicadas" not in linha:
        linha["metodologias_aplicadas"] = []
        met_legada = linha.get("metodologia")
        if isinstance(met_legada, dict) and met_legada.get("nome"):
            linha["metodologias_aplicadas"].append({
                "nome": met_legada.get("nome"),
                "periodo": met_legada.get("periodo", "Todos"),
                "mes_inicio": int(met_legada.get("mes_inicio", 1)),
                "mes_fim": int(met_legada.get("mes_fim", 12)),
                "data_aplicacao": met_legada.get("data_aplicacao", datetime.now().isoformat()),
            })

    # NOVO: valores_base = snapshot do projetado ANTES da primeira metodologia
    # (apenas inicializa; mantém se já existir para preservar o baseline correto)
    if "valores_base" not in linha:
        linha["valores_base"] = list(linha.get("projetado", [0.0] * 12))
    if "valores_base_preenchidos" not in linha:
        linha["valores_base_preenchidos"] = list(_garantir_flags_projetado(linha))

    existentes = linha.get("metodologias_aplicadas", [])
    nomes_existentes = [m.get("nome") for m in existentes]
    if met_nome in nomes_existentes:
        # Atualiza a configuração da metodologia já acumulada mantendo posição na ordem
        idx_met = nomes_existentes.index(met_nome)
        existentes[idx_met] = {
            "nome": met_nome,
            "periodo": modo_periodo,
            "mes_inicio": mes_inicio,
            "mes_fim": mes_fim,
            "data_aplicacao": datetime.now().isoformat(),
        }
    else:
        # Nova metodologia: acumula no final da ordem
        existentes.append({
            "nome": met_nome,
            "periodo": modo_periodo,
            "mes_inicio": mes_inicio,
            "mes_fim": mes_fim,
            "data_aplicacao": datetime.now().isoformat(),
        })
    linha["metodologias_aplicadas"] = existentes

    _recalcular_linha_por_metodologias(dre_dados, codigo)

    alterou = not np.allclose(
        np.array(valores_antes, dtype=float),
        np.array(dre_dados[codigo].get("valores", [0.0] * 12), dtype=float)
    )
    return True, f"Metodologia acumulada em {codigo}.", alterou


def _remover_metodologia_da_linha(dre_dados: dict, codigo: str, restaurar_valores: bool = True) -> tuple[bool, str]:
    """Remove metodologia da linha e restaura valores anteriores quando possível."""
    if codigo not in dre_dados:
        return False, f"Linha {codigo} não encontrada."

    linha = dre_dados.get(codigo, {})
    mets = linha.get("metodologias_aplicadas", [])
    if not mets and not isinstance(linha.get("metodologia"), dict):
        return False, f"Linha {codigo} não possui metodologia aplicada."

    linha["metodologias_aplicadas"] = []
    linha["metodologia"] = None

    if restaurar_valores:
        base = linha.get("valores_base")
        if isinstance(base, list) and len(base) >= 12:
            linha["projetado"] = [float(v) for v in base[:12]]
        else:
            linha["projetado"] = [0.0] * 12
        linha["projetado_preenchido"] = _normalizar_flags_preenchimento(
            linha.get("valores_base_preenchidos"),
            valores=linha["projetado"],
            mes_corte=int(linha.get("mes_corte", 0) or 0),
        )
        linha["valores"] = _mesclar_realizado_projetado(linha)
        _obter_flags_valores_linha(linha)

    return True, f"Metodologias removidas da linha {codigo}."


def _recalcular_linha_por_metodologias(dre_dados: dict, codigo: str):
    """Recalcula uma linha aplicando metodologias acumuladas em ordem (efeito somatório).

    REGRA DE PROTEÇÃO: meses com realizado (índice < mes_corte) são preservados —
    a metodologia só escreve nos meses futuros (projetado).
    """
    if codigo not in dre_dados:
        return

    linha = dre_dados[codigo]
    mes_corte = int(linha.get("mes_corte", 0))

    # Base do projetado: valores_base guarda o projetado antes de qualquer metodologia
    base_projetado = linha.get("valores_base")
    if not isinstance(base_projetado, list) or len(base_projetado) < 12:
        base_projetado = [0.0] * 12
        linha["valores_base"] = list(base_projetado)
    base_flags = _normalizar_flags_preenchimento(
        linha.get("valores_base_preenchidos"),
        valores=base_projetado,
        mes_corte=mes_corte,
    )
    linha["valores_base_preenchidos"] = list(base_flags)

    acumulado_projetado = [float(v) for v in base_projetado[:12]]
    acumulado_flags = list(base_flags)

    # Normalização de estado legado
    mets = linha.get("metodologias_aplicadas", [])
    if not mets:
        met_legada = linha.get("metodologia")
        if isinstance(met_legada, dict) and met_legada.get("nome"):
            mets = [{
                "nome": met_legada.get("nome"),
                "periodo": met_legada.get("periodo", "Todos"),
                "mes_inicio": int(met_legada.get("mes_inicio", 1)),
                "mes_fim": int(met_legada.get("mes_fim", 12)),
                "data_aplicacao": met_legada.get("data_aplicacao", datetime.now().isoformat()),
            }]
            linha["metodologias_aplicadas"] = mets

    # Para calcular a fórmula, o contexto de cada linha expõe o merge atual (realizado + projetado)
    linha["valores"] = _mesclar_realizado_projetado({
        "realizado": linha.get("realizado", [0.0] * 12),
        "projetado": acumulado_projetado,
        "mes_corte": mes_corte,
    })

    ativos = []
    for m in mets:
        met_nome = m.get("nome")
        met_cfg = st.session_state.get("dre_metodologias", {}).get(met_nome)
        if not met_cfg:
            continue

        serie = _avaliar_formula(
            _normalizar_formula_usuario(met_cfg.get("formula", "")),
            dre_dados,
            sazonalidade=met_cfg.get("sazonalidade"),
            linha_destino_codigo=codigo,
        )

        periodo = m.get("periodo", "Todos")
        mi = int(m.get("mes_inicio", 1))
        mf = int(m.get("mes_fim", 12))

        if periodo == "Todos":
            ini, fim = 0, 11
        else:
            ini = min(mi, mf) - 1
            fim = max(mi, mf) - 1

        for i in range(ini, fim + 1):
            mes_num = i + 1  # 1-based
            # ── PROTEÇÃO: não sobrescreve meses realizados ──
            if mes_num <= mes_corte:
                continue
            acumulado_projetado[i] += float(serie[i])
            acumulado_flags[i] = True

        # Atualiza contexto com o acumulado mais recente
        linha["valores"] = _mesclar_realizado_projetado({
            "realizado": linha.get("realizado", [0.0] * 12),
            "projetado": acumulado_projetado,
            "mes_corte": mes_corte,
        })
        ativos.append(m)

    linha["metodologias_aplicadas"] = ativos
    linha["projetado"] = acumulado_projetado
    linha["projetado_preenchido"] = acumulado_flags
    linha["valores"] = _mesclar_realizado_projetado(linha)
    _obter_flags_valores_linha(linha)

    if ativos:
        nomes = [m.get("nome", "") for m in ativos if m.get("nome")]
        linha["metodologia"] = {
            "nome": " + ".join(nomes),
            "periodo": "Todos",
            "mes_inicio": 1,
            "mes_fim": 12,
            "data_aplicacao": ativos[-1].get("data_aplicacao", datetime.now().isoformat()),
            "metodologias": nomes,
        }
    else:
        linha["metodologia"] = None


def _remover_metodologia_especifica_da_linha(dre_dados: dict, codigo: str, met_nome: str):
    """Remove somente uma metodologia específica da pilha da linha e recalcula o resultado."""
    if codigo not in dre_dados:
        return
    linha = dre_dados[codigo]
    mets = linha.get("metodologias_aplicadas", [])
    if not mets:
        met_legada = linha.get("metodologia")
        if isinstance(met_legada, dict):
            # Normaliza: pode ser nome composto ("A + B") ou lista simples
            nomes_legados = met_legada.get("metodologias", []) or [met_legada.get("nome", "")]
            if met_nome in nomes_legados:
                # Migrar para lista antes de remover, depois cai no fluxo normal
                linha["metodologias_aplicadas"] = [
                    {
                        "nome": n,
                        "periodo": "Todos",
                        "mes_inicio": 1,
                        "mes_fim": 12,
                        "data_aplicacao": met_legada.get("data_aplicacao", datetime.now().isoformat()),
                    }
                    for n in nomes_legados if n
                ]
                mets = linha["metodologias_aplicadas"]
            else:
                return
        else:
            return

    filtradas = [m for m in mets if m.get("nome") != met_nome]
    linha["metodologias_aplicadas"] = filtradas

    # CRÍTICO: limpar campo legado ANTES de chamar _recalcular, para evitar que
    # a migração de estado legado dentro de _recalcular re-insira a metodologia removida.
    linha["metodologia"] = None

    if not filtradas:
        # Sem metodologias: restaurar projetado ao baseline e recalcular merge
        base = linha.get("valores_base")
        if isinstance(base, list) and len(base) >= 12:
            linha["projetado"] = [float(v) for v in base[:12]]
        else:
            linha["projetado"] = [0.0] * 12
        linha["projetado_preenchido"] = _normalizar_flags_preenchimento(
            linha.get("valores_base_preenchidos"),
            valores=linha["projetado"],
            mes_corte=int(linha.get("mes_corte", 0) or 0),
        )
        linha["valores"] = _mesclar_realizado_projetado(linha)
        _obter_flags_valores_linha(linha)
    else:
        _recalcular_linha_por_metodologias(dre_dados, codigo)


def _limpar_query_params_exclusao_metodologia():
    """Remove query params usados na exclusão por clique de tag da tabela."""
    for _k in ["dre_del_cod", "dre_del_met", "dre_del_src"]:
        try:
            if _k in st.query_params:
                del st.query_params[_k]
        except Exception:
            pass


@_DIALOG_DECORATOR("Confirmar exclusão de metodologia", width="small")
def _dialog_confirmar_exclusao_metodologia_linha(codigo: str, met_nome: str):
    st.markdown(f"Deseja remover a metodologia **{met_nome}** da linha **{codigo}**?")
    st.caption("Essa ação remove apenas esta metodologia da linha selecionada e recalcula os valores.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancelar", use_container_width=True, key=f"btn_cancel_del_ss_{codigo}_{met_nome}"):
            st.session_state.pop("dre_del_pending", None)
            st.rerun()

    with c2:
        if st.button("Excluir", use_container_width=True, type="primary", key=f"btn_ok_del_ss_{codigo}_{met_nome}"):
            dre_state = deepcopy(st.session_state.get("dre_dados", {}))
            _remover_metodologia_especifica_da_linha(dre_state, codigo, met_nome)

            st.session_state.dre_dados = dre_state
            _calcular_totalizadores()
            _persistir_linhas_dre()

            st.session_state.pop("dre_del_pending", None)
            st.session_state["dre_msg_sucesso_exclusao_tag"] = f"Metodologia '{met_nome}' removida da linha {codigo}."
            st.rerun()


def _fmt_dre_valor(v: float) -> str:
    """Exibe o valor completo da DRE em pt-BR, sem abreviação e sem casas decimais."""
    try:
        val = float(v)
    except Exception:
        return "-"

    if val == 0:
        return "0"
    return fmt_br(val, casas=0)


def _diagnosticar_formula_sem_efeito(formula: str, dre_dados: dict) -> str:
    """Retorna diagnóstico simples quando uma metodologia não altera valores."""
    try:
        formula_norm = _normalizar_formula_usuario(formula or "")
        classif = _classificar_tokens_formula(formula_norm, dre_dados)
        refs = list(dict.fromkeys(classif.get("dre", []) + classif.get("indices", [])))
        if not refs:
            return ""

        contexto = _preparar_contexto_com_indices(_obter_contexto_formula(dre_dados))
        refs_zeradas = []
        for ref in refs:
            valores = (contexto.get(ref, {}) or {}).get("valores", [])
            if valores and all(np.isclose(float(v), 0.0) for v in valores):
                refs_zeradas.append(ref)

        if refs_zeradas:
            return f" Referências zeradas no escopo atual: {', '.join(refs_zeradas)}."
        return ""
    except Exception:
        return ""


# ============================================================================
# PERSISTÊNCIA
# ============================================================================

def salvar_dre_usuario():
    """
    Salva dados da DRE para o usuário atual.
    - session_state: para acesso rápido na sessão
    - JSON em backend/database/simulacoes/: para persistência entre sessões
    """
    usuario = st.session_state.get("usuario", "anonimo")
    usuario_id = st.session_state.get("usuario_id", usuario)
    filtros = st.session_state.get("dre_filtros", {})
    ano = st.session_state.get("dre_ano_filter", 2026)
    dre_dados = st.session_state.get("dre_dados", {})
    dre_metodologias = st.session_state.get("dre_metodologias", {})

    combo_key = f"{filtros.get('cliente', 'Todos')}::{filtros.get('categoria', '')}::{filtros.get('produto', '')}::{ano}"

    # ── Persistência em session_state (acesso rápido) ───────────────────────
    if "dre_salvas" not in st.session_state:
        st.session_state.dre_salvas = {}
    if usuario not in st.session_state.dre_salvas:
        st.session_state.dre_salvas[usuario] = {}
    st.session_state.dre_salvas[usuario][combo_key] = {
        "cliente": filtros.get("cliente", "Todos"),
        "categoria": filtros.get("categoria", ""),
        "produto": filtros.get("produto", ""),
        "ano": ano,
        "dre_dados": dre_dados,
        "dre_metodologias": dre_metodologias,
        "data_salvo": datetime.now().isoformat(),
    }

    # ── Persistência JSON no backend (sobrevive a restart) ──────────────────
    if _DRE_BACKEND_OK:
        projecoes = {}
        for codigo, ln in dre_dados.items():
            projetado = ln.get("projetado")
            if isinstance(projetado, list) and len(projetado) >= 12:
                projecoes[codigo] = {
                    "projetado": [float(v) for v in projetado[:12]],
                    "projetado_preenchido": [
                        bool(v) for v in _normalizar_flags_preenchimento(
                            ln.get("projetado_preenchido"),
                            valores=projetado,
                            mes_corte=int(ln.get("mes_corte", 0) or 0),
                        )
                    ],
                    "valores_base": [
                        float(v) for v in (ln.get("valores_base") or projetado)[:12]
                    ],
                    "valores_base_preenchidos": [
                        bool(v) for v in _normalizar_flags_preenchimento(
                            ln.get("valores_base_preenchidos"),
                            valores=(ln.get("valores_base") or projetado)[:12],
                            mes_corte=int(ln.get("mes_corte", 0) or 0),
                        )
                    ],
                }
        try:
            ok, msg = _salvar_simulacao_dre_backend(usuario_id, combo_key, projecoes, dre_metodologias)
            if ok:
                _log_dre(f"[DRE] Persistida no JSON backend: {combo_key}")
            else:
                _log_dre(f"[DRE] Falha no backend: {msg}")
        except Exception as e:
            _log_dre(f"[DRE] Exceção ao persistir no backend: {e}")

    _log_dre(f"[DRE] Salva para usuário {usuario}: {combo_key}")
    st.success(f"DRE salva com sucesso para {filtros.get('produto', 'escopo atual')}!")


def _carregar_simulacao_dre_usuario(combo_key: str):
    """Carrega projeções e metodologias persistidas do backend para o escopo dado.
    
    Aplica sobre as linhas já inicializadas com realizados:
    - projetado[12] é restaurado a partir do JSON
    - metodologias são restauradas para o session_state
    - valores[12] é recalculado (merge)
    """
    if not _DRE_BACKEND_OK:
        return False

    usuario_id = st.session_state.get("usuario_id", st.session_state.get("usuario", "anonimo"))
    try:
        escopo = _carregar_simulacao_dre_backend(usuario_id, combo_key)
    except Exception as e:
        _log_dre(f"[DRE] Exceção ao carregar simulação DRE: {e}")
        return False

    if not escopo:
        return False

    projecoes_salvas = escopo.get("projecoes", {})
    metodologias_salvas = escopo.get("metodologias", {})

    dre_dados = st.session_state.get("dre_dados", {})
    for codigo, projetado_salvo in projecoes_salvas.items():
        if codigo not in dre_dados:
            continue
        ln = dre_dados[codigo]
        payload = projetado_salvo if isinstance(projetado_salvo, dict) else {"projetado": projetado_salvo}
        projetado_lista = payload.get("projetado")
        if isinstance(projetado_lista, list) and len(projetado_lista) >= 12:
            ln["projetado"] = [float(v) for v in projetado_lista[:12]]
            ln["projetado_preenchido"] = _normalizar_flags_preenchimento(
                payload.get("projetado_preenchido"),
                valores=ln["projetado"],
                mes_corte=int(ln.get("mes_corte", 0) or 0),
            )

            valores_base = payload.get("valores_base")
            if isinstance(valores_base, list) and len(valores_base) >= 12:
                ln["valores_base"] = [float(v) for v in valores_base[:12]]
            else:
                ln["valores_base"] = list(ln["projetado"])

            ln["valores_base_preenchidos"] = _normalizar_flags_preenchimento(
                payload.get("valores_base_preenchidos"),
                valores=ln["valores_base"],
                mes_corte=int(ln.get("mes_corte", 0) or 0),
            )
            ln["valores"] = _mesclar_realizado_projetado(ln)
            _obter_flags_valores_linha(ln)

    if metodologias_salvas:
        st.session_state["dre_metodologias"] = metodologias_salvas

    st.session_state["dre_dados"] = dre_dados
    _log_dre(f"[DRE] Simulação restaurada do backend: {combo_key}")
    return True


def carregar_dre_usuario(cliente: str, categoria: str, produto: str):
    """Carrega dados da DRE do session_state para esta combinação (legado)."""
    usuario = st.session_state.get("usuario", "anonimo")
    combo_key = f"{cliente}::{categoria}::{produto}"
    try:
        dre_salvas = st.session_state.get("dre_salvas", {}).get(usuario, {})
        dre_salva = dre_salvas.get(combo_key)
        if dre_salva:
            _log_dre(f"[DRE] Carregada para usuário {usuario}: {combo_key}")
        else:
            _log_dre(f"[DRE] Nenhuma DRE salva para: {combo_key}")
        return dre_salva
    except Exception as e:
        _log_dre(f"[DRE] Erro ao carregar: {e}")
        return None


def _dre_linhas_store_path() -> str:
    """Retorna caminho do arquivo de persistência das linhas da DRE."""
    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "database")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "dre_linhas_store.json")


def _persistir_linhas_dre(combo_key: str = "") -> bool:
    """Persiste linhas da DRE apenas na sessão atual (reset ao reiniciar servidor)."""
    try:
        filtros = st.session_state.get("dre_filtros", {})
        ano = st.session_state.get("dre_ano_filter", 2026)
        if not combo_key:
            combo_key = f"{filtros.get('cliente', 'Todos')}::{filtros.get('categoria', '')}::{filtros.get('produto', '')}::{ano}"

        st.session_state.setdefault("dre_dados_persistidos", {})
        st.session_state["dre_dados_persistidos"][combo_key] = {
            "dre_dados": deepcopy(st.session_state.get("dre_dados", {})),
            "dre_metodologias": deepcopy(st.session_state.get("dre_metodologias", {})),
            "salvo_em": datetime.now().isoformat(),
        }
        return True
    except Exception as e:
        _log_dre(f"[DRE] Falha ao persistir linhas: {e}")
        return False


def _restaurar_linhas_dre(combo_key: str) -> bool:
    """Restaura linhas da DRE persistidas na sessão atual para usuário + escopo."""
    try:
        registro = st.session_state.get("dre_dados_persistidos", {}).get(combo_key)
        if not registro:
            return False

        st.session_state.dre_dados = deepcopy(registro.get("dre_dados", st.session_state.get("dre_dados", {})))
        if registro.get("dre_metodologias"):
            st.session_state.dre_metodologias = deepcopy(registro.get("dre_metodologias", {}))
        return True
    except Exception as e:
        _log_dre(f"[DRE] Falha ao restaurar linhas: {e}")
        return False


def _linhas_variaveis_estao_zeradas() -> bool:
    """Detecta se as linhas variáveis da DRE estão integralmente zeradas na sessão atual."""
    dre_dados = st.session_state.get("dre_dados", {})
    for linha in ESTRUTURA_DRE:
        if linha.tipo != "variavel":
            continue
        serie = dre_dados.get(linha.codigo, {}).get("valores", [])
        if any(abs(float(v or 0.0)) > 0 for v in serie):
            return False
    return True



# ============================================================================
# RENDERIZAÇÃO - SEÇÕES DO NOVO LAYOUT (v2.5.1)
# ============================================================================

# ============================================================================
# UTILITÁRIOS - CÁLCULOS DE DIAS ÚTEIS E CORRIDOS
# ============================================================================

def _calcular_dias_uteis_e_corridos(ano: int = 2026) -> Dict[str, List[int]]:
    """
    Calcula dias úteis (seg-sex) e dias corridos para cada mês do ano.
    
    Dias úteis: segundas a sextas (desconsiderando fins de semana)
    Dias corridos: total de dias do mês
    
    Args:
        ano: Ano para o cálculo (default: 2026)
        
    Returns:
        Dict com estrutura:
        {
            "dias_uteis": [22, 20, 22, 21, 22, 21, 23, 22, 21, 23, 21, 22],
            "dias_corridos": [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        }
    """
    import calendar
    
    dias_uteis = []
    dias_corridos = []
    
    for mes in range(1, 13):
        # Obter número de dias do mês
        _, num_dias = calendar.monthrange(ano, mes)
        dias_corridos.append(num_dias)
        
        # Contar dias úteis (seg-sex = 0-4, sab-dom = 5-6)
        dias_uteis_mes = 0
        for dia in range(1, num_dias + 1):
            # weekday() retorna: 0=seg, 1=ter, 2=qua, 3=qui, 4=sex, 5=sab, 6=dom
            dia_semana = pd.Timestamp(ano, mes, dia).weekday()
            if dia_semana < 5:  # Segunda a sexta
                dias_uteis_mes += 1
        
        dias_uteis.append(dias_uteis_mes)
    
    return {
        "dias_uteis": dias_uteis,
        "dias_corridos": dias_corridos
    }


def _renderizar_secao_indices_economicos():
    """Renderiza a segunda seção: Índices Econômicos em tabela tipo-DRE com st.data_editor"""
    
    # Carregar índices disponíveis
    try:
        import sys
        import os
        backend_path = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        from database import obter_lista_indices_disponiveis, agregar_indice_para_12_meses
        
        indices_disponiveis = obter_lista_indices_disponiveis()
    except Exception as e:
        print(f"[UI] Erro ao carregar índices: {e}")
        indices_disponiveis = []
        st.error("Erro ao carregar índices disponíveis")
        return
    
    if not indices_disponiveis:
        st.info("Nenhum índice econômico carregado. Faça upload de um arquivo com a aba 'INDICES_TESOU'.")
        return
    
    # ===== MULTISELECT PARA ADICIONAR ÍNDICES =====
    st.markdown("""
    <div style="
        background: linear-gradient(90deg, #f0fef4 0%, rgba(6, 182, 212, 0.05) 100%);
        border-left: 4px solid #10b981;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
    ">
        <p style="color: #0c3a66; font-family: Plus Jakarta Sans, sans-serif; margin: 0; font-weight: 600; font-size: 0.95em;">
            <i class="fas fa-magnifying-glass" style="color: #10b981; margin-right: 8px;"></i>Selecione os Índices Econômicos
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    indices_selecionados = st.multiselect(
        "Escolha um ou mais índices",
        indices_disponiveis,
        default=st.session_state.dre_indices_selecionados,
        key="dre_multiselect_indice",
        label_visibility="collapsed"
    )
    
    # Sincronizar com session_state
    if indices_selecionados != st.session_state.dre_indices_selecionados:
        st.session_state.dre_indices_selecionados = indices_selecionados
        st.rerun()
    
    # ===== RENDERIZAR COM st.data_editor =====
    if st.session_state.dre_indices_selecionados:
        st.markdown("""
        <div style="
            background: linear-gradient(90deg, #ecf5fc 0%, rgba(6, 182, 212, 0.03) 100%);
            border-left: 4px solid #06b6d4;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 16px 0 12px 0;
        ">
            <p style="color: #0c3a66; font-family: Plus Jakarta Sans, sans-serif; margin: 0; font-weight: 600; font-size: 0.95em;">
                <i class="fas fa-chart-bar" style="color: #06b6d4; margin-right: 8px;"></i>Dados dos Índices (12 meses agregados)
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Preparar DataFrame com índices selecionados
        dados = []
        for nome_indice in st.session_state.dre_indices_selecionados:
            try:
                valores_indice = agregar_indice_para_12_meses(nome_indice)
                if valores_indice:
                    linha = {"Índice": nome_indice}
                    for i, mes in enumerate(MESES_ABR_LIST):
                        linha[mes] = valores_indice[i]
                    dados.append(linha)
            except Exception as e:
                print(f"[UI] Erro ao processar índice {nome_indice}: {e}")
        
        # Adicionar linhas de dias úteis e dias corridos
        dias_info = _calcular_dias_uteis_e_corridos(ano=2026)
        
        linha_dias_uteis = {"Índice": "Dias úteis"}
        for i, mes in enumerate(MESES_ABR_LIST):
            linha_dias_uteis[mes] = dias_info["dias_uteis"][i]
        dados.append(linha_dias_uteis)
        
        linha_dias_corridos = {"Índice": "Dias corridos"}
        for i, mes in enumerate(MESES_ABR_LIST):
            linha_dias_corridos[mes] = dias_info["dias_corridos"][i]
        dados.append(linha_dias_corridos)
        
        if dados:
            df = pd.DataFrame(dados)
            
            # Configurar columns_config para melhor visualização
            column_config = {
                "Índice": st.column_config.TextColumn(
                    width="medium",
                    disabled=True  # Não editável
                )
            }
            
            # Adicionar config para colunas de meses
            for mes in MESES_ABR_LIST:
                column_config[mes] = st.column_config.NumberColumn(
                    width="small",
                    disabled=True,  # Não editável
                    format="%.4f"
                )
            
            # ===== CSS SIMPLES E PADRONIZADO =====
            st.markdown("""
            <style>
                /* Tags do multiselect em ciano */
                .stMultiSelect [data-baseweb="tag"] {
                    background-color: #06b6d4 !important;
                    color: white !important;
                }
                
                .stMultiSelect [data-baseweb="tag"] span {
                    color: white !important;
                }
            </style>
            """, unsafe_allow_html=True)
            
            # Renderizar editor
            st.data_editor(
                df,
                use_container_width=True,
                column_config=column_config,
                hide_index=True,
                key="dre_data_editor",
                disabled=True  # Toda a tabela é somente leitura
            )
        else:
            st.warning("⚠️ Erro ao carregar dados dos índices.")
    
    else:
        st.info("ℹ️ Nenhum índice selecionado. Selecione um ou mais índices acima.")


def _renderizar_secao_volumes_financeiros():
    """Renderiza a primeira seção: Volumes Financeiros (TD21 e TD62) em tabela tipo-DRE"""
    
    volumes_dados = st.session_state.dre_volumes_dados
    
    # Preparar dados para tabela
    dados_tabela = []
    for linha in ESTRUTURA_VOLUMES:
        codigo = linha.codigo
        dados = volumes_dados.get(codigo, {})
        eh_negrito = dados.get("eh_negrito", False)
        tipo = dados.get("tipo", "variavel")
        valores_linha = dados.get("valores", [0.0] * 12)
        
        dados_tabela.append({
            "codigo": codigo,
            "descricao": dados.get("descricao", ""),
            "eh_negrito": eh_negrito,
            "tipo": tipo,
            "valores": valores_linha,
        })
    
    # ===== RENDERIZAR TABELA VOLUMES COM HTML/CSS =====
    st.markdown("""
    <style>
    .tabela-volumes {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 13px;
    }
    .tabela-volumes th {
        background: linear-gradient(135deg, #0c3a66 0%, #06b6d4 100%);
        color: white;
        font-weight: 600;
        padding: 12px 8px;
        text-align: center;
        border: 1px solid #0a2847;
    }
    .tabela-volumes th.codigo-col { text-align: left; width: 60px; }
    .tabela-volumes th.desc-col { text-align: left; width: 300px; }
    .tabela-volumes th.mes-col { width: 55px; }
    
    .tabela-volumes td {
        padding: 12px 8px;
        border: 1px solid #e2e8f0;
    }
    .tabela-volumes td.codigo-col {
        font-weight: 700;
        color: #0c3a66;
        background-color: #f0f9ff;
    }
    .tabela-volumes td.desc-col {
        color: #334155;
        background-color: #f8fafc;
    }
    .tabela-volumes td.mes-col {
        text-align: right;
        padding-right: 12px;
        background-color: #ffffff;
    }
    
    .tabela-volumes tbody tr {
        background-color: #ffffff;
        transition: background-color 0.2s;
    }
    .tabela-volumes tbody tr:hover {
        background-color: #f0f9ff;
    }
    .tabela-volumes tbody tr:nth-child(odd) td.mes-col {
        background-color: #fafbfc;
    }
    .tabela-volumes tbody tr:nth-child(odd):hover td.mes-col {
        background-color: #eff6ff;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Criar tabela HTML
    html_table = '<table class="tabela-volumes"><thead><tr>'
    html_table += '<th class="codigo-col">TD</th>'
    html_table += '<th class="desc-col">Descrição</th>'
    
    for mes in MESES_ABR_LIST:
        html_table += f'<th class="mes-col">{mes}</th>'
    
    html_table += '</tr></thead><tbody>'
    
    # Preencher dados
    for linha_data in dados_tabela:
        codigo = linha_data["codigo"]
        descricao = linha_data["descricao"]
        valores = linha_data["valores"]
        
        html_table += '<tr>'
        html_table += f'<td class="codigo-col">{codigo}</td>'
        html_table += f'<td class="desc-col">{descricao}</td>'
        
        for mes_idx in range(12):
            valor = valores[mes_idx]
            valor_formatado = _fmt_dre_valor(valor)
            html_table += f'<td class="mes-col">{valor_formatado}</td>'
        
        html_table += '</tr>'
    
    html_table += '</tbody></table>'
    st.markdown(html_table, unsafe_allow_html=True)


def _renderizar_secao_dre_linhas(dre_dados: dict, modo_viz: bool):
    """Renderiza a terceira seção: Linhas da DRE com estrutura completa"""
    
    st.markdown('<h3 style="color: #0c3a66; font-family: Plus Jakarta Sans, sans-serif;"><i class="fas fa-chart-line" style="color: #06b6d4; margin-right: 8px;"></i>Componentes de Resultado Gerencial</h3>', unsafe_allow_html=True)
    
    # Preparar dados para exibição
    dados_tabela = []
    for linha in ESTRUTURA_DRE:
        codigo = linha.codigo
        dados = dre_dados.get(codigo, {})
        eh_negrito = dados.get("eh_negrito", False)
        tipo = dados.get("tipo", "variavel")
        valores_linha = dados.get("valores", [0.0] * 12)
        
        dados_tabela.append({
            "codigo": codigo,
            "descricao": dados.get("descricao", ""),
            "eh_negrito": eh_negrito,
            "tipo": tipo,
            "valores": valores_linha,
        })
    
    # ===== RENDERIZAR TABELA COM HTML/CSS =====
    st.markdown("""
    <style>
    .dre-tabela {
        width: 100%;
        min-width: 1320px;
        border-collapse: collapse;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 13px;
    }
    .dre-table-wrap {
        width: 100%;
        overflow-x: auto;
        border-radius: 10px;
        border: 1px solid #dbe7f4;
        background: #fff;
    }
    .dre-tabela th {
        background: linear-gradient(135deg, #0c3a66 0%, #06b6d4 100%);
        color: white;
        font-weight: 600;
        padding: 12px 8px;
        text-align: center;
        border: 1px solid #0a2847;
    }
    .dre-tabela th.codigo-col { text-align: left; width: 60px; }
    .dre-tabela th.desc-col { text-align: left; width: 240px; }
    .dre-tabela th.met-col { text-align: left; width: 150px; }
    .dre-tabela th.mes-col { width: 45px; }
    
    .dre-tabela td {
        padding: 10px 8px;
        border: 1px solid #e2e8f0;
    }
    .dre-tabela td.codigo-col {
        font-weight: 600;
        color: #0c3a66;
    }
    .dre-tabela td.desc-col {
        color: #334155;
    }
    .dre-tabela td.met-col {
        color: #0c3a66;
        font-size: 12px;
        font-weight: 600;
    }
    .dre-tabela td.mes-col {
        text-align: right;
        padding-right: 12px;
        white-space: nowrap;
    }
    
    .dre-tabela tbody tr {
        background-color: #ffffff;
        transition: background-color 0.2s;
    }
    .dre-tabela tbody tr:hover {
        background-color: #f0f9ff;
    }
    .dre-tabela tbody tr.negrito {
        background: linear-gradient(90deg, #fce7f3 0%, #f8fafc 100%);
        font-weight: 600;
        border-top: 2px solid #f9a8d4;
        border-bottom: 2px solid #f9a8d4;
    }
    .dre-tabela tbody tr.negrito td {
        color: #c026d3;
    }
    .dre-tabela tbody tr:nth-child(odd) {
        background-color: #fafbfc;
    }
    .dre-tabela tbody tr:nth-child(odd):hover {
        background-color: #eff6ff;
    }
    .dre-input-valor {
        width: 100%;
        border: none;
        background: transparent;
        text-align: right;
        font-weight: 500;
    }
    .dre-cell-editable {
        cursor: cell;
    }
    .dre-met-tag {
        display: inline-block;
        margin: 2px 4px 2px 0;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        color: #0c3a66;
        background: rgba(6, 182, 212, 0.18);
        border: 1px solid rgba(6, 182, 212, 0.4);
        white-space: nowrap;
    }
    .dre-met-tag-click {
        text-decoration: none;
        cursor: pointer;
        appearance: none;
        -webkit-appearance: none;
        font-family: inherit;
        line-height: 1.1;
    }
    .dre-met-tag-click:hover {
        background: rgba(6, 182, 212, 0.25);
        border-color: rgba(6, 182, 212, 0.7);
    }
    [data-testid="stDataFrame"] div[role="columnheader"] {
        background: linear-gradient(135deg, #0c3a66 0%, #06b6d4 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    </style>
    <script>
    function dreSelectCell(codigo, mes) {
        try {
            const u = new URL(window.location.href);
            u.searchParams.set('dre_cell', `${codigo}_${mes}`);
            window.location.href = u.toString();
        } catch (e) {
            console.log(e);
        }
    }

    function dreAskDelete(codigoEnc, metEnc) {
        // Fallback JS mantido por compatibilidade; o fluxo primário usa href target=_self
        try {
            const codigo = decodeURIComponent(codigoEnc);
            const metodologia = decodeURIComponent(metEnc);
            const u = new URL(window.parent.location.href);
            u.searchParams.set('dre_del_cod', codigo);
            u.searchParams.set('dre_del_met', metodologia);
            u.searchParams.set('dre_del_src', 'js');
            window.parent.location.assign(u.toString());
        } catch (e) {
            console.log(e);
        }
    }
    </script>
    """, unsafe_allow_html=True)
    
    # ===== CRIAR ESTRUTURA DA TABELA =====
    html_table = '<table class="dre-tabela"><thead><tr>'
    html_table += '<th class="codigo-col">TD</th>'
    html_table += '<th class="desc-col">Descrição</th>'
    html_table += '<th class="met-col">Metodologia</th>'
    
    for mes in MESES_ABR_LIST:
        html_table += f'<th class="mes-col">{mes}</th>'
    
    html_table += '</tr></thead><tbody>'
    
    # ===== PREENCHER DADOS =====
    for i, linha_data in enumerate(dados_tabela):
        codigo = linha_data["codigo"]
        descricao = linha_data["descricao"]
        eh_negrito = linha_data["eh_negrito"]
        tipo = linha_data["tipo"]
        valores = linha_data["valores"]
        met_aplicada = dre_dados.get(codigo, {}).get("metodologia")
        
        classe_linha = "negrito" if eh_negrito else ""
        html_table += f'<tr class="{classe_linha}">'
        
        # Código
        html_table += f'<td class="codigo-col">{codigo}</td>'
        
        # Descrição
        html_table += f'<td class="desc-col">{descricao}</td>'

        # Renderizar cada metodologia em sua própria badge (separadas)
        met_col_html = "-"
        if met_aplicada and isinstance(met_aplicada, dict):
            mets_lista = met_aplicada.get("metodologias", [])
            if isinstance(mets_lista, list) and mets_lista:
                # Em modo visual, tag é clicável para abrir confirmação de exclusão
                tags_html = []
                for m in mets_lista:
                    if not m:
                        continue
                    m_txt = html.escape(str(m))
                    if modo_viz:
                        tags_html.append(
                            f'<span class="dre-met-tag" title="Use o painel abaixo para remover">{m_txt}</span>'
                        )
                    else:
                        tags_html.append(f'<span class="dre-met-tag">{m_txt}</span>')
                met_col_html = " ".join(tags_html) if tags_html else "-"
            else:
                # Fallback: usar o nome direto para compat. com estado legado
                nome = met_aplicada.get("nome", "-")
                if nome and nome != "-":
                    nome_txt = html.escape(str(nome))
                    met_col_html = f'<span class="dre-met-tag">{nome_txt}</span>'
        html_table += f'<td class="met-col">{met_col_html}</td>'
        
        # Valores dos meses — realizado = cinza/bloqueado, projetado = editável
        ln_dados = dre_dados.get(codigo, {})
        mes_corte_linha = int(ln_dados.get("mes_corte", 0))
        for mes_idx in range(12):
            valor = valores[mes_idx]
            valor_formatado = _fmt_dre_valor(valor)
            mes_num = mes_idx + 1  # 1-based
            eh_realizado = tipo == "variavel" and mes_num <= mes_corte_linha

            if eh_realizado:
                # Mês realizado: cinza, bloqueado, badge "R"
                html_table += (
                    f'<td class="mes-col" '
                    f'style="background:#f1f5f9;color:#64748b;" '
                    f'title="Realizado — não editável">'
                    f'{valor_formatado}'
                    f'<sup style="color:#94a3b8;font-size:8px;margin-left:2px;">R</sup>'
                    f'</td>'
                )
            elif tipo == "variavel" and not modo_viz:
                html_table += (
                    f'<td class="mes-col dre-cell-editable" '
                    f'ondblclick="dreSelectCell(\'{codigo}\',{mes_idx+1})" '
                    f'title="Projetado — duplo clique para aplicar metodologia">{valor_formatado}</td>'
                )
            else:
                html_table += f'<td class="mes-col">{valor_formatado}</td>'
        
        html_table += '</tr>'
    
    html_table += '</tbody></table>'

    colunas_meses = list(MESES_ABR_LIST)
    dados_editor = []
    for linha in ESTRUTURA_DRE:
        codigo = linha.codigo
        dados = dre_dados.get(codigo, {})
        met_aplicada = dados.get("metodologia") or {}
        linha_editor = {
            "TD": codigo,
            "Descrição": ("∑ " + dados.get("descricao", "")) if dados.get("tipo") == "totalizador" else dados.get("descricao", ""),
            "Metodologia": met_aplicada.get("nome", "-"),
        }
        for mes_idx, mes in enumerate(MESES_ABR_LIST):
            linha_editor[mes] = float((dados.get("valores") or [0.0] * 12)[mes_idx])
        dados_editor.append(linha_editor)

    if modo_viz:
        st.markdown(f'<div class="dre-table-wrap">{html_table}</div>', unsafe_allow_html=True)

        # ===== PAINEL DE GESTÃO DE METODOLOGIAS POR LINHA =====
        # Motivo: href/JS navigation causa recarga total e perde session_state (auth).
        # Solução: botões Streamlit nativos + session_state para disparar st.dialog.
        linhas_com_met = []
        for _linha_struct in ESTRUTURA_DRE:
            _cod = _linha_struct.codigo
            _dados = dre_dados.get(_cod, {})
            _met = _dados.get("metodologia")
            if isinstance(_met, dict):
                _mets_lista = _met.get("metodologias", [])
                if _mets_lista:
                    linhas_com_met.append((_cod, _dados.get("descricao", ""), list(_mets_lista)))

        if linhas_com_met:
            with st.container(border=True):
                st.markdown("#### 🗑️ Remover metodologia aplicada")
                for _cod, _desc, _mets in linhas_com_met:
                    for _m in _mets:
                        _c1, _c2 = st.columns([5, 1])
                        with _c1:
                            st.markdown(f"**{_cod}** — {_desc[:40]}: `{_m}`")
                        with _c2:
                            if st.button(
                                "✕",
                                key=f"btn_rm_met_{_cod}_{_m}",
                                use_container_width=True,
                                help=f"Remover {_m} de {_cod}",
                            ):
                                st.session_state["dre_del_pending"] = {"cod": _cod, "met": _m}
                                st.rerun()

        # Abrir dialog de confirmação se houver pendência no session_state
        _del_pending = st.session_state.get("dre_del_pending")
        if isinstance(_del_pending, dict) and _del_pending.get("cod") and _del_pending.get("met"):
            _dialog_confirmar_exclusao_metodologia_linha(_del_pending["cod"], _del_pending["met"])
    else:
        # O modo edição trabalha no valor completo para facilitar leitura e conferência.
        _ESCALA_EDITOR = 1.0
        df_dre_editor = pd.DataFrame(dados_editor)
        for mes in colunas_meses:
            df_dre_editor[mes] = (
                pd.to_numeric(df_dre_editor[mes], errors="coerce")
                .astype(float)
                .div(_ESCALA_EDITOR)
            )
            df_dre_editor[mes] = df_dre_editor[mes].apply(
                lambda valor: "" if pd.isna(valor) else fmt_br(valor, casas=0)
            )

        column_config_editor = {
            "TD": st.column_config.TextColumn("TD", width="small", disabled=True),
            "Descrição": st.column_config.TextColumn("Descrição", width="medium", disabled=True),
            "Metodologia": st.column_config.TextColumn("Metodologia", width="small", disabled=True),
        }
        for mes in colunas_meses:
            column_config_editor[mes] = st.column_config.TextColumn(
                mes,
                width="medium",
                help="Valor completo sem casas decimais. Aceita formatos como 928980649, 928.980.649 ou 928,980,649.",
            )

        df_editado = st.data_editor(
            df_dre_editor,
            key="dre_grade_editavel",
            hide_index=True,
            use_container_width=True,
            height=560,
            disabled=["TD", "Descrição", "Metodologia"],
            column_config=column_config_editor,
            num_rows="fixed",
        )

        _aplicar_edicoes_grade_dre(df_editado, colunas_meses, _ESCALA_EDITOR)
        dre_dados = st.session_state.get("dre_dados", dre_dados)

    if st.session_state.get("dre_msg_sucesso_exclusao_tag"):
        st.success(st.session_state.get("dre_msg_sucesso_exclusao_tag"))
        del st.session_state["dre_msg_sucesso_exclusao_tag"]

    st.caption("Gerenciamento de metodologia por linha foi concentrado na aba 'Aplicar e Histórico' para manter o fluxo simples e previsível.")
    
    if not modo_viz:
        dre_cell_qs = st.query_params.get("dre_cell", "")
        if dre_cell_qs and isinstance(dre_cell_qs, str) and "_" in dre_cell_qs:
            try:
                cod_qs, mes_qs = dre_cell_qs.split("_", 1)
                mes_int = int(mes_qs)
                if 1 <= mes_int <= 12:
                    st.session_state["met_cell_linha"] = cod_qs
                    st.session_state["met_cell_mes"] = mes_int
            except Exception:
                pass

        st.markdown("---")
        st.markdown("""
        <div style="
            background: linear-gradient(90deg, #fffbeb 0%, rgba(245, 158, 11, 0.05) 100%);
            border-left: 4px solid #f59e0b;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
        ">
            <h3 style="color: #0c3a66; font-family: Plus Jakarta Sans, sans-serif; margin: 0 0 4px 0;">
                <i class="fas fa-pen-to-square" style="color: #f59e0b; margin-right: 10px;"></i>Editar Valores
            </h3>
            <p style="color: #666; margin: 4px 0 0 28px; font-size: 0.9em;">Atualize os valores variáveis das linhas da DRE</p>
        </div>
        """, unsafe_allow_html=True)
        st.caption("A própria grade acima fica editável no modo edição. Totalizadores continuam calculados automaticamente.")

        st.caption("No Streamlit, o componente de edição não expõe evento de duplo clique por célula. Use o painel abaixo para aplicar metodologia por TD/mês com o mesmo efeito operacional.")

        with st.container(border=True):
            st.markdown("#### ⚡ Aplicação rápida de metodologia")
            st.caption("Fluxo estilo planilha para aplicar a mesma metodologia em várias linhas.")
            variaveis_editaveis = [ln.codigo for ln in ESTRUTURA_DRE if ln.tipo == "variavel"]
            col_q1, col_q2 = st.columns([1.2, 1.8])
            with col_q1:
                linha_origem = st.selectbox("Linha base", variaveis_editaveis, key="met_quick_linha")
            with col_q2:
                metodologias_linha = {
                    nome: dados for nome, dados in st.session_state.get("dre_metodologias", {}).items()
                    if linha_origem in dados.get("aplicavel_a", [])
                }
                met_quick = st.selectbox(
                    "Metodologia",
                    ["Nenhuma"] + list(metodologias_linha.keys()),
                    key="met_quick_nome"
                )

            col_q3, col_q4 = st.columns([1.5, 1])
            with col_q3:
                linhas_destino = st.multiselect(
                    "Linhas destino (equivalente ao arrastar)",
                    variaveis_editaveis,
                    default=[linha_origem],
                    key="met_quick_destinos"
                )
            with col_q4:
                modo_quick = st.selectbox("Período", ["Todos", "Intervalo"], key="met_quick_periodo")

            col_q5, col_q6 = st.columns(2)
            with col_q5:
                met_quick_ini = st.selectbox("Mês inicial", options=list(range(1, 13)), format_func=lambda m: MESES_ABR_LIST[m-1], key="met_quick_ini")
            with col_q6:
                met_quick_fim = st.selectbox("Mês final", options=list(range(1, 13)), format_func=lambda m: MESES_ABR_LIST[m-1], key="met_quick_fim")

            if st.button("Aplicar nas linhas selecionadas", key="btn_met_quick_apply", use_container_width=True, type="primary"):
                if met_quick == "Nenhuma":
                    st.error("Selecione uma metodologia.")
                elif not linhas_destino:
                    st.error("Selecione ao menos uma linha destino.")
                else:
                    alteradas = []
                    sem_efeito = []
                    erros = []
                    for cod_dest in linhas_destino:
                        if cod_dest not in metodologias_linha[met_quick].get("aplicavel_a", []):
                            erros.append(f"{cod_dest}: metodologia não aplicável")
                            continue
                        ok, msg, alterou = _aplicar_metodologia_em_linha(
                            dre_dados,
                            cod_dest,
                            met_quick,
                            metodologias_linha[met_quick],
                            modo_periodo=modo_quick,
                            mes_inicio=met_quick_ini,
                            mes_fim=met_quick_fim,
                        )
                        if ok:
                            alteradas.append(cod_dest)
                            if not alterou:
                                sem_efeito.append(cod_dest)
                        else:
                            erros.append(f"{cod_dest}: {msg}")

                    if alteradas:
                        st.success(f"Aplicada em: {', '.join(alteradas)}")
                        if sem_efeito:
                            st.warning(f"Sem mudança de valores em: {', '.join(sem_efeito)}")
                        st.rerun()
                    if erros:
                        st.error(" | ".join(erros))

    st.session_state.dre_dados = dre_dados
    _calcular_totalizadores()
    _persistir_linhas_dre()
    
    # ===== RESUMO EM CARDS =====
    st.markdown("---")
    st.markdown("""
    <div style="
        background: linear-gradient(90deg, #fef2f2 0%, rgba(239, 68, 68, 0.05) 100%);
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    ">
        <h2 style="color: #0c3a66; font-family: Plus Jakarta Sans, sans-serif; margin: 0 0 4px 0;">
            <i class="fas fa-chart-pie" style="color: #ef4444; margin-right: 10px;"></i>Resumo de Resultado
        </h2>
        <p style="color: #666; margin: 4px 0 0 28px; font-size: 0.9em;">Principais indicadores financeiros da DRE</p>
    </div>
    """, unsafe_allow_html=True)
    
    dre_dados = st.session_state.dre_dados
    total_mfb = sum(dre_dados.get("MFB", {}).get("valores", []))
    total_mfbe = sum(dre_dados.get("MFBE", {}).get("valores", []))
    total_td71 = sum(dre_dados.get("TD71", {}).get("valores", []))
    total_td11 = sum(dre_dados.get("TD11", {}).get("valores", []))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Margem Bruta",
            fmt_br(total_mfb),
            help="Soma de todas as margens financeiras"
        )
    
    with col2:
        st.metric(
            "📊 Margem Efetiva",
            fmt_br(total_mfbe),
            help="Margem bruta + diferenciais"
        )
    
    with col3:
        st.metric(
            "📈 Receita Financeira",
            fmt_br(total_td71),
            help="Total de receitas financeiras"
        )
    
    with col4:
        st.metric(
            "📋 Receita Diferida",
            fmt_br(total_td11),
            help="Receitas diferidas para próximos períodos"
        )


# ============================================================================
# RENDERIZAÇÃO PRINCIPAL
# ============================================================================

def renderizar():
    """Renderiza a página de DRE Gerencial"""
    
    # Garantir que Font Awesome está carregado
    st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">', unsafe_allow_html=True)
    
    _init_dre_state()
    init_data_state()  # Inicializar data manager (session state para uploads)
    
    # ===== HEADER ELEGANTE COM DESTAQUE =====
    render_page_header(
        "DRE Gerencial - Demonstrativo de Resultado",
        "fa-receipt",
        "Simule e projete os componentes do Demonstrativo de Resultado Gerencial com precisão"
    )
    
    # ===== FILTROS (Cliente, Categoria, Produto) =====
    # Carregar dados para filtros a partir da mesma fonte usada nos realizados da DRE.
    df_upload = get_base_dre_ativa()
    origem_base_dre = get_origem_base_dre_ativa()
    catalogo_filtros = _obter_catalogo_filtros_dre(df_upload)
    base_rows = len(df_upload) if isinstance(df_upload, pd.DataFrame) else 0
    base_max_ano = int(df_upload["ANO_NUM"].max()) if isinstance(df_upload, pd.DataFrame) and "ANO_NUM" in df_upload.columns and not df_upload.empty else 0
    base_version_key = f"{origem_base_dre}::{base_rows}::{base_max_ano}"

    col_cli, col_cat, col_prod, col_ano, col_modo, col_btn = st.columns([1.2, 1.2, 1.5, 1, 1, 1])

    if origem_base_dre.startswith("upload_session:"):
        st.caption(f"Base ativa da DRE: upload atual da sessao ({origem_base_dre.split(':', 1)[1]}).")
    else:
        st.caption("Base ativa da DRE: base compartilhada salva no sistema.")
    
    # Cliente
    with col_cli:
        clientes = catalogo_filtros["clientes"]

        _cli_atual = st.session_state.get("dre_cliente_filter", "Todos")
        _idx_cli = clientes.index(_cli_atual) if _cli_atual in clientes else 0
        
        cliente_sel = st.selectbox(
            "Cliente",
            clientes,
            index=_idx_cli,
            key="dre_cliente_filter",
            label_visibility="collapsed"
        )
        st.session_state.dre_filtros["cliente"] = cliente_sel
    
    # Categoria
    with col_cat:
        categorias = catalogo_filtros["categorias_por_cliente"].get(cliente_sel, [""])
        
        # Preserva o valor atual do widget se ainda estiver disponível nas opções
        _cat_atual = st.session_state.get("dre_categoria_filter", "")
        _idx_cat = categorias.index(_cat_atual) if _cat_atual in categorias else 0

        categoria_sel = st.selectbox(
            "Categoria",
            categorias,
            index=_idx_cat,
            key="dre_categoria_filter",
            label_visibility="collapsed"
        )
        st.session_state.dre_filtros["categoria"] = categoria_sel
    
    # Produto
    with col_prod:
        produtos = catalogo_filtros["produtos_por_escopo"].get(f"{cliente_sel}::{categoria_sel}", [""])

        # Preserva o valor atual do widget se ainda estiver disponível nas opções
        _prod_atual = st.session_state.get("dre_produto_filter", "")
        _idx_prod = _selecionar_opcao_equivalente(produtos, _prod_atual)

        produto_sel = st.selectbox(
            "Produto",
            produtos,
            index=_idx_prod,
            key="dre_produto_filter",
            label_visibility="collapsed"
        )
        st.session_state.dre_filtros["produto"] = produto_sel
    
    # Ano
    with col_ano:
        ano_sel = st.selectbox(
            "Ano",
            [2024, 2025, 2026, 2027],
            index=2,
            key="dre_ano_filter",
            label_visibility="collapsed"
        )
        st.session_state.dre_filtros["ano"] = int(ano_sel)
    
    # Modo Visualização
    with col_modo:
        modo_edicao = st.toggle(
            "Modo edição",
            value=st.session_state.get("dre_modo_edicao", False),
            key="dre_modo_edicao"
        )
        modo_viz = not modo_edicao
        st.session_state["dre_modo_visualizacao"] = modo_viz
    
    # Botão Salvar
    with col_btn:
        if st.button("Salvar", use_container_width=True, type="primary"):
            salvar_dre_usuario()
    
    # Botão para Recarregar Base TD_DRE (força atualização)
    with col_btn:
        if st.button("🔄 Recarregar Base", use_container_width=True):
            # Limpar cache persistido para forçar recarregamento completo
            st.session_state.dre_dados_persistidos = {}
            st.session_state.dre_combo_filtro_anterior = ""
            st.rerun()
    
    # ===== DETECTAR MUDANÇA DE FILTRO E PERSISTIR DADOS =====
    # Criar chave única para a combinação atual de filtros
    combo_filtro_atual = f"{base_version_key}::{cliente_sel}::{categoria_sel}::{produto_sel}::{ano_sel}"
    combo_filtro_anterior = st.session_state.get("dre_combo_filtro_anterior", "")
    
    if combo_filtro_atual != combo_filtro_anterior:
        if combo_filtro_anterior:
            _persistir_linhas_dre(combo_filtro_anterior)

        if not _restaurar_linhas_dre(combo_filtro_atual):
            _carregar_realizados_dre_linhas(
                cliente_sel,
                categoria_sel,
                produto_sel,
                ano_sel,
                resetar_projetado=True,
            )
            carregou_backend = _carregar_simulacao_dre_usuario(combo_filtro_atual)
            if not carregou_backend:
                _reaplicar_metodologias_no_escopo_atual(st.session_state.get("dre_dados", {}))

        _carregar_td21_volumes(cliente_sel, categoria_sel, produto_sel, ano_sel)
        st.session_state.dre_combo_filtro_anterior = combo_filtro_atual
    
    st.divider()
    
    # ===== ABAS =====
    tab_editor, tab_metodologias, tab_analise, tab_indices = st.tabs([
        "Editor DRE",
        "Metodologias",
        "Análise",
        "Índices Econômicos"
    ])
    
    with tab_editor:
        _renderizar_editor_dre()
    
    with tab_metodologias:
        _renderizar_metodologias()
    
    with tab_analise:
        _renderizar_analise()
    
    with tab_indices:
        _renderizar_indices_economicos()


def _renderizar_editor_dre():
    """Renderiza o editor principal da DRE com 3 seções colapsáveis (novo layout)"""
    
    st.markdown("###  DRE Gerencial - Layout Integrado")
    
    dre_dados = st.session_state.dre_dados
    modo_viz = st.session_state.get("dre_modo_visualizacao", False)
    
    # ========================================================================
    # SEÇÃO 1: VOLUMES FINANCEIROS (EXPANDER) - AGORA PRIMEIRO
    # ========================================================================
    with st.expander("VOLUMES FINANCEIROS - TD21 e TD62", expanded=False):
        _renderizar_secao_volumes_financeiros()
    
    st.divider()
    
    # ========================================================================
    # SEÇÃO 2: INDICADORES ECONÔMICOS (EXPANDER) - AGORA SEGUNDO
    # ========================================================================
    with st.expander("INDICADORES ECONÔMICOS - Índices Compartilhados", expanded=False):
        _renderizar_secao_indices_economicos()
    
    st.divider()
    
    # ========================================================================
    # SEÇÃO 3: ESTRUTURA DA DRE (EXPANDER) - AGORA TERCEIRO
    # ========================================================================
    ano_exibicao = int(st.session_state.get("dre_ano_filter", 2026))
    with st.expander(f"ESTRUTURA DA DRE - Projeção Mensal ({ano_exibicao})", expanded=True):
        _renderizar_secao_dre_linhas(dre_dados, modo_viz)


def _renderizar_metodologias():
    """Renderiza página de configuração de metodologias com suporte a funções nativas"""
    
    st.markdown("###  Metodologias de Cálculo")
    st.markdown("""
    Crie fórmulas automáticas para calcular valores de variáveis na DRE.
    
    **Recursos:**
    - Operações matemáticas: `=0.05*TD71`, `=TD71+TD72`
    - Funções nativas: `=SOMA(TD71)`, `=MEDIA(TD71;TD72)`, `=MINIMO(TD71:TD90)`
    - Histórico de aplicações com filtros e contexto
    """)

    st.markdown("#### Cenários")
    cenarios = st.session_state.get("dre_cenarios", {})
    nomes_cenarios = list(cenarios.keys())
    ativo = st.session_state.get("dre_cenario_ativo", "Base")
    idx_ativo = nomes_cenarios.index(ativo) if ativo in nomes_cenarios else 0

    col_c1, col_c2, col_c3 = st.columns([1.4, 1, 1])
    with col_c1:
        cenario_sel = st.selectbox("Cenário ativo", nomes_cenarios, index=idx_ativo, key="dre_cenario_selector")
    with col_c2:
        if st.button("Carregar cenário", use_container_width=True, key="btn_carregar_cenario"):
            if _carregar_snapshot_cenario(cenario_sel):
                st.success(f"Cenário '{cenario_sel}' carregado.")
                st.rerun()
            st.error("Não foi possível carregar o cenário selecionado.")
    with col_c3:
        if st.button("Salvar cenário atual", use_container_width=True, key="btn_salvar_cenario"):
            _salvar_snapshot_cenario(cenario_sel)
            st.success(f"Cenário '{cenario_sel}' salvo.")

    novo_cenario = st.text_input("Novo cenário", placeholder="Ex: Estresse Selic + IPCA", key="dre_novo_cenario")
    if st.button("Criar cenário a partir do atual", use_container_width=True, key="btn_criar_cenario"):
        nome = (novo_cenario or "").strip()
        if not nome:
            st.error("Informe um nome para o cenário.")
        elif nome in st.session_state.dre_cenarios:
            st.error("Já existe um cenário com esse nome.")
        else:
            _salvar_snapshot_cenario(nome)
            st.session_state.dre_cenario_ativo = nome
            st.success(f"Cenário '{nome}' criado.")
            st.rerun()
    
    # ===== ABAS INTERNAS =====
    tab_criar, tab_aplicar, tab_refs = st.tabs([
        " Criar Metodologia",
        " Aplicar e Histórico",
        " Referência"
    ])
    
    # ===== ABA 1: CRIAR NOVA METODOLOGIA =====
    with tab_criar:
        st.markdown("####  Criar Nova Metodologia")
        
        # Importar função para obter índices (somente para validação e tags)
        try:
            import sys
            import os
            backend_path = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            from database import obter_lista_indices_disponiveis
            
            indices_disponiveis = obter_lista_indices_disponiveis()
        except Exception as e:
            _log_dre(f"[UI] Erro ao carregar índices: {e}")
            indices_disponiveis = []

        if st.session_state.pop("met_criar_limpar_pendente", False):
            st.session_state["met_criar_nome"] = ""
            st.session_state["met_criar_descricao"] = ""
            st.session_state["met_criar_formula"] = ""
            st.session_state["met_criar_aplicavel"] = []
            st.session_state["met_criar_sugestao"] = ""

        msg_sucesso = st.session_state.pop("met_criar_msg_sucesso", "")
        if msg_sucesso:
            st.success(msg_sucesso)
        
        st.session_state.setdefault("met_criar_nome", "")
        st.session_state.setdefault("met_criar_descricao", "")
        st.session_state.setdefault("met_criar_formula", "")
        st.session_state.setdefault("met_criar_aplicavel", [])
        st.session_state.setdefault("met_criar_sugestao", "")
        st.session_state.setdefault("met_skip_keyup_sync", False)
        st.session_state.setdefault("met_formula_widget_rev", 0)

        pending_formula = st.session_state.pop("met_formula_pending_keyup", None)
        if pending_formula is not None:
            st.session_state["met_criar_formula"] = pending_formula
            keyup_key = f"met_criar_formula_keyup_{st.session_state.get('met_formula_widget_rev', 0)}"
            st.session_state[keyup_key] = pending_formula

        nome_metodologia = st.text_input(
            "Nome da Metodologia",
            placeholder="ex: Despesa com Inflação (IPCA)",
            label_visibility="collapsed",
            key="met_criar_nome"
        )

        descricao_met = st.text_area(
            "Descrição (opcional)",
            placeholder="Descreva o propósito desta metodologia",
            height=60,
            label_visibility="collapsed",
            key="met_criar_descricao"
        )

        if st_keyup is not None:
            keyup_key = f"met_criar_formula_keyup_{st.session_state.get('met_formula_widget_rev', 0)}"
            formula_keyup = st_keyup(
                "Fórmula de Cálculo",
                value=st.session_state.get("met_criar_formula", ""),
                placeholder="ex: =0.60*TD71 ou =TD71*(1+IPCA/100)",
                key=keyup_key,
                debounce=120,
            )
            if formula_keyup is not None and not st.session_state.pop("met_skip_keyup_sync", False):
                st.session_state["met_criar_formula"] = formula_keyup
            formula_metodologia = st.session_state.get("met_criar_formula", "")
        else:
            formula_metodologia = st.text_input(
                "Fórmula de Cálculo",
                placeholder="ex: =0.60*TD71 ou =TD71*(1+IPCA/100)",
                label_visibility="collapsed",
                key="met_criar_formula",
                help="Use '=' no início. Exemplos: =0.60*TD71, =MEDIA(TD71), =MEDIA_INTERNA(TD21; 0,2; -6), =TD71*(1+IPCA/100)"
            )

        contexto_formula = _obter_contexto_formula(st.session_state.dre_dados)
        tokens_base = ["SOMA", "MEDIA", "MEDIA_INTERNA", "MINIMO", "MAXIMO", "DESVIO_PADRAO"] + list(contexto_formula.keys()) + list(_preparar_contexto_com_indices(contexto_formula).keys())
        tokens_unicos = sorted(set(t for t in tokens_base if isinstance(t, str) and t))

        formula_normalizada = _normalizar_formula_usuario(formula_metodologia)
        if formula_normalizada and formula_normalizada != formula_metodologia:
            st.caption(f"Fórmula normalizada automaticamente: {formula_normalizada}")

        classificacao = _classificar_tokens_formula(formula_normalizada, st.session_state.dre_dados)
        texto_autocomplete = (formula_metodologia or "")
        match_prefixo = re.search(r"([A-Za-z_][A-Za-z0-9_]*)$", texto_autocomplete.rstrip())
        caps_trigger = bool(re.search(r"[A-Z]$", texto_autocomplete or ""))
        sugestoes = []
        if match_prefixo:
            prefixo = match_prefixo.group(1).upper()
            sugestoes = [tok for tok in tokens_unicos if tok.startswith(prefixo) and tok != prefixo][:10]
            if not sugestoes and caps_trigger:
                sugestoes = tokens_unicos[:10]
        elif texto_autocomplete and texto_autocomplete.rstrip().endswith(("=", "+", "-", "*", "/", "(", ";")):
            sugestoes = tokens_unicos[:10]

        st.markdown("**Autocomplete e Sugestões**")
        if sugestoes:
            st.caption("Selecione uma sugestão para completar o token atual")
            opcoes_sugestoes = [""] + sugestoes
            if st.session_state.get("met_criar_sugestao", "") not in opcoes_sugestoes:
                st.session_state["met_criar_sugestao"] = ""
            st.selectbox(
                "Sugestões da fórmula",
                options=opcoes_sugestoes,
                key="met_criar_sugestao",
                help="Ao selecionar, a sugestão é aplicada automaticamente na fórmula",
                on_change=_aplicar_sugestao_formula_criar
            )

            st.caption("Sugestões rápidas")
            if hasattr(st, "pills"):
                st.markdown("""
                <style>
                [data-testid="stPills"] [role="radiogroup"] {
                    gap: 8px;
                    align-items: flex-start;
                }
                [data-testid="stPills"] [role="radio"] {
                    min-width: 110px;
                    justify-content: center;
                    border-radius: 999px;
                    padding: 4px 10px;
                }
                </style>
                """, unsafe_allow_html=True)
                pill_key = f"met_criar_pills_{abs(hash((formula_metodologia or '')[-12:]))}"
                escolhido_pill = st.pills(
                    "Tokens sugeridos",
                    options=sugestoes[:12],
                    selection_mode="single",
                    label_visibility="collapsed",
                    key=pill_key,
                )
                if escolhido_pill:
                    _inserir_token_formula_criar(escolhido_pill)
                    st.rerun()
            else:
                sugestoes_rapidas = sugestoes[:6]
                colunas_rapidas = st.columns(6)
                for idx, tok in enumerate(sugestoes_rapidas):
                    with colunas_rapidas[idx]:
                        st.button(
                            tok,
                            key=f"btn_sugestao_rapida_{idx}_{tok}",
                            use_container_width=True,
                            on_click=_inserir_token_formula_criar,
                            args=(tok,)
                        )
        elif texto_autocomplete:
            st.caption("Autocomplete: digite o início de um token (ex.: TD, IPC, SOMA) para ver sugestões.")

        if st_keyup is None:
            st.caption("Dica: para autocomplete em tempo real de cada tecla, instale o pacote streamlit-keyup.")

        _renderizar_formula_inline(formula_normalizada, classificacao)
        _renderizar_tags_formula(classificacao)
        if classificacao.get("invalidos"):
            st.warning(f"Referências não reconhecidas: {', '.join(classificacao['invalidos'])}")

        # Info profissional
        col_info1, col_info2, col_info3 = st.columns(3)

        with col_info1:
            st.markdown("""
            **📝 Variáveis DRE:**
            - `TD71` - Receita Financeira
            - `TD72` - Despesa Financeira
            - `TD21` - MSD - Curva Ajustada (Volumes)
            - `TD62` - Componente TD62 (Volumes)
            """)

        with col_info2:
            st.markdown("""
            ** Funções Nativas:**
            - `SOMA(TD71)`
            - `MEDIA(TD71;TD72)`
            - `MEDIA_INTERNA(TD21; 0,2; -6)`
            - `MINIMO(TD71:TD90)`
            - `MAXIMO(TD71)`
            - `DESVIO_PADRAO(TD90; -5; 1)`
            """)

        with col_info3:
            st.markdown("""
            ** Índices econômicos:**
            - Use diretamente na fórmula quando existir na base
            - Ex.: `IPCA`, `TAXA_SELIC`, `DOLAR_PTAX`
            """)

        aplicavel_a = st.multiselect(
            "Aplicar em (linhas destino da DRE):",
            [linha.codigo for linha in ESTRUTURA_DRE if linha.tipo == "variavel"],
            key="met_criar_aplicavel",
            help="Escolha quais variáveis receberão o cálculo desta fórmula"
        )

        if st.button(" Criar Metodologia", use_container_width=True, type="primary", key="btn_criar_metodologia"):
            if nome_metodologia and formula_metodologia and aplicavel_a:
                if not formula_normalizada.startswith("="):
                    st.error("⚠️ A fórmula deve começar com '='")
                elif classificacao.get("invalidos"):
                    st.error(f"⚠️ Referências inválidas: {', '.join(classificacao['invalidos'])}")
                else:
                    try:
                        _avaliar_formula(formula_normalizada, st.session_state.dre_dados, None)

                        nova_met = {
                            "nome": nome_metodologia,
                            "descricao": descricao_met,
                            "formula": formula_normalizada,
                            "aplicavel_a": aplicavel_a,
                            "sazonalidade": {"tipo": "NENHUM"},
                            "data_criacao": datetime.now().isoformat(),
                            "data_atualizacao": datetime.now().isoformat(),
                            "aplicacoes": [],
                            "usa_indices": any(ind in formula_normalizada.upper() for ind in [i.upper() for i in indices_disponiveis])
                        }
                        st.session_state.dre_metodologias[nome_metodologia] = nova_met

                        st.session_state["met_criar_limpar_pendente"] = True
                        st.session_state["met_criar_msg_sucesso"] = f" Metodologia '{nome_metodologia}' criada!"
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro na fórmula: {str(e)}")
            else:
                st.error("⚠️ Preencha: Nome, Fórmula e selecione variáveis")
        
        # ===== EXEMPLOS PRÁTICOS =====
        st.markdown("---")
        st.markdown("#### 💡 Exemplos Práticos")
        
        col_ex1, col_ex2 = st.columns(2)
        
        with col_ex1:
            st.markdown("""
            **🏦 Receita com Inflação (IPCA)**
            ```
            =TD71 * (1 + IPCA/100)
            ```
            Aplicar a: TD71, TD90
            
            **💰 Despesa = 60% Receita**
            ```
            =0.60*TD71
            ```
            Aplicar a: TD72
            
            **📊 Média com Índice de Câmbio**
            ```
            =MEDIA(TD71) * DOLAR_PTAX
            ```
            Aplicar a: TD87, TD88
            """)
        
        with col_ex2:
            st.markdown("""
            ** Receita com Sazonalidade + SELIC**
            ```
            =MEDIA(TD71) * (1 + TAXA_SELIC/100)
            ```
            Sazonalidade: VARIÁVEL, -7 meses
            Aplicar a: TD71, TD90
            
            **💹 Múltiplos Índices**
            ```
            =0.5*SOMA(TD71) * IPCA + 0.05*TAXA_SELIC
            ```
            Aplicar a: TD90, TD91, TD95

            **📉 Volatilidade Recente com Lag**
            ```
            =TD90 + 0.2*DESVIO_PADRAO(TD90; -5; 1)
            ```
            Aplicar a: TD90
            
            ** Receita Mínima + Proteção**
            ```
            =MAXIMO(TD71; MINIMO(IPCA)*100)
            ```
            Aplicar a: TD71
            """)
        
        st.info("""
        **✨ Dicas Profissionais:**
        - Índices são **agregados para 12 meses** automaticamente
        - Use **sazonalidade** para periodos específicos
        - **Funções** funcionam com índices também: `SOMA(IPCA)`, `MEDIA(TAXA_SELIC)`
        - **Formulas complexas**: `=0.05*TD71 + 0.03*MEDIA(IPCA) + DOLAR_PTAX`
        - **Janela + lag**: `DESVIO_PADRAO(TD90; -5; 1)` usa últimos 5 meses excluindo o mês atual
        """)

    # ===== ABA 2: APLICAR METODOLOGIAS =====
    with tab_aplicar:
        st.markdown("####  Aplicar Metodologias e Histórico")
        st.markdown("""
        Selecione uma metodologia abaixo e clique em "Aplicar" para usar os filtros já selecionados no topo.
        Todos os dados serão atualizados e o histórico será registrado automaticamente.
        """)
        
        metodologias = st.session_state.dre_metodologias
        
        if not metodologias:
            st.warning("ℹ️ Nenhuma metodologia foi criada ainda. Acesse a aba ' Criar Metodologia'", icon="ℹ️")
        else:
            # ===== OBTER FILTROS JÁ SELECIONADOS NO TOPO =====
            filtros_atuais = st.session_state.get("dre_filtros", {})
            cliente_atual = filtros_atuais.get("cliente", "Todos")
            categoria_atual = filtros_atuais.get("categoria", "")
            produto_atual = filtros_atuais.get("produto", "")
            
            # Construir descrição do escopo
            escopo_display = []
            if cliente_atual and cliente_atual != "Todos":
                escopo_display.append(f"👤 {cliente_atual}")
            if categoria_atual:
                escopo_display.append(f"📁 {categoria_atual}")
            if produto_atual:
                escopo_display.append(f"📦 {produto_atual}")
            
            escopo_texto = " • ".join(escopo_display) if escopo_display else "Sem filtro específico"
            
            st.info(f"""
            ** Escopo Atual (filtros do topo):**
            
            {escopo_texto}
            """)
            
            st.markdown("---")
            st.markdown("** Metodologias Disponíveis:**")
            
            # ===== LISTAR METODOLOGIAS COM BOTÕES DE APLICAR =====
            for met_nome, met_dados in list(metodologias.items()):
                col_expand, col_apply, col_edit, col_del = st.columns([2.5, 0.8, 0.8, 0.7])
                
                with col_expand:
                    with st.expander(f"📌 {met_nome}"):
                        st.markdown(f"**Fórmula:** `{met_dados['formula']}`", help="Esta é a fórmula que será calculada")
                        
                        if met_dados.get('descricao'):
                            st.markdown(f"**Descrição:** {met_dados['descricao']}")
                        
                        st.markdown(f"**Linhas destino:** {', '.join([f'`{v}`' for v in met_dados['aplicavel_a']])}")
                        classif_met = _classificar_tokens_formula(
                            _normalizar_formula_usuario(met_dados['formula']),
                            st.session_state.get("dre_dados", {})
                        )
                        refs_formula = classif_met.get("dre", []) + classif_met.get("indices", [])
                        if refs_formula:
                            st.markdown(f"**Referências da fórmula:** {', '.join([f'`{v}`' for v in refs_formula])}")
                        
                        st.caption(f"Criada em: {met_dados['data_criacao'][:10]}")
                        st.caption(f"Atualizada em: {met_dados.get('data_atualizacao', 'N/A')[:10] if met_dados.get('data_atualizacao') else 'N/A'}")
                        
                        # Histórico
                        aplicacoes = met_dados.get("aplicacoes", [])
                        if aplicacoes:
                            st.markdown("** Histórico:**")
                            for app in aplicacoes[-5:]:
                                tipo_app = app.get("tipo", "aplicacao")
                                icone_app = "✏️" if tipo_app == "edicao" else "▶️"
                                detalhe = f" — {app.get('detalhes','')}" if app.get("detalhes") and tipo_app == "edicao" else ""
                                st.caption(f"• {icone_app} {app.get('escopo','N/A')} ({app.get('data','')[:10]}){detalhe}")
                
                with col_apply:
                    if st.button(" Aplicar", key=f"btn_app_{met_nome}", use_container_width=True, type="primary"):
                        try:
                            _log_dre(f"\n{'='*60}")
                            _log_dre(f"[APLICACAO] Iniciando: {met_nome}")
                            _log_dre(f"[APLICACAO] Escopo: {escopo_texto}")
                            _log_dre(f"{'='*60}")
                            
                            # ===== APLICAR METODOLOGIA =====
                            dre_dados = deepcopy(st.session_state.dre_dados)
                            formula_aplicar = _normalizar_formula_usuario(met_dados.get('formula', ''))
                            classif = _classificar_tokens_formula(formula_aplicar, dre_dados)
                            if classif.get("invalidos"):
                                st.error(f"⚠️ Referências inválidas na metodologia '{met_nome}': {', '.join(classif['invalidos'])}")
                                continue
                            
                            aplicadas_a = []
                            sem_efeito = []
                            for var_codigo in met_dados['aplicavel_a']:
                                if var_codigo in dre_dados:
                                    ok, msg, alterou = _aplicar_metodologia_em_linha(
                                        dre_dados,
                                        var_codigo,
                                        met_nome,
                                        met_dados,
                                        modo_periodo="Todos",
                                        mes_inicio=1,
                                        mes_fim=12,
                                    )
                                    if ok:
                                        aplicadas_a.append(var_codigo)
                                        if not alterou:
                                            sem_efeito.append(var_codigo)
                                    else:
                                        st.error(f"{var_codigo}: {msg}")
                            
                            # Armazenar série computada para encadeamento entre metodologias
                            try:
                                _serie_met = _avaliar_formula(
                                    _normalizar_formula_usuario(met_dados.get('formula', '')),
                                    dre_dados,
                                    sazonalidade=met_dados.get("sazonalidade"),
                                )
                                st.session_state.dre_metodologias[met_nome]["serie_computada"] = _serie_met
                            except Exception:
                                pass

                            # ===== SALVAR E RECALCULAR =====
                            st.session_state.dre_dados = dre_dados
                            _calcular_totalizadores()
                            _persistir_linhas_dre()
                            
                            # ===== REGISTRAR APLICAÇÃO =====
                            novo_registro = {
                                "data": datetime.now().isoformat(),
                                "escopo": escopo_texto,
                                "variáveis": aplicadas_a,
                                "filtros": {
                                    "cliente": cliente_atual,
                                    "categoria": categoria_atual,
                                    "produto": produto_atual
                                }
                            }
                            
                            if "aplicacoes" not in st.session_state.dre_metodologias[met_nome]:
                                st.session_state.dre_metodologias[met_nome]["aplicacoes"] = []
                            
                            st.session_state.dre_metodologias[met_nome]["aplicacoes"].append(novo_registro)
                            
                            _log_dre(f"[APLICACAO]  SUCESSO")
                            _log_dre(f"{'='*60}\n")
                            
                            st.success(f"""
                             **Aplicado com Sucesso!**
                            
                            • Variáveis: {', '.join(aplicadas_a)}
                            • Escopo: {escopo_texto}
                            • Timestamp: {novo_registro['data'][:19].replace('T', ' ')}
                            """)
                            if sem_efeito:
                                diag_sem_efeito = _diagnosticar_formula_sem_efeito(met_dados.get('formula', ''), dre_dados)
                                st.warning(
                                    f"Sem alteração de valores em: {', '.join(sem_efeito)}. "
                                    f"Verifique se a fórmula está resultando em zero no contexto atual.{diag_sem_efeito}"
                                )
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
                            _log_dre(f"[APLICACAO] ❌ ERRO: {e}")
                
                # ===== BOTÃO EDITAR =====
                with col_edit:
                    if st.button("✏️ Editar", key=f"btn_edit_{met_nome}", use_container_width=True):
                        st.session_state[f"editando_{met_nome}"] = True
                        st.rerun()
                
                with col_del:
                    if st.button("🗑️", key=f"btn_del_{met_nome}", use_container_width=True):
                        dre_state = deepcopy(st.session_state.get("dre_dados", {}))
                        for cod_linha in list(dre_state.keys()):
                            _remover_metodologia_especifica_da_linha(dre_state, cod_linha, met_nome)

                        st.session_state.dre_dados = dre_state
                        _calcular_totalizadores()
                        _persistir_linhas_dre()

                        del st.session_state.dre_metodologias[met_nome]
                        st.session_state["dre_msg_sucesso_exclusao_met"] = (
                            f"Metodologia '{met_nome}' excluída e removida das linhas aplicadas."
                        )
                        st.rerun()

                if st.session_state.get("dre_msg_sucesso_exclusao_met"):
                    st.success(st.session_state.get("dre_msg_sucesso_exclusao_met"))
                    del st.session_state["dre_msg_sucesso_exclusao_met"]
                
                # ===== MODO EDIÇÃO =====
                if st.session_state.get(f"editando_{met_nome}", False):
                    st.divider()
                    st.markdown(f"### Editando: {met_nome}")
                    
                    # 🔑 PARÂMETROS DE SAZONALIDADE (FORA do form para ser dinâmico)
                    with st.expander("⚙️ Parâmetros de Sazonalidade", expanded=False):
                        nova_saz = criar_interface_sazonalidade(
                            rotulo_prefix=f"edit_{met_nome}",
                            valor_padrao=met_dados.get('sazonalidade', {"tipo": "NENHUM"})
                        )
                    
                    with st.form(f"form_edit_{met_nome}"):
                        novo_nome = st.text_input(
                            "Nome",
                            value=met_dados['nome'],
                            label_visibility="collapsed"
                        )
                        
                        novo_descricao = st.text_area(
                            "Descrição",
                            value=met_dados.get('descricao', ''),
                            height=60,
                            label_visibility="collapsed"
                        )
                        
                        nova_formula = st.text_input(
                            "Fórmula",
                            value=met_dados['formula'],
                            label_visibility="collapsed"
                        )
                        
                        nova_aplicavel = st.multiselect(
                            "Linhas destino",
                            [linha.codigo for linha in ESTRUTURA_DRE if linha.tipo == "variavel"],
                            default=met_dados['aplicavel_a'],
                            key=f"vars_edit_{met_nome}"
                        )
                        
                        # Botões
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("Salvar Alterações", use_container_width=True, type="primary"):
                                try:
                                    novo_nome = (novo_nome or "").strip() or met_nome
                                    nova_formula = _normalizar_formula_usuario(nova_formula)
                                    old_aplicavel = set(met_dados.get("aplicavel_a", []))
                                    new_aplicavel = set(nova_aplicavel or [])

                                    # Atualizar metodologia
                                    st.session_state.dre_metodologias[met_nome] = {
                                        "nome": novo_nome,
                                        "descricao": novo_descricao,
                                        "formula": nova_formula,
                                        "aplicavel_a": nova_aplicavel,
                                        "sazonalidade": nova_saz,
                                        "data_criacao": met_dados['data_criacao'],
                                        "data_atualizacao": datetime.now().isoformat(),
                                        "aplicacoes": met_dados.get('aplicacoes', [])
                                    }
                                    
                                    # Se o nome mudou, reorganizar dicionário
                                    if novo_nome != met_nome:
                                        st.session_state.dre_metodologias[novo_nome] = st.session_state.dre_metodologias.pop(met_nome)

                                    # Sincronizar linhas já afetadas por essa metodologia no modelo acumulativo:
                                    # - remove apenas essa metodologia onde deixou de ser aplicável
                                    # - renomeia somente essa metodologia na pilha da linha
                                    dre_state = st.session_state.get("dre_dados", {})
                                    for cod_linha, dados_linha in dre_state.items():
                                        mets_linha = dados_linha.get("metodologias_aplicadas", [])
                                        nomes_linha = [m.get("nome") for m in mets_linha if isinstance(m, dict)]
                                        if met_nome not in nomes_linha:
                                            # fallback legado
                                            met_legada = dados_linha.get("metodologia")
                                            if not (isinstance(met_legada, dict) and met_legada.get("nome") == met_nome):
                                                continue

                                        if cod_linha not in new_aplicavel:
                                            _remover_metodologia_especifica_da_linha(dre_state, cod_linha, met_nome)
                                        else:
                                            if novo_nome != met_nome:
                                                for m in dados_linha.get("metodologias_aplicadas", []):
                                                    if isinstance(m, dict) and m.get("nome") == met_nome:
                                                        m["nome"] = novo_nome
                                            _recalcular_linha_por_metodologias(dre_state, cod_linha)

                                    st.session_state.dre_dados = dre_state
                                    _calcular_totalizadores()
                                    _persistir_linhas_dre()

                                    # Registrar evento de edição no histórico da metodologia
                                    _filtros_edit = st.session_state.get("dre_filtros", {})
                                    _partes_esc = [
                                        f"👤 {_filtros_edit.get('cliente','')}" if _filtros_edit.get('cliente','Todos') != 'Todos' else "",
                                        f"📁 {_filtros_edit.get('categoria','')}" if _filtros_edit.get('categoria') else "",
                                        f"📦 {_filtros_edit.get('produto','')}" if _filtros_edit.get('produto') else "",
                                    ]
                                    _escopo_edit = " • ".join(p for p in _partes_esc if p) or "Sem filtro"
                                    _detalhes_edit = []
                                    if novo_nome != met_nome:
                                        _detalhes_edit.append(f"Renomeado: {met_nome} → {novo_nome}")
                                    if set(nova_aplicavel) != old_aplicavel:
                                        _detalhes_edit.append(f"Linhas: {sorted(old_aplicavel)} → {sorted(new_aplicavel)}")
                                    _registro_edicao = {
                                        "tipo": "edicao",
                                        "data": datetime.now().isoformat(),
                                        "escopo": _escopo_edit,
                                        "variáveis": nova_aplicavel,
                                        "detalhes": "; ".join(_detalhes_edit) if _detalhes_edit else "Parâmetros atualizados",
                                    }
                                    _apps = st.session_state.dre_metodologias.get(novo_nome, {}).get("aplicacoes", [])
                                    _apps.append(_registro_edicao)
                                    st.session_state.dre_metodologias[novo_nome]["aplicacoes"] = _apps

                                    st.session_state[f"editando_{met_nome}"] = False
                                    st.success(" Metodologia atualizada!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro ao salvar: {str(e)}")
                        
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state[f"editando_{met_nome}"] = False
                                st.rerun()
    
    # ===== ABA 3: REFERÊNCIA DE FUNÇÕES =====
    with tab_refs:
        st.markdown("####  Documentação de Funções Nativas")
        st.markdown("""
        Guia completo de como usar as funções nativas nas fórmulas de metodologia.
        """)
        
        # ===== CARDS COM CADA FUNÇÃO =====
        for idx, nome_func in enumerate(["SOMA", "MEDIA", "MEDIA_INTERNA", "MINIMO", "MAXIMO", "DESVIO_PADRAO"]):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                with st.container(border=True):
                    st.markdown(f"### {nome_func}()")
                    st.markdown(DESCRICOES_FUNCOES.get(nome_func, ""))
                    
                    st.markdown("**Sintaxe:**")
                    st.code(EXEMPLOS_FUNCOES.get(nome_func, ""), language="text")
            
            with col2:
                with st.container(border=True):
                    st.markdown(f"### Exemplos de {nome_func}()")
                    
                    if nome_func == "SOMA":
                        st.markdown("""
                        ```
                        =SOMA(TD71)
                        =0.1*SOMA(TD71)
                        =SOMA(TD71:TD90)
                        =SOMA(TD71;TD72;TD87)
                        ```
                        """)
                    elif nome_func == "MEDIA":
                        st.markdown("""
                        ```
                        =MEDIA(TD71)
                        =MEDIA(TD71;TD72)
                        =MEDIA(TD71:TD90)
                        =0.5*MEDIA(TD71)
                        ```
                        """)
                    elif nome_func == "MEDIA_INTERNA":
                        st.markdown("""
                        ```
                        =MEDIA_INTERNA(TD21; 0,2)
                        =MEDIA_INTERNA(TD21; 0,2; -6)
                        =MEDIA_INTERNA(TD21; 0,2; -6; 1)
                        =TRIMMEAN(TD21; 0,2; -6)
                        ```
                        """)
                    elif nome_func == "MINIMO":
                        st.markdown("""
                        ```
                        =MINIMO(TD71)
                        =MINIMO(TD71;TD72;TD87)
                        =MINIMO(TD71:TD90)
                        =100-MINIMO(TD71)
                        ```
                        """)
                    elif nome_func == "MAXIMO":
                        st.markdown("""
                        ```
                        =MAXIMO(TD71)
                        =MAXIMO(TD71;TD72;TD87)
                        =MAXIMO(TD71:TD90)
                        =MAXIMO(TD71)*0.05
                        ```
                        """)
                    elif nome_func == "DESVIO_PADRAO":
                        st.markdown("""
                        ```
                        =DESVIO_PADRAO(TD90)
                        =DESVIO_PADRAO(TD90; -5)
                        =DESVIO_PADRAO(TD90; -5; 1)
                        =TD90 + 0.1*DESVIO_PADRAO(TD90; -3)
                        ```
                        """)
        
        # ===== SINTAXE DE ARGUMENTOS =====
        st.divider()
        st.markdown("####  Formatos de Argumentos")
        
        col_arg1, col_arg2, col_arg3 = st.columns(3)
        
        with col_arg1:
            st.markdown("""
            **Um Código:**
            
            ```
            SOMA(TD71)
            ```
            
            Processa os 12 meses de TD71
            """)
        
        with col_arg2:
            st.markdown("""
            **Múltiplos (;):**
            
            ```
            MEDIA(TD71;TD72;TD87)
            ```
            
            Combina valores de múltiplos códigos
            """)
        
        with col_arg3:
            st.markdown("""
            **Intervalo (:):**
            
            ```
            MINIMO(TD71:TD90)
            ```
            
            Intervalo contínuo de códigos
            """)

        st.markdown("""
        **Sintaxe especial da MEDIA_INTERNA**

        ```
        MEDIA_INTERNA(referencia; percentual; janela_opcional; lag_opcional)
        ```

        Exemplo de uso mensal:
        - `MEDIA_INTERNA(TD21; 0,2; -6)` → media interna dos ultimos 6 meses de `TD21`
        - `TRIMMEAN(TD21; 0,2; -6)` → alias equivalente
        """)
        
        # ===== PROCESSAMENTO =====
        st.divider()
        st.markdown("#### Ordem de Processamento")
        
        st.markdown("""
        As fórmulas são processadas em três etapas:
        
        **1️⃣ Funções Nativas**
        - Todas as funções (SOMA, MEDIA, MEDIA_INTERNA etc) são avaliadas PRIMEIRO
        - Cada função pode usar o valor do mês corrente ou uma janela temporal da referência
        - Exemplo: `MEDIA_INTERNA(TD21; 0,2; -6)` calcula, em cada mês, a media interna dos ultimos 6 meses de `TD21`
        
        **2️⃣ Substituição**
        - O resultado mensal de cada função substitui a chamada função naquele mês
        - Exemplo: `0.05*SOMA(TD71)` → `0.05*valor_da_funcao_no_mes`
        
        **3️⃣ Cálculo Mês-a-Mês**
        - A fórmula final é calculada para cada um dos 12 meses
        - Variáveis (TD71, TD72) usam seus valores mensais
        - Resultado: 12 valores (um por mês)
        
        **Exemplo Completo:**
        ```
        Fórmula: =0.05*SOMA(TD71)+0.03*MEDIA_INTERNA(TD21; 0,2; -6)
        
        Passo 1: para cada mês, SOMA(TD71) e MEDIA_INTERNA(TD21; 0,2; -6) geram um valor
        Passo 2: a expressão final usa os dois resultados mensais
        Passo 3: Para cada mês:
          - Mês 1: 0.05*valor_soma_jan + 0.03*valor_media_interna_jan
          - Mês 2: 0.05*valor_soma_fev + 0.03*valor_media_interna_fev
          - ... (total 12 valores)
        ```
        """)
        
        st.info("""
        💡 **Dica:** Abra o console (terminal) para ver logs de processamento da fórmula.
        Os logs mostram cada passo e ajudam a depurar fórmulas complexas.
        """)


def _renderizar_analise():
    """Renderiza página de análise com gráficos e métricas"""
    
    st.markdown("### Análise e Relatórios")
    
    dre_dados = st.session_state.dre_dados
    
    # ===== MÉTRICAS PRINCIPAIS =====
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    td71_total = sum(dre_dados.get("TD71", {}).get("valores", [0]*12))
    td72_total = sum(dre_dados.get("TD72", {}).get("valores", [0]*12))
    mfb_total = sum(dre_dados.get("MFB", {}).get("valores", [0]*12))
    
    with col_m1:
        st.metric(
            " Receita Financeira (TD71)",
            fmt_br(td71_total),
            delta=f"Média: R$ {fmt_br(td71_total/12)}/mês"
        )
    
    with col_m2:
        st.metric(
            "💰 Despesa (TD72)",
            fmt_br(td72_total),
            delta=f"Média: R$ {fmt_br(td72_total/12)}/mês"
        )
    
    with col_m3:
        margem = ((mfb_total / td71_total * 100) if td71_total != 0 else 0)
        st.metric(
            "📊 Margem Financeira",
            f"{margem:.1f}%",
            delta=f"Total: R$ {fmt_br(mfb_total)}"
        )
    
    with col_m4:
        st.metric(
            "📅 Período",
            "12 Meses",
            delta=f"{datetime.now().year}"
        )
    
    st.divider()
    
    # ===== GRÁFICOS =====
    col_grf1, col_grf2 = st.columns(2, gap="large")
    
    with col_grf1:
        st.markdown("#### Evolução Mensal - Receita vs Despesa")
        
        dados_grafico = pd.DataFrame({
            "Mês": MESES_ABR_LIST,
            "Receita (TD71)": dre_dados.get("TD71", {}).get("valores", [0]*12),
            "Despesa (TD72)": dre_dados.get("TD72", {}).get("valores", [0]*12),
        })
        
        st.line_chart(dados_grafico.set_index("Mês"), use_container_width=True)
    
    with col_grf2:
        st.markdown("#### 💹 Margens - MFB e MFBE")
        
        dados_margens = pd.DataFrame({
            "Mês": MESES_ABR_LIST,
            "MFB": dre_dados.get("MFB", {}).get("valores", [0]*12),
            "MFBE": dre_dados.get("MFBE", {}).get("valores", [0]*12),
        })
        
        st.line_chart(dados_margens.set_index("Mês"), use_container_width=True)
    
    st.divider()
    
    # ===== COMPOSIÇÃO DE RECEITA =====
    st.markdown("#### 💰 Composição da Receita (Total Anual)")
    
    componentes = {
        "Receita Financeira": sum(dre_dados.get("TD71", {}).get("valores", [0]*12)),
        "Receita Oportunidade": sum(dre_dados.get("TD90", {}).get("valores", [0]*12)),
        "Variação Cambial": sum(dre_dados.get("TD70", {}).get("valores", [0]*12)),
    }
    
    # Remover valores zero e negativos
    componentes = {k: v for k, v in componentes.items() if v > 0}
    
    if componentes:
        df_comp = pd.DataFrame(list(componentes.items()), columns=["Componente", "Valor"])
        st.bar_chart(df_comp.set_index("Componente"), use_container_width=True)
    else:
        st.info("Nenhuma receita registrada")
    
    st.divider()
    
    # ===== TABELA DE RESUMO =====
    st.markdown("####  Resumo Detalhado (Totais Anuais)")
    
    resumo_dados = []
    for linha in ESTRUTURA_DRE:
        codigo = linha.codigo
        valores = dre_dados.get(codigo, {}).get("valores", [0]*12)
        total = sum(valores)
        media = total / 12 if len(valores) > 0 else 0
        tipo = dre_dados.get(codigo, {}).get("tipo", "")
        
        # Mostrar todas as linhas
        resumo_dados.append({
            "Código": f"**{codigo}**" if tipo == "totalizador" else codigo,
            "Descrição": dre_dados.get(codigo, {}).get("descricao", ""),
            "Total Anual": fmt_br(total),
            "Média Mensal": fmt_br(media),
            "Tipo": "📊 Totalizador" if tipo == "totalizador" else "📝 Variável",
        })
    
    df_resumo = pd.DataFrame(resumo_dados)
    
    st.dataframe(
        df_resumo, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Código": st.column_config.TextColumn(width=80),
            "Descrição": st.column_config.TextColumn(width=250),
            "Total Anual": st.column_config.TextColumn(width=120),
            "Média Mensal": st.column_config.TextColumn(width=120),
            "Tipo": st.column_config.TextColumn(width=120),
        }
    )
    
    st.divider()
    
    # ===== EXPORTAÇÃO =====
    st.markdown("#### 💾 Exportar Dados")
    
    col_exp1, col_exp2 = st.columns(2, gap="large")
    
    with col_exp1:
        if st.button("📥 Exportar para JSON", use_container_width=True, key="exp_json"):
            json_data = {
                "data_criacao": datetime.now().isoformat(),
                "filtros": st.session_state.dre_filtros,
                "dre": {}
            }
            
            for linha in ESTRUTURA_DRE:
                json_data["dre"][linha.codigo] = {
                    "descricao": linha.descricao,
                    "tipo": linha.tipo,
                    "valores": dre_dados.get(linha.codigo, {}).get("valores", [0]*12),
                    "formula": dre_dados.get(linha.codigo, {}).get("formula")
                }
            
            st.download_button(
                "⬇️ Download JSON",
                data=json.dumps(json_data, indent=2, ensure_ascii=False),
                file_name=f"dre_gerencial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    with col_exp2:
        if st.button("📥 Exportar para CSV", use_container_width=True, key="exp_csv"):
            csv_lines = ["Código,Descrição,Tipo," + ",".join(MESES_ABR_LIST)]
            
            for linha in ESTRUTURA_DRE:
                valores = dre_dados.get(linha.codigo, {}).get("valores", [0]*12)
                tipo_label = "Totalizador" if linha.tipo == "totalizador" else "Variável"
                csv_lines.append(
                    f"{linha.codigo},{linha.descricao},{tipo_label}," + 
                    ",".join(str(int(v)) for v in valores)
                )
            
            st.download_button(
                "⬇️ Download CSV",
                data="\n".join(csv_lines),
                file_name=f"dre_gerencial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )


def _renderizar_indices_economicos():
    """Renderiza a aba de visualização de Índices Econômicos"""
    
    st.markdown("### Índices Econômicos Disponíveis")
    
    # Carregar índices do backend
    caminho_backend = os.path.join(os.path.dirname(__file__), "..", "..")
    sys.path.insert(0, caminho_backend)
    
    try:
        from backend.database import carregar_indices_json, obter_metadados_ultimo_upload_indices
        
        # Carregar dados de índices
        dados_indices = carregar_indices_json()
        
        if dados_indices is None or not dados_indices.get("indices", {}):
            st.warning(
                "📭 Nenhum índice econômico carregado ainda.\n\n"
                "Por favor, faça upload de um arquivo Excel com a aba 'INDICES_TESOU' "
                "na página de **Upload de Dados** para visualizar os índices aqui."
            )
            return
        
        # Obter metadata
        metadata = obter_metadados_ultimo_upload_indices()
        
        # ===== INFORMAÇÕES GERAIS =====
        st.markdown("####  Informações Gerais")
        
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        
        with col_info1:
            total_registros = dados_indices["metadata"].get("total_registros", 0)
            st.metric("📊 Total de Registros", f"{total_registros:,}")
        
        with col_info2:
            indices_unicos = dados_indices["metadata"].get("indices_unicos", 0)
            st.metric("🏷️ Índices Únicos", f"{indices_unicos}")
        
        with col_info3:
            total_colunas = len(dados_indices["metadata"].get("colunas", []))
            st.metric("📐 Total de Colunas", f"{total_colunas}")
        
        with col_info4:
            if metadata:
                data_upload = metadata.get("data_upload", "N/A")
                st.metric("📅 Último Upload", data_upload.split("T")[0] if data_upload != "N/A" else "N/A")
        
        st.divider()
        
        # ===== FILTRO POR ÍNDICE =====
        st.markdown("####  Filtrar por Índice")
        
        # Obter lista de índices únicos
        indices_disponiveis = sorted(dados_indices.get("indices", {}).keys())
        
        if not indices_disponiveis:
            st.error("Nenhum índice encontrado nos dados carregados.")
            return
        
        col_filtro1, col_filtro2 = st.columns([2, 1])
        
        with col_filtro1:
            indice_selecionado = st.selectbox(
                "Selecione o Índice:",
                indices_disponiveis,
                key="dre_indice_select"
            )
        
        with col_filtro2:
            # Botão para atualizar
            if st.button("🔄 Atualizar", use_container_width=True):
                st.rerun()
        
        st.divider()
        
        # ===== DADOS DO ÍNDICE SELECIONADO =====
        if indice_selecionado:
            dados_indice = dados_indices["indices"].get(indice_selecionado, [])
            
            if dados_indice:
                st.markdown(f"####  Dados do Índice: **{indice_selecionado}**")
                
                # Converter para DataFrame
                df_indice = pd.DataFrame(dados_indice)
                
                # Informações sobre o índice
                col_info_ind1, col_info_ind2, col_info_ind3 = st.columns(3)
                
                with col_info_ind1:
                    st.metric("📊 Registros", f"{len(df_indice):,}")
                
                with col_info_ind2:
                    # Tentar obter data mínima e máxima
                    try:
                        datas = pd.to_datetime(df_indice["DT_ALVO"], errors="coerce").dropna()
                        if len(datas) > 0:
                            data_min = datas.min().strftime("%d/%m/%Y")
                            st.metric("📅 Período (Início)", data_min)
                    except:
                        st.metric("📅 Período (Início)", "N/A")
                
                with col_info_ind3:
                    try:
                        datas = pd.to_datetime(df_indice["DT_ALVO"], errors="coerce").dropna()
                        if len(datas) > 0:
                            data_max = datas.max().strftime("%d/%m/%Y")
                            st.metric("📅 Período (Fim)", data_max)
                    except:
                        st.metric("📅 Período (Fim)", "N/A")
                
                st.divider()
                
                # Opções de visualização
                col_viz1, col_viz2 = st.columns(2)
                
                with col_viz1:
                    st.markdown("**Primeiras 50 linhas:**")
                    
                    # Selecionar colunas importantes
                    colunas_importante = []
                    for col in ["DT_ALVO", "DT_PRJ", "VL_PJTD", "NM_IN"]:
                        if col in df_indice.columns:
                            colunas_importante.append(col)
                    
                    # Adicionar outras colunas
                    outras_colunas = [c for c in df_indice.columns if c not in colunas_importante]
                    colunas_exibir = colunas_importante + outras_colunas
                    
                    st.dataframe(
                        df_indice[colunas_exibir].head(50),
                        use_container_width=True,
                        hide_index=True
                    )
                
                with col_viz2:
                    st.markdown("**Estatísticas:**")
                    
                    # Mostrar estatísticas das colunas numéricas
                    colunas_numericas = df_indice.select_dtypes(include=[np.number]).columns
                    
                    if len(colunas_numericas) > 0:
                        stats_data = {
                            "Coluna": [],
                            "Mínimo": [],
                            "Máximo": [],
                            "Média": [],
                            "Desvio Padrão": []
                        }
                        
                        for col in colunas_numericas:
                            stats_data["Coluna"].append(col)
                            stats_data["Mínimo"].append(f"{df_indice[col].min():.2f}")
                            stats_data["Máximo"].append(f"{df_indice[col].max():.2f}")
                            stats_data["Média"].append(f"{df_indice[col].mean():.2f}")
                            stats_data["Desvio Padrão"].append(f"{df_indice[col].std():.2f}")
                        
                        df_stats = pd.DataFrame(stats_data)
                        st.dataframe(df_stats, use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhuma coluna numérica encontrada para análise estatística.")
                
                st.divider()
                
                # ===== GRÁFICO DE VALORES =====
                try:
                    if "DT_ALVO" in df_indice.columns and "VL_PJTD" in df_indice.columns:
                        st.markdown("**Evolução de Valores**")
                        
                        # Preparar dados para gráfico
                        df_grafico = df_indice[["DT_ALVO", "VL_PJTD"]].copy()
                        df_grafico["DT_ALVO"] = pd.to_datetime(df_grafico["DT_ALVO"], errors="coerce")
                        df_grafico = df_grafico.dropna().sort_values("DT_ALVO")
                        
                        if len(df_grafico) > 0:
                            df_grafico_pivot = df_grafico.set_index("DT_ALVO")
                            st.line_chart(df_grafico_pivot, use_container_width=True)
                        else:
                            st.info("Não há dados suficientes para gráfico.")
                except Exception as e:
                    st.warning(f"Erro ao gerar gráfico: {str(e)}")
                
                st.divider()
                
                # ===== EXPORTAR DADOS DO ÍNDICE =====
                st.markdown("#### 💾 Exportar Dados do Índice")
                
                col_exp_ind1, col_exp_ind2 = st.columns(2)
                
                with col_exp_ind1:
                    csv_export = df_indice.to_csv(index=False, sep=";")
                    st.download_button(
                        "📥 Baixar como CSV",
                        data=csv_export,
                        file_name=f"indice_{indice_selecionado}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col_exp_ind2:
                    json_export = df_indice.to_json(orient="records", force_ascii=False)
                    st.download_button(
                        "📥 Baixar como JSON",
                        data=json_export,
                        file_name=f"indice_{indice_selecionado}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
            else:
                st.error(f"Nenhum dado encontrado para o índice '{indice_selecionado}'")
    
    except ImportError as e:
        st.error(f"❌ Erro ao carregar módulos do backend: {str(e)}")
        st.info("Verifique se o backend está configurado corretamente.")
    except Exception as e:
        st.error(f"❌ Erro ao carregar índices: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


# ============================================================================
# CHAMAR RENDERIZAR NO NÍVEL SUPERIOR PARA STREAMLIT MULTIPAGE
# ============================================================================
if __name__ == "__main__":
    renderizar()
else:
    # Quando importado, renderizar é chamado pelo app.py
    pass
