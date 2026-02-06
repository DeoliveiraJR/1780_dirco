"""
Data Manager - Gerencia dados compartilhados entre páginas
Armazena dados do upload e simulações
"""

import pandas as pd
import streamlit as st
import json
from datetime import datetime


# ============================================================================
# INICIALIZAÇÃO DO SESSION STATE
# ============================================================================
def init_data_state():
    if "dados_upload" not in st.session_state:
        st.session_state.dados_upload = None
    if "simulacoes" not in st.session_state:
        st.session_state.simulacoes = []
    if "simulacoes_salvas" not in st.session_state:
        st.session_state.simulacoes_salvas = {}  # {usuario: [lista de simulações]}
    if "metricas_dashboard" not in st.session_state:
        st.session_state.metricas_dashboard = {
            "valor_total": 0,
            "realizado_atual": 0,
            "taxa_acuracia": 0,
            "simulacoes_ativas": 0
        }
    if "ajustada" not in st.session_state:
        st.session_state.ajustada = [0.0] * 12
    if "ajustes_categoria" not in st.session_state:
        st.session_state.ajustes_categoria = {}
    if "sync_counter" not in st.session_state:
        st.session_state.sync_counter = 0
    if "last_combo" not in st.session_state:
        st.session_state.last_combo = None


# ============================================================================
# RESET COMPLETO - Limpa todos os estados
# ============================================================================
def resetar_tudo():
    """
    Reseta completamente todos os estados do session_state.
    Deve ser chamado quando quiser começar do zero.
    """
    st.session_state.dados_upload = None
    st.session_state.simulacoes = []
    st.session_state.simulacoes_salvas = {}
    st.session_state.metricas_dashboard = {
        "valor_total": 0,
        "realizado_atual": 0,
        "taxa_acuracia": 0,
        "simulacoes_ativas": 0
    }
    st.session_state.ajustada = [0.0] * 12
    st.session_state.ajustes_categoria = {}
    st.session_state.sync_counter = 0
    st.session_state.last_combo = None
    st.session_state.filtros = {}
    st.session_state.curva_analitica = []
    st.session_state.curva_mercado = []
    # Flag para limpar localStorage no próximo render
    st.session_state._limpar_localStorage = True


def resetar_simulacao_atual():
    """
    Reseta apenas a simulação atual (curva ajustada volta para analítica).
    Mantém os dados de upload e simulações salvas.
    """
    st.session_state.ajustada = st.session_state.get("curva_analitica", [0.0] * 12)[:]
    st.session_state.sync_counter = st.session_state.get("sync_counter", 0) + 1
    st.session_state.ajustes_categoria = {}
    st.session_state._limpar_localStorage = True


# ============================================================================
# DADOS DE UPLOAD
# ============================================================================
def set_dados_upload(df):
    """Armazena dados do upload no session state"""
    st.session_state.dados_upload = df
    atualizar_metricas_dashboard()


def get_dados_upload():
    """Recupera dados do upload"""
    return st.session_state.dados_upload


# ============================================================================
# SIMULAÇÕES - CRUD
# ============================================================================
def adicionar_simulacao(nome, categoria, produto, taxa_crescimento, 
                        volatilidade, cenarios, dados_grafico):
    """Adiciona uma nova simulação ao session_state"""
    usuario = st.session_state.get("usuario", "anonimo")
    
    simulacao = {
        "id": f"{usuario}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "nome": nome,
        "categoria": categoria,
        "produto": produto,
        "cliente": cenarios.get("Cliente", "Todos"),
        "taxa_crescimento": taxa_crescimento,
        "volatilidade": volatilidade,
        "cenarios": cenarios,
        "dados_grafico": dados_grafico,
        "ajustada": dados_grafico.get("Ajustada", [0.0] * 12),
        "data_criacao": datetime.now().isoformat(),
        "status": "Ativa"
    }
    
    # Adiciona à lista do usuário
    if usuario not in st.session_state.simulacoes_salvas:
        st.session_state.simulacoes_salvas[usuario] = []
    
    # Verifica se já existe simulação com mesmo nome para mesma combo
    combo_key = f"{categoria}::{produto}::{cenarios.get('Cliente', 'Todos')}"
    existente = None
    for i, sim in enumerate(st.session_state.simulacoes_salvas[usuario]):
        sim_combo = f"{sim.get('categoria')}::{sim.get('produto')}::{sim.get('cliente', 'Todos')}"
        if sim.get("nome") == nome and sim_combo == combo_key:
            existente = i
            break
    
    if existente is not None:
        # Atualiza simulação existente
        st.session_state.simulacoes_salvas[usuario][existente] = simulacao
    else:
        # Adiciona nova
        st.session_state.simulacoes_salvas[usuario].append(simulacao)
    
    # Mantém compatibilidade com lista antiga
    st.session_state.simulacoes.append(simulacao)
    
    return simulacao


def get_simulacoes_usuario(usuario=None):
    """Retorna todas as simulações do usuário"""
    if usuario is None:
        usuario = st.session_state.get("usuario", "anonimo")
    return st.session_state.simulacoes_salvas.get(usuario, [])


def get_simulacao_por_combo(categoria, produto, cliente="Todos"):
    """Busca simulação salva para uma combinação específica"""
    usuario = st.session_state.get("usuario", "anonimo")
    simulacoes = st.session_state.simulacoes_salvas.get(usuario, [])
    
    for sim in reversed(simulacoes):  # Mais recente primeiro
        if (sim.get("categoria") == categoria and 
            sim.get("produto") == produto and
            sim.get("cliente", "Todos") == cliente):
            return sim
    return None


