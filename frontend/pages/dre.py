"""
Página de DRE Gerencial (Demonstrativo de Resultado Gerencial)
Permite simular e editar variáveis da DRE com layout mês-a-mês
Suporta metodologias de cálculo automáticas
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import sys
import os
import json
import re
from datetime import datetime
from copy import deepcopy
from typing import Union, Dict

# Importar utilitários
from utils_ext.css import make_stylesheet
from utils_ext.formatters import fmt_br
from utils_ext.series import (
    _norm_txt, _mes_to_num, _variacao_mensal
)
from utils_ext.constants import (
    MESES_FULL, MESES_NUM, MESES_ABR, MESES_ABR_LIST, COR_ANALITICA, COR_MERCADO, 
    COR_AJUSTADA, COR_RLZD_BASE, CAT_COLORS
)
from utils_ext.calc_functions import (
    FUNCOES_NATIVAS, DESCRICOES_FUNCOES, EXEMPLOS_FUNCOES, 
    evaluar_funcao_em_formula, obter_documentacao_funcoes
)
from utils_ext.icons import get_icon, render_icon_header, render_section_divider, render_info_box, render_page_header

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_manager import get_dados_upload, carregar_curva_ajustada, init_data_state
from services.aggregations import _carregar_curvas_por_ano


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
        # Carregar TD21 da simulação se disponível
        _carregar_td21_volumes()
    
    if "dre_metodologias" not in st.session_state:
        st.session_state.dre_metodologias = {}
    
    if "dre_filtros" not in st.session_state:
        st.session_state.dre_filtros = {
            "cliente": "Todos",
            "categoria": "",
            "produto": ""
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


def _carregar_td21_volumes(cliente: str = "Todos", categoria: str = "", produto: str = "", ano: int = 2026):
    """
    Carrega valores de TD21 (Curva Ajustada) para a seção de volumes financeiros.
    """
    try:
        # Verificar se dre_volumes_dados foi inicializado
        if "dre_volumes_dados" not in st.session_state:
            return
        
        curva_ajustada = st.session_state.get("ajustada", [0.0] * 12)
        if len(curva_ajustada) == 24:
            curva_ajustada = curva_ajustada[:12]
        
        if st.session_state.dre_volumes_dados.get("TD21"):
            st.session_state.dre_volumes_dados["TD21"]["valores"] = list(curva_ajustada)
    except Exception as e:
        print(f"[DRE] Erro ao carregar TD21: {e}")


def _carregar_td71_simulacao(cliente: str = "Todos", categoria: str = "", produto: str = "", ano: int = 2026):
    """
    Carrega valores de TD71 a partir da curva ajustada.
    Tenta em ordem:
    1. Carregar do BACKEND SCHEMA (novo - sincronizado com Simulador)
    2. Carregar curva persistida no session_state
    3. Carregar de st.session_state.ajustada (simulador)
    4. Carregar curva analítica do DataFrame de upload
    5. Deixar em zero
    """
    try:
        # 0. NOVO: Tentar carregar do BACKEND SCHEMA primeiro
        if cliente and cliente != "Todos" and categoria and produto:
            try:
                usuario_id = st.session_state.get("usuario_id", "")
                if usuario_id:
                    from data_manager import obter_curva_do_backend
                    curva_backend = obter_curva_do_backend(usuario_id, cliente, categoria, produto, ano)
                    if curva_backend and len(curva_backend) == 12 and any(v != 0.0 for v in curva_backend):
                        st.session_state.dre_dados["TD71"]["valores"] = list(curva_backend)
                        print(f"[DRE]  TD71 carregado do BACKEND: {cliente}::{categoria}::{produto}::{ano}")
                        return
            except Exception as e:
                print(f"[DRE] Aviso ao carregar do backend: {e}")
        
        # 1. Tentar carregar curva persistida para essa combinação específica
        if cliente or categoria or produto:
            curva_persistida = carregar_curva_ajustada(cliente, categoria, produto)
            if curva_persistida and len(curva_persistida) == 12:
                st.session_state.dre_dados["TD71"]["valores"] = list(curva_persistida)
                print(f"[DRE] TD71 carregado de curva persistida: {cliente}::{categoria}::{produto}")
                return
        
        # 2. Tentar carregar do session_state do simulador (usuário veio direto do simulador)
        ajustada = st.session_state.get("ajustada", None)
        if ajustada and len(ajustada) == 12:
            st.session_state.dre_dados["TD71"]["valores"] = list(ajustada)
            print("[DRE] TD71 sincronizado com simulador (session_state.ajustada)")
            return
        
        # 3. Tentar carregar curva analítica do DataFrame de upload
        if cliente and cliente != "Todos" and categoria and produto:
            try:
                df_upload = get_dados_upload()
                if df_upload is not None and not df_upload.empty:
                    ana_curva, mer_curva, ajs_curva = _carregar_curvas_por_ano(df_upload, cliente, categoria, produto, ano)
                    # Usar a curva analítica como fallback
                    if ana_curva and len(ana_curva) == 12 and any(v != 0.0 for v in ana_curva):
                        st.session_state.dre_dados["TD71"]["valores"] = list(ana_curva)
                        print(f"[DRE] TD71 carregado de curva analítica (upload): {cliente}::{categoria}::{produto}::{ano}")
                        return
            except Exception as e:
                print(f"[DRE] Erro ao carregar curva analítica: {e}")
        
        # 4. Se nada funcionar, deixa em zero (será preenchido manualmente)
        print("[DRE] Nenhuma curva encontrada para TD71 - valores em zero")
        
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


def _avaliar_formula(formula: str, dre_dados: dict, sazonalidade: Union[Dict, int, None] = None) -> list:
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
    
    # Preparar contexto simplificado para substituição de variáveis: {codigo: [12 valores]}
    contexto_simples = {}
    for codigo, dados in dre_dados.items():
        valores = dados.get("valores", [0.0] * 12)
        contexto_simples[codigo] = valores
    
    print(f"[DRE] Processando fórmula: {formula}")
    print(f"[DRE] Sazonalidade: {sazonalidade}")
    print(f"[DRE] Variáveis disponíveis: {list(dre_dados.keys())}")
    
    # ===== PROCESSAR FUNÇÕES NATIVAS =====
    # Padrão regex para encontrar funções: SOMA(ARGS), MEDIA(ARGS), etc
    padrao_funcoes = r'(SOMA|MEDIA|MINIMO|MAXIMO)\((.*?)\)'
    
    # Mapeamento de placeholders para resultados das funções
    # ex: __FUNC_0__ → [valores dos 12 meses]
    funcoes_dinamicas = {}
    formula_processada = formula_limpa
    
    matches = list(re.finditer(padrao_funcoes, formula_limpa, re.IGNORECASE))
    
    for idx, match in enumerate(matches):
        nome_funcao = match.group(1).upper()
        argumentos = match.group(2)
        
        print(f"[DRE] Encontrada função nativa: {nome_funcao}({argumentos})")
        
        # 🔑 NOVO: Chamar função dinâmica por mês
        from utils_ext.calc_functions import evaluar_funcao_dinamica_por_mes
        
        valores_dinamicos = evaluar_funcao_dinamica_por_mes(
            nome_funcao, 
            argumentos, 
            dre_dados,
            saz=sazonalidade
        )
        
        # Armazenar resultado
        placeholder = f"__FUNC_{idx}__"
        funcoes_dinamicas[placeholder] = valores_dinamicos
        
        # Substituir na fórmula com placeholder
        funcao_str = f"{nome_funcao}({argumentos})"
        formula_processada = formula_processada.replace(funcao_str, placeholder)
        
        print(f"[DRE] → Resultado (12 meses): {valores_dinamicos[:3]}...")
    
    print(f"[DRE] Fórmula final (antes do mês-a-mês): {formula_processada}")
    
    # ===== AVALIAR FÓRMULA PARA CADA MÊS =====
    valores_resultado = []
    
    for mes_idx in range(12):
        # Construir expressão para este mês específico
        expr = formula_processada
        
        # Substituir placeholders de funções com valores do mês
        for placeholder, valores_12 in funcoes_dinamicas.items():
            valor_mes = valores_12[mes_idx] if mes_idx < len(valores_12) else 0.0
            expr = expr.replace(placeholder, f"float({valor_mes})")
        
        # Ordenar por comprimento decrescente para evitar conflitos
        # Ex: TD70 não seja substituído quando fazemos replace em TD701
        codigos_ordenados = sorted(contexto_simples.keys(), key=len, reverse=True)
        
        for codigo in codigos_ordenados:
            if codigo in contexto_simples:
                valor_mes_var = contexto_simples[codigo][mes_idx]
                # Envolver em float() para garantir operações matemáticas
                expr = expr.replace(codigo, f"float({valor_mes_var})")
        
        try:
            resultado = eval(expr)
            valores_resultado.append(float(resultado))
            if mes_idx == 0:  # Log apenas do primeiro mês para não poluir
                print(f"[DRE] Mês 0 resultado: {resultado}")
        except Exception as e:
            print(f"[DRE] ❌ Erro ao avaliar fórmula '{formula}' mês {mes_idx}: {e}")
            print(f"[DRE] Expressão era: {expr}")
            valores_resultado.append(0.0)
    
    print(f"[DRE] Resultado final (12 meses): {valores_resultado[:3]}... (primeiros 3)")
    return valores_resultado


# ============================================================================
# PERSISTÊNCIA
# ============================================================================

def salvar_dre_usuario():
    """
    Salva dados da DRE para o usuário atual no session_state.
    Isso permite que os dados persistam entre navegações de página.
    """
    usuario = st.session_state.get("usuario", "anonimo")
    filtros = st.session_state.get("dre_filtros", {})
    dre_dados = st.session_state.get("dre_dados", {})
    dre_metodologias = st.session_state.get("dre_metodologias", {})
    
    # Cria chave única para esta combinação cliente/categoria/produto
    combo_key = f"{filtros.get('cliente', 'Todos')}::{filtros.get('categoria', '')}::{filtros.get('produto', '')}"
    
    # Inicializa dicionário de DREs salvas se não existir
    if "dre_salvas" not in st.session_state:
        st.session_state.dre_salvas = {}
    
    if usuario not in st.session_state.dre_salvas:
        st.session_state.dre_salvas[usuario] = {}
    
    # Salva dados da DRE
    st.session_state.dre_salvas[usuario][combo_key] = {
        "cliente": filtros.get("cliente", "Todos"),
        "categoria": filtros.get("categoria", ""),
        "produto": filtros.get("produto", ""),
        "dre_dados": dre_dados,
        "dre_metodologias": dre_metodologias,
        "data_salvo": datetime.now().isoformat(),
    }
    
    print(f"[DRE] Salva para usuário {usuario}: {combo_key}")
    st.success(f" DRE salva com sucesso para {filtros.get('produto', 'Sem produto')}!")


def carregar_dre_usuario(cliente: str, categoria: str, produto: str):
    """
    Carrega dados da DRE do usuário se existirem para esta combinação.
    
    Args:
        cliente, categoria, produto: Filtros para localizar a DRE
        
    Returns:
        Dicionário com dre_dados e dre_metodologias, ou None
    """
    usuario = st.session_state.get("usuario", "anonimo")
    combo_key = f"{cliente}::{categoria}::{produto}"
    
    try:
        dre_salvas = st.session_state.get("dre_salvas", {}).get(usuario, {})
        dre_salva = dre_salvas.get(combo_key, None)
        
        if dre_salva:
            print(f"[DRE] Carregada para usuário {usuario}: {combo_key}")
            return dre_salva
        else:
            print(f"[DRE] Nenhuma DRE salva para: {combo_key}")
            return None
    except Exception as e:
        print(f"[DRE] Erro ao carregar: {e}")
        return None



# ============================================================================
# RENDERIZAÇÃO - SEÇÕES DO NOVO LAYOUT (v2.5.1)
# ============================================================================

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
    st.markdown('<h3 style="color: #0c3a66; font-family: Plus Jakarta Sans, sans-serif;"><i class="fas fa-magnifying-glass" style="color: #06b6d4; margin-right: 8px;"></i>Selecione os Índices Econômicos</h3>', unsafe_allow_html=True)
    
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
    
    st.divider()
    
    # ===== RENDERIZAR COM st.data_editor =====
    if st.session_state.dre_indices_selecionados:
        st.markdown('<h3 style="color: #0c3a66; font-family: Plus Jakarta Sans, sans-serif;"><i class="fas fa-chart-bar" style="color: #06b6d4; margin-right: 8px;"></i>Dados dos Índices</h3>', unsafe_allow_html=True)
        
        # Preparar DataFrame
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
    
    # Sincronizar TD21 com curva ajustada
    curva_ajustada = st.session_state.get("ajustada", [0.0] * 12)
    if len(curva_ajustada) == 24:
        curva_ajustada = curva_ajustada[:12]
    
    if volumes_dados.get("TD21"):
        volumes_dados["TD21"]["valores"] = list(curva_ajustada)
    
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
            valor_formatado = fmt_br(valor) if valor != 0 else "0"
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
        border-collapse: collapse;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 13px;
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
    .dre-tabela td.mes-col {
        text-align: right;
        padding-right: 12px;
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
    </style>
    """, unsafe_allow_html=True)
    
    # ===== CRIAR ESTRUTURA DA TABELA =====
    html_table = '<table class="dre-tabela"><thead><tr>'
    html_table += '<th class="codigo-col">TD</th>'
    html_table += '<th class="desc-col">Descrição</th>'
    
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
        
        classe_linha = "negrito" if eh_negrito else ""
        html_table += f'<tr class="{classe_linha}">'
        
        # Código
        html_table += f'<td class="codigo-col">{codigo}</td>'
        
        # Descrição
        html_table += f'<td class="desc-col">{descricao}</td>'
        
        # Valores dos meses
        for mes_idx in range(12):
            valor = valores[mes_idx]
            
            if tipo == "variavel" and not modo_viz:
                # Input editável (usar st.number_input dentro de coluna)
                html_table += f'<td class="mes-col" id="cell_{codigo}_{mes_idx}"></td>'
            else:
                # Apenas visualização
                valor_formatado = fmt_br(valor) if valor != 0 else "0"
                html_table += f'<td class="mes-col">{valor_formatado}</td>'
        
        html_table += '</tr>'
    
    html_table += '</tbody></table>'
    st.markdown(html_table, unsafe_allow_html=True)
    
    # ===== INPUTS EDITÁVEIS (renderizar após a tabela para melhor UX) =====
    if not modo_viz:
        st.markdown("---")
        st.markdown('<h3 style="color: #0c3a66; font-family: Plus Jakarta Sans, sans-serif;"><i class="fas fa-pen-to-square" style="color: #06b6d4; margin-right: 8px;"></i>Editar Valores</h3>', unsafe_allow_html=True)
        
        for linha_data in dados_tabela:
            codigo = linha_data["codigo"]
            tipo = linha_data["tipo"]
            
            if tipo == "variavel":
                with st.expander(f"📝 {codigo} - {linha_data['descricao']}", expanded=False):
                    valores_atual = dre_dados[codigo]["valores"]
                    
                    cols = st.columns(12)
                    for mes_idx, mes in enumerate(MESES_ABR_LIST):
                        with cols[mes_idx]:
                            novo_valor = st.number_input(
                                mes,
                                value=float(valores_atual[mes_idx]),
                                format="%.2f",
                                key=f"input_{codigo}_{mes_idx}",
                                label_visibility="collapsed",
                                step=100.0
                            )
                            dre_dados[codigo]["valores"][mes_idx] = novo_valor
    
    st.session_state.dre_dados = dre_dados
    _calcular_totalizadores()
    
    # ===== RESUMO EM CARDS =====
    st.markdown("---")
    st.markdown('<h2 style="color: #0c3a66; font-family: Plus Jakarta Sans, sans-serif;"><i class="fas fa-chart-pie" style="color: #06b6d4; margin-right: 10px;"></i>Resumo de Resultado</h2>', unsafe_allow_html=True)
    
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
    # Carregar dados para filtros
    df_upload = get_dados_upload()
    
    col_cli, col_cat, col_prod, col_ano, col_modo, col_btn = st.columns([1.2, 1.2, 1.5, 1, 1, 1])
    
    # Cliente
    with col_cli:
        clientes = ["Todos"]
        if df_upload is not None and "TIPO_CLIENTE" in df_upload.columns:
            cli_list = sorted([c for c in df_upload["TIPO_CLIENTE"].dropna().astype(str).unique() if c.strip() != ""])
            clientes.extend(cli_list)
        
        cliente_sel = st.selectbox(
            "Cliente",
            clientes,
            index=0,
            key="dre_cliente_filter",
            label_visibility="collapsed"
        )
        st.session_state.dre_filtros["cliente"] = cliente_sel
    
    # Categoria
    with col_cat:
        categorias = [""]
        if df_upload is not None and "CATEGORIA" in df_upload.columns:
            df_cli = df_upload if cliente_sel == "Todos" else df_upload[df_upload["TIPO_CLIENTE"].astype(str) == cliente_sel]
            cat_list = sorted([c for c in df_cli["CATEGORIA"].dropna().astype(str).unique() if c.strip() != ""])
            categorias = [""] + cat_list
        
        categoria_sel = st.selectbox(
            "Categoria",
            categorias,
            index=0,
            key="dre_categoria_filter",
            label_visibility="collapsed"
        )
        st.session_state.dre_filtros["categoria"] = categoria_sel
    
    # Produto
    with col_prod:
        produtos = [""]
        if df_upload is not None and categoria_sel and "CATEGORIA" in df_upload.columns:
            df_cat = df_upload[df_upload["CATEGORIA"].astype(str) == categoria_sel]
            prod_list = sorted([p for p in df_cat["PRODUTO"].dropna().astype(str).unique() if p.strip() != ""][:10])
            produtos = [""] + prod_list
        
        produto_sel = st.selectbox(
            "Produto",
            produtos,
            index=0,
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
    
    # Modo Visualização
    with col_modo:
        modo_viz = st.toggle(
            " Viz",
            value=False,
            key="dre_modo_visualizacao",
            label_visibility="collapsed"
        )
    
    # Botão Salvar
    with col_btn:
        if st.button("Salvar", use_container_width=True, type="primary"):
            salvar_dre_usuario()
    
    # ===== DETECTAR MUDANÇA DE FILTRO E PERSISTIR DADOS =====
    # Criar chave única para a combinação atual de filtros
    combo_filtro_atual = f"{cliente_sel}::{categoria_sel}::{produto_sel}::{ano_sel}"
    combo_filtro_anterior = st.session_state.get("dre_combo_filtro_anterior", "")
    
    if combo_filtro_atual != combo_filtro_anterior:
        # print(f"[DRE] Mudanca de filtro detectada")  # Removed emoji for Windows encoding
        
        # ===== ETAPA 1: SALVAR DADOS DO FILTRO ANTERIOR =====
        if combo_filtro_anterior:  # Se não é a primeira inicialização
            st.session_state.dre_dados_persistidos[combo_filtro_anterior] = deepcopy(st.session_state.dre_dados)
        
        # ===== ETAPA 2: CARREGAR OU INICIALIZAR DADOS DO NOVO FILTRO =====
        if combo_filtro_atual in st.session_state.dre_dados_persistidos:
            # Já existe dados salvos para este filtro - RESTAURAR
            st.session_state.dre_dados = deepcopy(st.session_state.dre_dados_persistidos[combo_filtro_atual])
        else:
            # Primeiro acesso a este filtro - RESETAR VALORES (EXCETO TD71)
            for codigo in st.session_state.dre_dados:
                if codigo != "TD71":
                    st.session_state.dre_dados[codigo]["valores"] = [0.0] * 12
        
        # ===== ARMAZENAR NOVA CHAVE DE FILTRO =====
        st.session_state.dre_combo_filtro_anterior = combo_filtro_atual
    
    # ===== NOTA: TD71 MANTÉM VALORES ZERADOS =====
    # O carregamento de TD71 foi desativado. Será preenchido através de outra lógica no futuro.
    # _carregar_td71_simulacao(cliente_sel, categoria_sel, produto_sel, ano_sel)
    
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
    with st.expander("1. VOLUMES FINANCEIROS", expanded=False):
        _renderizar_secao_volumes_financeiros()
    
    st.divider()
    
    # ========================================================================
    # SEÇÃO 2: INDICADORES ECONÔMICOS (EXPANDER) - AGORA SEGUNDO
    # ========================================================================
    with st.expander("2. INDICADORES ECONÔMICOS", expanded=False):
        _renderizar_secao_indices_economicos()
    
    st.divider()
    
    # ========================================================================
    # SEÇÃO 3: ESTRUTURA DA DRE (EXPANDER) - AGORA TERCEIRO
    # ========================================================================
    with st.expander("3. ESTRUTURA DA DRE - PROJEÇÃO MENSAL (2026)", expanded=True):
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
    
    # ===== ABAS INTERNAS =====
    tab_criar, tab_aplicar, tab_refs = st.tabs([
        " Criar Metodologia",
        " Aplicar e Histórico",
        " Referência"
    ])
    
    # ===== ABA 1: CRIAR NOVA METODOLOGIA =====
    with tab_criar:
        st.markdown("####  Criar Nova Metodologia")
        
        # 🔑 PARÂMETROS DE SAZONALIDADE (FORA do form para ser dinâmico)
        with st.expander("⚙️ Parâmetros de Sazonalidade (opcional)", expanded=False):
            sazonalidade = criar_interface_sazonalidade(rotulo_prefix="criar")
        
        # ✨ Seletor de Índices Econômicos com busca (ANTES do form)
        st.markdown("#####  Índices Econômicos Disponíveis")
        
        # Importar função para obter índices
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
        
        # Layout do seletor de índices (FORA do form)
        if indices_disponiveis:
            col_busca, col_preview = st.columns([1.5, 1])
            
            with col_busca:
                busca_indice = st.text_input(
                    " Buscar índices:",
                    placeholder="Digite para filtrar (ex: IPCA, SELIC, DOLAR)",
                    key="busca_indices_criar"
                )
                
                indices_filtrados = [ind for ind in indices_disponiveis 
                                    if busca_indice.lower() in ind.lower()] if busca_indice else indices_disponiveis
                
                if indices_filtrados:
                    indice_selecionado = st.selectbox(
                        "Selecione um índice:",
                        indices_filtrados,
                        key="selectbox_indices_criar",
                        format_func=lambda x: f"📊 {x}"
                    )
                else:
                    indice_selecionado = None
                    st.warning("Nenhum índice encontrado")
            
            with col_preview:
                if indice_selecionado:
                    try:
                        valores_indice = agregar_indice_para_12_meses(indice_selecionado)
                        if valores_indice:
                            st.markdown(f"**{indice_selecionado}**")
                            st.metric(label="Valor Médio", value=f"{np.mean(valores_indice):.4f}")
                            st.metric(label="Min-Max", value=f"{min(valores_indice):.4f} - {max(valores_indice):.4f}")
                    except Exception as e:
                        st.error(f"Erro: {e}")
        else:
            st.info("Nenhum índice importado. Use a aba Upload para adicionar.")
        
        st.divider()
        
        # FORMULÁRIO (sem botões st.button() dentro)
        with st.form("form_nova_metodologia", clear_on_submit=True):
            nome_metodologia = st.text_input(
                "Nome da Metodologia",
                placeholder="ex: Despesa com Inflação (IPCA)",
                label_visibility="collapsed"
            )
            
            descricao_met = st.text_area(
                "Descrição (opcional)",
                placeholder="Descreva o propósito desta metodologia",
                height=60,
                label_visibility="collapsed"
            )
            
            formula_metodologia = st.text_input(
                "Fórmula de Cálculo",
                placeholder="ex: =0.60*TD71 ou =TD71*(1+IPCA/100)",
                label_visibility="collapsed",
                key="formula_input_criar",
                help="Use '=' no início. Exemplos: =0.60*TD71, =MEDIA(TD71), =TD71*(1+IPCA/100)"
            )
            
            # Info profissional
            col_info1, col_info2, col_info3 = st.columns(3)
            
            with col_info1:
                st.markdown("""
                **📝 Variáveis DRE:**
                - `TD71` - Receita Financeira
                - `TD72` - Despesa Financeira
                - `TD87` - Spread Câmbio
                - `MFB` - Margem Bruta
                """)
            
            with col_info2:
                st.markdown("""
                ** Funções Nativas:**
                - `SOMA(TD71)`
                - `MEDIA(TD71;TD72)`
                - `MINIMO(TD71:TD90)`
                - `MAXIMO(TD71)`
                """)
            
            with col_info3:
                st.markdown("""
                ** Índices Disponíveis:**
                """ + "".join([f"- `{ind}`\n" for ind in indices_disponiveis[:5]]) + 
                (f"- ... (+{len(indices_disponiveis)-5} mais)" if len(indices_disponiveis) > 5 else "")
                )
            
            aplicavel_a = st.multiselect(
                "Aplicável às variáveis (selecione pelo menos 1):",
                [linha.codigo for linha in ESTRUTURA_DRE if linha.tipo == "variavel"],
                help="Escolha quais variáveis receberão o cálculo desta fórmula"
            )
            
            # Botão de submit (DENTRO do form - único lugar permitido)
            submitted = st.form_submit_button(" Criar Metodologia", use_container_width=True, type="primary")
            
            if submitted:
                if nome_metodologia and formula_metodologia and aplicavel_a:
                    if not formula_metodologia.startswith("="):
                        st.error("⚠️ A fórmula deve começar com '='")
                    else:
                        # Validar fórmula
                        try:
                            _avaliar_formula(formula_metodologia, st.session_state.dre_dados, sazonalidade)
                            
                            # Salvar metodologia
                            nova_met = {
                                "nome": nome_metodologia,
                                "descricao": descricao_met,
                                "formula": formula_metodologia,
                                "aplicavel_a": aplicavel_a,
                                "sazonalidade": sazonalidade,
                                "data_criacao": datetime.now().isoformat(),
                                "data_atualizacao": datetime.now().isoformat(),
                                "aplicacoes": [],
                                "usa_indices": any(ind in formula_metodologia for ind in indices_disponiveis)
                            }
                            st.session_state.dre_metodologias[nome_metodologia] = nova_met
                            st.success(f" Metodologia '{nome_metodologia}' criada!")
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
                        
                        st.markdown(f"**Variáveis:** {', '.join([f'`{v}`' for v in met_dados['aplicavel_a']])}")
                        
                        saz = met_dados.get('sazonalidade', 0)
                        if saz != 0:
                            st.markdown(f"**Sazonalidade:** {saz} meses")
                        
                        st.caption(f"Criada em: {met_dados['data_criacao'][:10]}")
                        st.caption(f"Atualizada em: {met_dados.get('data_atualizacao', 'N/A')[:10] if met_dados.get('data_atualizacao') else 'N/A'}")
                        
                        # Histórico
                        aplicacoes = met_dados.get("aplicacoes", [])
                        if aplicacoes:
                            st.markdown("** Últimas Aplicações:**")
                            for app in aplicacoes[-5:]:
                                st.caption(f"• {app.get('escopo', 'N/A')} ({app.get('data', '')[:10]})")
                
                with col_apply:
                    if st.button(" Aplicar", key=f"btn_app_{met_nome}", use_container_width=True, type="primary"):
                        try:
                            print(f"\n{'='*60}")
                            print(f"[APLICACAO] Iniciando: {met_nome}")
                            print(f"[APLICACAO] Escopo: {escopo_texto}")
                            print(f"{'='*60}")
                            
                            # ===== APLICAR METODOLOGIA =====
                            dre_dados = deepcopy(st.session_state.dre_dados)
                            
                            aplicadas_a = []
                            for var_codigo in met_dados['aplicavel_a']:
                                if var_codigo in dre_dados:
                                    # Calcular nova série
                                    valores_calc = _avaliar_formula(
                                        met_dados['formula'], 
                                        dre_dados,
                                        sazonalidade=met_dados.get('sazonalidade', None)  #  Passar sazonalidade
                                    )
                                    
                                    # Log
                                    v_antes = dre_dados[var_codigo]["valores"][:3]
                                    dre_dados[var_codigo]["valores"] = valores_calc
                                    v_depois = valores_calc[:3]
                                    
                                    print(f"[APLICACAO] {var_codigo}")
                                    print(f"  ANTES:  {v_antes}...")
                                    print(f"  DEPOIS: {v_depois}...")
                                    
                                    aplicadas_a.append(var_codigo)
                            
                            # ===== SALVAR E RECALCULAR =====
                            st.session_state.dre_dados = dre_dados
                            _calcular_totalizadores()
                            
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
                            
                            print(f"[APLICACAO]  SUCESSO")
                            print(f"{'='*60}\n")
                            
                            st.success(f"""
                             **Aplicado com Sucesso!**
                            
                            • Variáveis: {', '.join(aplicadas_a)}
                            • Escopo: {escopo_texto}
                            • Timestamp: {novo_registro['data'][:19].replace('T', ' ')}
                            """)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
                            print(f"[APLICACAO] ❌ ERRO: {e}")
                            import traceback
                            traceback.print_exc()
                
                # ===== BOTÃO EDITAR =====
                with col_edit:
                    if st.button("✏️ Editar", key=f"btn_edit_{met_nome}", use_container_width=True):
                        st.session_state[f"editando_{met_nome}"] = True
                        st.rerun()
                
                with col_del:
                    if st.button("🗑️", key=f"btn_del_{met_nome}", use_container_width=True):
                        del st.session_state.dre_metodologias[met_nome]
                        st.rerun()
                
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
                            "Variáveis",
                            [linha.codigo for linha in ESTRUTURA_DRE if linha.tipo == "variavel"],
                            default=met_dados['aplicavel_a'],
                            key=f"vars_edit_{met_nome}"
                        )
                        
                        # Botões
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("Salvar Alterações", use_container_width=True, type="primary"):
                                try:
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
        for idx, nome_func in enumerate(["SOMA", "MEDIA", "MINIMO", "MAXIMO"]):
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
        
        # ===== PROCESSAMENTO =====
        st.divider()
        st.markdown("#### Ordem de Processamento")
        
        st.markdown("""
        As fórmulas são processadas em três etapas:
        
        **1️⃣ Funções Nativas**
        - Todas as funções (SOMA, MEDIA, etc) são avaliadas PRIMEIRO
        - Cada função retorna um ÚNICO valor agregado
        - Exemplo: `SOMA(TD71)` = 1860.0 (soma de 12 meses)
        
        **2️⃣ Substituição**
        - O resultado de cada função substitui a chamada função
        - Exemplo: `0.05*SOMA(TD71)` → `0.05*1860.0`
        
        **3️⃣ Cálculo Mês-a-Mês**
        - A fórmula final é calculada para cada um dos 12 meses
        - Variáveis (TD71, TD72) usam seus valores mensais
        - Resultado: 12 valores (um por mês)
        
        **Exemplo Completo:**
        ```
        Fórmula: =0.05*SOMA(TD71)+0.03*MEDIA(TD72)
        
        Passo 1: SOMA(TD71) = 1860.0, MEDIA(TD72) = 116.25
        Passo 2: =0.05*1860.0+0.03*116.25
        Passo 3: Para cada mês:
          - Mês 1: 0.05*155.0 + 0.03*9.69 = 8.06
          - Mês 2: 0.05*160.0 + 0.03*10.00 = 8.30
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
