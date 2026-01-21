"""
Utilitários da aplicação
"""

import streamlit as st
from functools import lru_cache


@lru_cache(maxsize=32)
def carregar_configuracoes():
    """Carrega configurações da aplicação"""
    return {
        'app_name': 'UAN Dashboard',
        'versao': '1.0.0',
        'tema': 'dark',
        'idioma': 'pt-br'
    }


def inicializar_sessao():
    """Inicializa variáveis de sessão"""
    
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    
    if 'usuario_email' not in st.session_state:
        st.session_state.usuario_email = None
    
    if 'simulacoes' not in st.session_state:
        st.session_state.simulacoes = []
    
    if 'tema' not in st.session_state:
        st.session_state.tema = 'light'


def formatar_moeda(valor: float) -> str:
    """Formata valor em moeda brasileira"""
    return f"R$ {valor:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')


def formatar_percentual(valor: float, casas: int = 2) -> str:
    """Formata valor em percentual"""
    return f"{valor:.{casas}f}%"