def restaurar_simulacao(simulacao_id):
    """Restaura uma simulação salva para o estado atual"""
    usuario = st.session_state.get("usuario", "anonimo")
    simulacoes = st.session_state.simulacoes_salvas.get(usuario, [])
    
    for sim in simulacoes:
        if sim.get("id") == simulacao_id:
            # Restaura os dados
            st.session_state["ajustada"] = sim.get("ajustada", [0.0] * 12)
            st.session_state["filtros"] = {
                "cliente": sim.get("cliente", "Todos"),
                "categoria": sim.get("categoria", ""),
                "produto": sim.get("produto", ""),
                "nome": sim.get("nome", "")
            }
            return sim
    return None


def deletar_simulacao(simulacao_id):
    """Deleta uma simulação por ID"""
    usuario = st.session_state.get("usuario", "anonimo")
    if usuario in st.session_state.simulacoes_salvas:
        st.session_state.simulacoes_salvas[usuario] = [
            s for s in st.session_state.simulacoes_salvas[usuario] 
            if s.get("id") != simulacao_id
        ]
    # Compatibilidade
    st.session_state.simulacoes = [
        s for s in st.session_state.simulacoes 
        if s.get("id") != simulacao_id
    ]


def get_simulacoes():
    """Retorna todas as simulações (compatibilidade)"""
    return st.session_state.simulacoes


# ============================================================================
# AJUSTES POR CATEGORIA (para propagar alterações do drag-and-drop)
# ============================================================================
def set_ajuste_categoria(categoria, valores):
    """Salva ajuste temporário para uma categoria"""
    st.session_state.ajustes_categoria[categoria] = valores


def get_ajuste_categoria(categoria):
    """Recupera ajuste temporário de uma categoria"""
    return st.session_state.ajustes_categoria.get(categoria, None)


def limpar_ajustes_categoria():
    """Limpa todos os ajustes temporários"""
    st.session_state.ajustes_categoria = {}


# ============================================================================
# MÉTRICAS DO DASHBOARD
# ============================================================================
def atualizar_metricas_dashboard():
    """Atualiza métricas do dashboard baseado nos dados do upload"""
    if st.session_state.dados_upload is not None:
        df = st.session_state.dados_upload
        
        st.session_state.metricas_dashboard = {
            "valor_total": float(df['PROJETADO_AJUSTADO'].sum()) 
                if 'PROJETADO_AJUSTADO' in df.columns else 0,
            "realizado_atual": float(df['CURVA_REALIZADO'].sum()) 
                if 'CURVA_REALIZADO' in df.columns else 0,
            "taxa_acuracia": calcular_acuracia(df),
            "simulacoes_ativas": len(get_simulacoes_usuario())
        }


def calcular_acuracia(df):
    """Calcula taxa de acurácia entre realizado e projetado"""
    if 'CURVA_REALIZADO' in df.columns and 'PROJETADO_ANALITICO' in df.columns:
        realizado = df['CURVA_REALIZADO'].sum()
        projetado = df['PROJETADO_ANALITICO'].sum()
        if projetado > 0:
            acuracia = (realizado / projetado) * 100
            return min(100, max(0, acuracia))
    return 0


def get_metricas_dashboard():
    """Retorna as métricas do dashboard"""
    return st.session_state.metricas_dashboard


# ============================================================================
# PERSISTÊNCIA (simulada via session_state - em produção usaria DB)
# ============================================================================
def exportar_simulacoes_json():
    """Exporta todas as simulações do usuário para JSON"""
    usuario = st.session_state.get("usuario", "anonimo")
    dados = st.session_state.simulacoes_salvas.get(usuario, [])
    return json.dumps(dados, default=str, indent=2)


def importar_simulacoes_json(json_str):
    """Importa simulações de um JSON"""
    usuario = st.session_state.get("usuario", "anonimo")
    try:
        dados = json.loads(json_str)
        if isinstance(dados, list):
            st.session_state.simulacoes_salvas[usuario] = dados
            return True
    except Exception:
        pass
    return False


# ============================================================================
# GERAR DADOS DE EXEMPLO
# ============================================================================
def gerar_dados_exemplo():
    """Gera dados de exemplo para demonstração"""
    import numpy as np
    
    datas = pd.date_range('2025-01-01', periods=12, freq='MS')
    categorias = ['Credito PF', 'Credito PJ', 'Investimentos']
    produtos = ['Credito Pessoal', 'Emprestimo', 'Fundo de Investimento']
    
    dados = []
    for data in datas:
        for cat_idx, categoria in enumerate(categorias):
            for prod_idx, produto in enumerate(produtos):
                realizado = np.random.uniform(200000, 800000)
                projetado = realizado * np.random.uniform(1.0, 1.3)
                
                dados.append({
                    'DATA_COMPLETA': data.strftime('%d/%m/%Y'),
                    'MES': data.strftime('%B').lower(),
                    'ANO': data.year,
                    'COD_CATEGORIA': f'CAT{cat_idx:02d}',
                    'CATEGORIA': categoria,
                    'COD_PRODUTO': f'PRD{prod_idx:02d}',
                    'PRODUTO': produto,
                    'CURVA_REALIZADO': realizado,
                    'PROJETADO_ANALITICO': projetado,
                    'PROJETADO_MERCADO': projetado * 0.95,
                    'PROJETADO_AJUSTADO': projetado * 0.98
                })
    
    return pd.DataFrame(dados)


# Inicializar ao importar
init_data_state()
