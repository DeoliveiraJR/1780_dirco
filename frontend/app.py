import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from styles import CORES, CSS_CUSTOM, aplicar_tema
from pages import autenticacao, dashboard, simulador, perfil, upload

st.set_page_config(
    page_title="UAN Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

aplicar_tema()

# ============= CARREGAMENTO DA LOGO =============
import os
from PIL import Image

logo_path = os.path.join(os.path.dirname(__file__), "images", "logo.png")
logo_image = None
if os.path.exists(logo_path):
    try:
        logo_image = Image.open(logo_path)
    except:
        logo_image = None
# ================================================

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = None

if not st.session_state.autenticado:
    autenticacao.renderizar()
else:
    with st.sidebar:
        st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {display: none;}
            [data-testid="collapsedControl"] {display: none;}
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0c3a66 0%, #1e3a8a 100%); 
                    padding: 20px; 
                    border-radius: 12px; 
                    margin-bottom: 20px;
                    text-align: center;">
        """, unsafe_allow_html=True)
        
        if logo_image:
            st.image(logo_image, width=120)
        else:
            st.markdown("""
            <div style="font-size: 16px; margin-bottom: 10px; color: white;">
                🏢 LOGO
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
            <div style="font-size: 18px; font-weight: 700; color: white;">UAN Dashboard</div>
            <div style="font-size: 12px; color: #e0f2fe; margin-top: 5px;">
                Sistema de Analise Financeira
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not logo_image:
            st.info("💡 **Para adicionar logo:** Coloque um arquivo `logo.png` em `/frontend/images/` e recarregue a página. Use PNG com fundo transparente para melhor resultado!")
        
        st.markdown("---")
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f0f9fc 0%, #e0f2fe 100%); 
                    padding: 12px; 
                    border-radius: 8px;
                    border-left: 4px solid #06b6d4;
                    margin-bottom: 20px;">
            <div style="font-size: 12px; color: #6b7280;">Usuario Logado</div>
            <div style="font-size: 14px; font-weight: 600; color: #0c3a66; margin-top: 4px;">
                {st.session_state.usuario}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### Menu")
        
        opcoes = {
            "📊 Dashboard": "Dashboard",
            "🎯 Simulador": "Simulador",
            "👤 Perfil": "Perfil",
            "📤 Upload": "Upload de Dados"
        }
        
        pagina = st.radio(
            "Selecione uma pagina:",
            list(opcoes.values()),
            format_func=lambda x: [k for k, v in opcoes.items() if v == x][0],
            label_visibility="collapsed",
            key="nav_radio"
        )
        
        st.markdown("---")
        
        with st.expander("⚙️ Configuracoes"):
            st.markdown("""
            - **Tema:** Profissional
            - **Idioma:** Portugues (BR)
            - **Versao:** 1.0.0
            - **Status:** Producao
            """)
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            st.session_state.autenticado = False
            st.session_state.usuario = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #9ca3af; font-size: 11px;">
            <p>UAN Dashboard v1.0.0</p>
            <p>(c) 2026 Banco Nacional</p>
        </div>
        """, unsafe_allow_html=True)
    
    if pagina == "Dashboard":
        dashboard.renderizar()
    elif pagina == "Simulador":
        simulador.renderizar()
    elif pagina == "Perfil":
        perfil.renderizar()
    elif pagina == "Upload de Dados":
        upload.renderizar()
