import streamlit as st
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from styles import CORES, CSS_CUSTOM, aplicar_tema

def renderizar():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<h1 style='text-align:center; color: #0c3a66;'>UAN Dashboard</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color: #6b7280;'>Sistema de Analise Financeira</p>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.write("Bem-vindo ao painel de controle de projecoes financeiras.")
        st.write("Faca login para acessar suas analises e simulacoes.")
        
        st.markdown("---")
        
        with st.form("form_login"):
            email = st.text_input(
                "Email",
                placeholder="seu@email.com",
                key="login_email"
            )
            
            senha = st.text_input(
                "Senha",
                type="password",
                placeholder="••••••••",
                key="login_senha"
            )
            
            lembrar = st.checkbox("Lembrar de mim")
            
            col_login, col_register = st.columns(2)
            
            with col_login:
                btn_login = st.form_submit_button("Entrar", use_container_width=True)
            
            with col_register:
                btn_register = st.form_submit_button("Registrar", use_container_width=True)
        
        if btn_login:
            if email and senha:
                if email.lower() == "teste@uan.com.br" and senha == "123456":
                    st.session_state.autenticado = True
                    st.session_state.usuario = email
                    st.success("Login realizado com sucesso!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Email ou senha invalidos")
            else:
                st.warning("Preencha email e senha")
        
        if btn_register:
            st.info("Registro em desenvolvimento")
        
        st.markdown("---")
        
        st.markdown("### Credenciais de Teste")
        st.code("Email: teste@uan.com.br")
        st.code("Senha: 123456")
        
        st.markdown("---")
        
        st.markdown("**Sobre o Sistema**")
        st.write("""
        UAN Dashboard eh uma plataforma para:
        - Analise de dados financeiros
        - Projecoes e simulacoes
        - Visualizacao de tendencias
        - Gerenciamento de carteira
        """)
