"""
Aplicação principal Streamlit
Dashboard de Projeções Financeiras
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Configuração da página
st.set_page_config(
    page_title="Dashboard Financeiro - UAN",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tema customizado
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
    }
    
    .main-title {
        color: #1f4788;
        margin-bottom: 2rem;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .sidebar {
        background: linear-gradient(180deg, #1f4788 0%, #2d5aa8 100%);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1f4788 0%, #2d5aa8 100%);
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Função principal da aplicação"""
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("### 🏦 UAN Dashboard")
        st.markdown("---")
        
        # Menu de navegação
        pagina = st.radio(
            "Navegação",
            ["🔐 Autenticação", "📊 Dashboard", "🎯 Simulador", "👤 Perfil"],
            label_visibility="collapsed"
        )
    
    # Roteamento das páginas
    if pagina == "🔐 Autenticação":
        from pages import autenticacao
        autenticacao.renderizar()
    
    elif pagina == "📊 Dashboard":
        from pages import dashboard
        dashboard.renderizar()
    
    elif pagina == "🎯 Simulador":
        from pages import simulador
        simulador.renderizar()
    
    elif pagina == "👤 Perfil":
        from pages import perfil
        perfil.renderizar()


if __name__ == "__main__":
    main()
