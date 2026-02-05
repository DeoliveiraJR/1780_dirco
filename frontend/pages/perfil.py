"""
Página de Perfil do Usuário
"""

import streamlit as st
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def renderizar():
    """Renderiza página de perfil"""
    
    st.markdown("### 👤 Perfil do Usuário")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["👤 Dados Pessoais", "🔐 Segurança", "📝 Histórico"])
    
    with tab1:
        dados_pessoais()
    
    with tab2:
        seguranca()
    
    with tab3:
        historico()


def dados_pessoais():
    """Exibe e permite editar dados pessoais"""
    
    col_foto, col_dados = st.columns([1, 2])
    
    with col_foto:
        st.markdown("#### Foto de Perfil")
        st.image(
            "https://via.placeholder.com/150",
            width=150,
            caption="Clique para alterar"
        )
        if st.button("📷 Alterar Foto", width='stretch'):
            st.info("Upload de foto implementado em breve")
    
    with col_dados:
        st.markdown("#### Informações Pessoais")
        
        nome = st.text_input("Nome Completo", value="João Silva Santos")
        email = st.text_input("Email", value="joao.silva@uan.com.br")
        telefone = st.text_input("Telefone", value="(11) 98765-4321")
        
        st.markdown("#### Informações Profissionais")
        
        departamento = st.selectbox(
            "Departamento",
            ["Análise de Dados", "Risco", "Crédito", "Operações", "Administração"]
        )
        
        funcao = st.text_input("Função", value="Analista de Dados Sênior")
        data_admissao = st.date_input("Data de Admissão", value=datetime(2020, 1, 15))
        
        st.markdown("---")
        
        col_save, col_cancel = st.columns(2)
        
        with col_save:
            if st.button("✓ Salvar Alterações", width='stretch', type="primary"):
                st.success("✓ Dados atualizados com sucesso!")
        
        with col_cancel:
            if st.button("✕ Cancelar", width='stretch'):
                st.rerun()


def seguranca():
    """Gerenciar segurança da conta"""
    
    st.markdown("#### Alterar Senha")
    
    col_passwd1, col_passwd2 = st.columns(1)[0], st.columns(1)[0]
    
    senha_atual = st.text_input("Senha Atual", type="password")
    senha_nova = st.text_input("Nova Senha", type="password")
    senha_confirmacao = st.text_input("Confirmar Nova Senha", type="password")
    
    if st.button("🔄 Atualizar Senha", width='stretch'):
        if senha_atual and senha_nova and senha_confirmacao:
            if senha_nova == senha_confirmacao:
                st.success("✓ Senha alterada com sucesso!")
            else:
                st.error("❌ As senhas não coincidem")
        else:
            st.error("❌ Preencha todos os campos")
    
    st.markdown("---")
    
    st.markdown("#### Autenticação de Dois Fatores (2FA)")
    
    auth_2fa = st.checkbox("Ativar autenticação de dois fatores", value=False)
    
    if auth_2fa:
        st.info("📱 Escaneie o código QR com seu app autenticador")
        st.image(
            "https://via.placeholder.com/200",
            width=200,
            caption="QR Code - App Autenticador"
        )
        
        codigo_backup = st.text_input("Digite o código de 6 dígitos", placeholder="000000")
        
        if st.button("✓ Confirmar 2FA", width='stretch'):
            st.success("✓ Autenticação de dois fatores ativada!")
    
    st.markdown("---")
    
    st.markdown("#### Sessões Ativas")
    
    sessoes = [
        {
            'dispositivo': 'Windows PC',
            'ip': '192.168.1.100',
            'localizacao': 'São Paulo, SP',
            'data_acesso': '20/01/2025 14:30'
        },
        {
            'dispositivo': 'iPhone 14',
            'ip': '189.45.67.89',
            'localizacao': 'São Paulo, SP',
            'data_acesso': '20/01/2025 09:15'
        }
    ]
    
    for sessao in sessoes:
        col_sess, col_actions = st.columns([3, 1])
        
        with col_sess:
            st.markdown(f"""
            **{sessao['dispositivo']}** • {sessao['localizacao']}
            
            IP: {sessao['ip']} | {sessao['data_acesso']}
            """)
        
        with col_actions:
            if st.button("❌ Logout", key=f"logout_{sessao['dispositivo']}"):
                st.warning(f"Encerrando sessão: {sessao['dispositivo']}")


def historico():
    """Exibe histórico de atividades"""
    
    st.markdown("#### Histórico de Atividades")
    
    atividades = [
        {
            'data': '20/01/2025 14:30',
            'acao': 'Login',
            'detalhes': 'Windows PC - São Paulo, SP'
        },
        {
            'data': '20/01/2025 14:35',
            'acao': 'Acesso Dashboard',
            'detalhes': 'Visualizou análise de projeções'
        },
        {
            'data': '20/01/2025 15:00',
            'acao': 'Criou Simulação',
            'detalhes': 'Simulação Q1 2025 - Pessoa Física'
        },
        {
            'data': '19/01/2025 09:15',
            'acao': 'Login',
            'detalhes': 'iPhone 14 - São Paulo, SP'
        },
        {
            'data': '19/01/2025 09:45',
            'acao': 'Download Relatório',
            'detalhes': 'Exportou dados do dashboard'
        },
        {
            'data': '18/01/2025 16:20',
            'acao': 'Logout',
            'detalhes': 'Encerrou sessão'
        }
    ]
    
    for ativ in atividades:
        col_time, col_action, col_details = st.columns([1.5, 1.5, 2])
        
        with col_time:
            st.markdown(f"⏰ {ativ['data']}")
        
        with col_action:
            st.markdown(f"**{ativ['acao']}**")
        
        with col_details:
            st.markdown(f"_{ativ['detalhes']}_")
        
        st.markdown("---")
    
    st.markdown("#### Download de Dados")
    
    col_export1, col_export2, col_export3 = st.columns(3)
    
    with col_export1:
        if st.button("📊 Exportar Simulações", width='stretch'):
            st.info("Download iniciado...")
    
    with col_export2:
        if st.button("📈 Exportar Histórico", width='stretch'):
            st.info("Download iniciado...")
    
    with col_export3:
        if st.button("📋 Exportar Relatório", width='stretch'):
            st.info("Download iniciado...")
