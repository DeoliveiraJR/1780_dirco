import streamlit as st
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'backend'))

from styles import CORES, CSS_CUSTOM, aplicar_tema
from database import validar_login, inicializar_database, carregar_usuarios

def renderizar():
    # Inicializa database na primeira execução
    if "db_inicializado" not in st.session_state:
        inicializar_database()
        st.session_state.db_inicializado = True
    
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<h1 style='text-align:center; color: #0c3a66;'>UAN Dashboard</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color: #6b7280;'>Sistema de análise e simulação das projeções de mercado</p>", unsafe_allow_html=True)
        
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
                # Valida usando o sistema de database mockado
                autenticado, usuario = validar_login(email, senha)
                
                if autenticado:
                    st.session_state.autenticado = True
                    st.session_state.usuario_email = email
                    st.session_state.usuario_id = usuario.get("id")
                    st.session_state.usuario_nome = usuario.get("nome")
                    st.session_state.usuario_role = usuario.get("role")
                    st.session_state.usuario_departamento = usuario.get("departamento")
                    # Compatibilidade com código antigo
                    st.session_state.usuario = email
                    
                    role_display = "Administrador" if usuario.get("role") == "admin" else "Usuário"
                    st.success(f"✓ Login realizado! Bem-vindo, {usuario.get('nome')} ({role_display})")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Email ou senha inválidos")
            else:
                st.warning("⚠️ Preencha email e senha")
        
        if btn_register:
            st.info("📝 Registro em desenvolvimento")
        
        st.markdown("---")
        
        st.markdown("### 📋 Credenciais de Teste")
        
        col_admin, col_user = st.columns(2)
        
        with col_admin:
            st.markdown("**👨‍💼 Admin (Upload)**")
            st.code("Email: admin@uan.com.br\nSenha: admin123", language="text")
        
        with col_user:
            st.markdown("**👤 Usuário Comum**")
            st.code("Email: teste@uan.com.br\nSenha: 123456", language="text")
        
        st.markdown("---")
        
        st.markdown("**ℹ️ Informações do Sistema**")
        st.write("""
        **UAN Dashboard** é uma plataforma para:
        - ✓ Análise de dados financeiros
        - ✓ Projeções e simulações
        - ✓ Visualização de tendências
        - ✓ Gerenciamento com controle de permissões
        
        **Versão com Persistência de Dados**
        - Base de dados compartilhada (admin pode atualizar)
        - Simulações individuais por usuário
        - Armazenamento em arquivos (mock database)
        """)
