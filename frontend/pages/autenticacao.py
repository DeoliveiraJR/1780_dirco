"""
Página de Autenticação
"""

import streamlit as st


def renderizar():
    """Renderiza página de autenticação"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Login")
        st.markdown("---")
        
        # Formulário de login
        email = st.text_input("Email", placeholder="seu@email.com")
        senha = st.text_input("Senha", type="password", placeholder="••••••••")
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            if st.button("🔓 Entrar", use_container_width=True):
                if email and senha:
                    st.success(f"✓ Bem-vindo, {email}!")
                    st.session_state.autenticado = True
                    st.session_state.usuario_email = email
                else:
                    st.error("Por favor, preencha todos os campos")
        
        with col_right:
            if st.button("📝 Registrar", use_container_width=True):
                st.info("Funcionalidade de registro será implementada em breve")
        
        st.markdown("---")
        st.markdown("""
        **Credenciais de Teste:**
        - Email: `teste@uan.com.br`
        - Senha: `123456`
        """)
