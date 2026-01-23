import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from styles import CORES, CSS_CUSTOM, aplicar_tema
from pages import autenticacao, dashboard, simulador, perfil, upload
from data_manager import init_data_state

# Inicializar data state logo no início
init_data_state()

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
            section[data-testid="stSidebar"] > div {padding-top: 2rem;}
        </style>
        """, unsafe_allow_html=True)
        
        # ============== HEADER COM BARRA AZUL GRADIENTE ==============
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0c3a66 0%, #06b6d4 100%); 
                    padding: 35px 20px; 
                    border-radius: 16px; 
                    margin-bottom: 25px;
                    text-align: center;
                    box-shadow: 0 8px 16px rgba(0,0,0,0.15);">
        """, unsafe_allow_html=True)
        
        # Logo centralizada
        if logo_image:
            col_logo = st.columns([0.15, 0.7, 0.15])
            with col_logo[1]:
                st.image(logo_image, use_container_width=True)
        else:
            st.markdown('<div style="font-size: 52px; margin: 0;">🏢</div>', unsafe_allow_html=True)
        
        st.markdown("""
            <h1 style="margin: 22px 0 10px 0; color: white; font-size: 28px; 
                       font-weight: 800; letter-spacing: 2px; text-align: center;">
                UAN DASHBOARD
            </h1>
            <p style="margin: 0; color: #FFD100; font-size: 14px; 
                      font-weight: 600; text-align: center;">
                sistema Arquitetura de projeções - Dirco
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if not logo_image:
            st.caption("💡 Adicione logo.png em /frontend/images/")
        
        st.markdown('<div style="height: 5px;"></div>', unsafe_allow_html=True)
        
        # ============== USUÁRIO ==============
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); 
                    padding: 16px; border-radius: 12px; border-left: 4px solid #06b6d4;
                    margin-bottom: 25px; display: flex; align-items: center; gap: 14px;">
            <div style="width: 52px; height: 52px; 
                        background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); 
                        border-radius: 50%; display: flex; align-items: center;
                        justify-content: center; font-size: 26px; flex-shrink: 0;
                        box-shadow: 0 4px 6px rgba(6, 182, 212, 0.3);">
                👤
            </div>
            <div>
                <p style="margin: 0; font-size: 10px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">USUÁRIO</p>
                <p style="margin: 4px 0 0 0; font-size: 15px; color: #0c3a66; font-weight: 700;">
        """ + st.session_state.usuario.split("@")[0].capitalize() + """
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ============== MENU DE NAVEGAÇÃO ==============
        st.markdown("<p style='font-size: 11px; font-weight: 600; color: #94a3b8; margin: 0 0 10px 0;'>📍 NAVEGAÇÃO</p>", unsafe_allow_html=True)
        
        # Mapeamento de páginas com ícones
        opcoes_menu = [
            ("📊", "Dashboard", "Dashboard"),
            ("🎯", "Simulador", "Simulador"),
            ("👤", "Perfil", "Perfil"),
            ("📤", "Upload", "Upload de Dados")
        ]
        
        # Criar labels formatados
        opcoes_display = {}
        for icone, label, valor in opcoes_menu:
            opcoes_display[f"{icone} {label}"] = valor
        
        pagina = st.radio(
            "Menu Principal",
            list(opcoes_display.values()),
            format_func=lambda x: [k for k, v in opcoes_display.items() if v == x][0],
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
