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
        # Ocultar navegação padrão
        st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {display: none;}
            [data-testid="collapsedControl"] {display: none;}
        </style>
        """, unsafe_allow_html=True)
        
        # ============== HEADER COM LOGO E TITULO ==============
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0c3a66 0%, #1e3a8a 100%); 
                    padding: 25px 15px; 
                    border-radius: 12px; 
                    margin-bottom: 25px;
                    text-align: center;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        """, unsafe_allow_html=True)
        
        # Logo
        if logo_image:
            col_logo = st.columns([1])[0]
            with col_logo:
                st.image(logo_image, width=100, use_column_width=False)
        
        st.markdown("""
            <h2 style="margin: 15px 0 5px 0; color: white; font-size: 22px; font-weight: 700;">
                UAN Dashboard
            </h2>
            <p style="margin: 0; color: #e0f2fe; font-size: 13px;">
                Sistema de Análise Financeira
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if not logo_image:
            st.info("💡 **Logo:** Adicione um arquivo `logo.png` em `/frontend/images/`")
        
        st.markdown("")
        
        # ============== SEÇÃO DO USUÁRIO COM AVATAR ==============
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ecf0f1 0%, #bdc3c7 100%); 
                    padding: 15px; 
                    border-radius: 10px;
                    border-left: 4px solid #06b6d4;
                    margin-bottom: 20px;
                    display: flex;
                    align-items: center;
                    gap: 12px;">
            <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #06b6d4, #a855f7); 
                        border-radius: 50%; 
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 24px;
                        color: white;
                        font-weight: bold;
                        flex-shrink: 0;">
                👤
            </div>
            <div>
                <p style="margin: 0; font-size: 11px; color: #7f8c8d; font-weight: 600;">USUÁRIO LOGADO</p>
                <p style="margin: 5px 0 0 0; font-size: 14px; color: #0c3a66; font-weight: 700;">
        """ + st.session_state.usuario.split("@")[0].capitalize() + """
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ============== MENU DE NAVEGAÇÃO ELEGANTE ==============
        st.markdown("<p style='font-size: 12px; font-weight: 600; color: #6b7280; margin-bottom: 10px;'>📍 NAVEGAÇÃO</p>", unsafe_allow_html=True)
        
        opcoes = {
            "📊 Dashboard": "Dashboard",
            "🎯 Simulador": "Simulador", 
            "👤 Perfil": "Perfil",
            "📤 Upload": "Upload de Dados"
        }
        
        pagina = st.radio(
            "Menu:",
            list(opcoes.values()),
            format_func=lambda x: [k for k, v in opcoes.items() if v == x][0],
            label_visibility="collapsed",
            key="nav_radio"
        )
        
        st.markdown("---")
        
        # ============== CONFIGURAÇÕES ==============
        with st.expander("⚙️ Configurações", expanded=False):
            st.markdown("""
            **Tema:** Profissional  
            **Idioma:** Português (BR)  
            **Versão:** 1.0.0  
            **Status:** Produção ✓
            """)
        
        st.markdown("---")
        
        # ============== LOGOUT ==============
        col_logout = st.columns([1])[0]
        with col_logout:
            if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                st.session_state.autenticado = False
                st.session_state.usuario = None
                st.rerun()
        
        st.markdown("---")
        
        # ============== FOOTER ==============
        st.markdown("""
        <div style="text-align: center; color: #95a5a6; font-size: 10px; margin-top: 20px;">
            <p style="margin: 5px 0;">UAN Dashboard v1.0.0</p>
            <p style="margin: 5px 0;">(c) 2026 Banco Nacional</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ============== RENDERIZAR PÁGINAS ==============
    if pagina == "Dashboard":
        dashboard.renderizar()
    elif pagina == "Simulador":
        simulador.renderizar()
    elif pagina == "Perfil":
        perfil.renderizar()
    elif pagina == "Upload de Dados":
        upload.renderizar()
