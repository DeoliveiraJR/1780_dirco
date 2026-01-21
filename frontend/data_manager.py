"""
Data Manager - Gerencia dados compartilhados entre páginas
Armazena dados do upload e simulações
"""

import pandas as pd
import streamlit as st
import json
from datetime import datetime

# Inicializar session state para dados compartilhados
def init_data_state():
    if "dados_upload" not in st.session_state:
        st.session_state.dados_upload = None
    if "simulacoes" not in st.session_state:
        st.session_state.simulacoes = []
    if "metricas_dashboard" not in st.session_state:
        st.session_state.metricas_dashboard = {
            "valor_total": 0,
            "realizado_atual": 0,
            "taxa_acuracia": 0,
            "simulacoes_ativas": 0
        }

def set_dados_upload(df):
    """Armazena dados do upload no session state"""
    st.session_state.dados_upload = df
    atualizar_metricas_dashboard()
    # Salvar no localStorage via JavaScript
    salvar_local_storage("dados_upload", df.to_json(orient='records'))

def get_dados_upload():
    """Recupera dados do upload"""
    return st.session_state.dados_upload

def atualizar_metricas_dashboard():
    """Atualiza métricas do dashboard baseado nos dados do upload"""
    if st.session_state.dados_upload is not None:
        df = st.session_state.dados_upload
        
        st.session_state.metricas_dashboard = {
            "valor_total": float(df['PROJETADO_AJUSTADO'].sum()) if 'PROJETADO_AJUSTADO' in df.columns else 0,
            "realizado_atual": float(df['CURVA_REALIZADO'].sum()) if 'CURVA_REALIZADO' in df.columns else 0,
            "taxa_acuracia": calcular_acuracia(df),
            "simulacoes_ativas": len(st.session_state.simulacoes)
        }

def calcular_acuracia(df):
    """Calcula taxa de acurácia entre realizado e projetado"""
    if 'CURVA_REALIZADO' in df.columns and 'PROJETADO_ANALITICO' in df.columns:
        realizado = df['CURVA_REALIZADO'].sum()
        projetado = df['PROJETADO_ANALITICO'].sum()
        if projetado > 0:
            acuracia = (realizado / projetado) * 100
            return min(100, max(0, acuracia))  # Limitar entre 0-100
    return 0

def adicionar_simulacao(nome, categoria, produto, taxa_crescimento, volatilidade, cenarios, dados_grafico):
    """Adiciona uma nova simulação"""
    simulacao = {
        "id": len(st.session_state.simulacoes) + 1,
        "nome": nome,
        "categoria": categoria,
        "produto": produto,
        "taxa_crescimento": taxa_crescimento,
        "volatilidade": volatilidade,
        "cenarios": cenarios,
        "dados_grafico": dados_grafico,
        "data_criacao": datetime.now().isoformat(),
        "status": "Ativa"
    }
    st.session_state.simulacoes.append(simulacao)
    salvar_local_storage("simulacoes", json.dumps(st.session_state.simulacoes, default=str))
    return simulacao

def get_simulacoes():
    """Retorna todas as simulações"""
    return st.session_state.simulacoes

def deletar_simulacao(simulacao_id):
    """Deleta uma simulação por ID"""
    st.session_state.simulacoes = [s for s in st.session_state.simulacoes if s["id"] != simulacao_id]
    salvar_local_storage("simulacoes", json.dumps(st.session_state.simulacoes, default=str))

def get_metricas_dashboard():
    """Retorna as métricas do dashboard"""
    return st.session_state.metricas_dashboard

def salvar_local_storage(chave, valor):
    """
    Salva dados no localStorage via JavaScript
    Isso persiste os dados mesmo após recarregar a página
    """
    js_code = f"""
    <script>
        localStorage.setItem('{chave}', JSON.stringify({json.dumps(valor)}));
    </script>
    """
    st.components.v1.html(js_code, height=0)

def carregar_local_storage(chave):
    """Carrega dados do localStorage via JavaScript"""
    js_code = f"""
    <script>
        const valor = localStorage.getItem('{chave}');
        console.log('Carregado do localStorage: {chave}', valor);
    </script>
    """
    st.components.v1.html(js_code, height=0)

# Gerar dados de exemplo para o dashboard
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
