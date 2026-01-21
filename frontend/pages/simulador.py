"""
Página de Simulador
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go


def renderizar():
    """Renderiza página do simulador"""
    
    st.markdown("### 🎯 Simulador de Projeções")
    st.markdown("---")
    
    # Abas principais
    tab1, tab2, tab3 = st.tabs(["➕ Nova Simulação", "📁 Minhas Simulações", "⚙️ Configurações"])
    
    with tab1:
        nova_simulacao()
    
    with tab2:
        minhas_simulacoes()
    
    with tab3:
        configuracoes_simulador()


def nova_simulacao():
    """Interface para criar nova simulação"""
    
    col_form, col_preview = st.columns([1.5, 1])
    
    with col_form:
        st.markdown("#### Dados da Simulação")
        
        nome_simulacao = st.text_input(
            "Nome da Simulação",
            placeholder="Ex: Simulação Q1 2025",
            help="Nome descritivo para identificar a simulação"
        )
        
        descricao = st.text_area(
            "Descrição",
            placeholder="Descreva os ajustes realizados nesta simulação",
            height=80
        )
        
        st.markdown("#### Parâmetros de Ajuste")
        
        col_param1, col_param2 = st.columns(2)
        
        with col_param1:
            categoria = st.selectbox(
                "Categoria",
                ["Pessoa Física", "Pessoa Jurídica", "Financiamento Imobiliário",
                 "Cartão de Crédito", "Empréstimo Pessoal", "Renda Fixa"]
            )
        
        with col_param2:
            periodo = st.select_slider(
                "Período (Meses)",
                options=list(range(1, 13)),
                value=(1, 12)
            )
        
        st.markdown("#### Ajustes de Valores")
        
        col_adj1, col_adj2 = st.columns(2)
        
        with col_adj1:
            taxa_crescimento = st.slider(
                "Taxa de Crescimento (%)",
                min_value=-20,
                max_value=50,
                value=5,
                step=1
            )
        
        with col_adj2:
            volatilidade = st.slider(
                "Volatilidade (%)",
                min_value=0,
                max_value=30,
                value=5,
                step=1
            )
        
        st.markdown("#### Cenários")
        
        col_cen1, col_cen2, col_cen3 = st.columns(3)
        
        with col_cen1:
            otimista = st.checkbox("Otimista (+10%)", value=False)
        
        with col_cen2:
            realista = st.checkbox("Realista", value=True)
        
        with col_cen3:
            pessimista = st.checkbox("Pessimista (-10%)", value=False)
        
        st.markdown("---")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("✓ Salvar Simulação", use_container_width=True, type="primary"):
                if nome_simulacao:
                    st.success(f"✓ Simulação '{nome_simulacao}' salva com sucesso!")
                    st.balloons()
                else:
                    st.error("Por favor, digite um nome para a simulação")
        
        with col_btn2:
            if st.button("🔄 Limpar Formulário", use_container_width=True):
                st.rerun()
    
    with col_preview:
        st.markdown("#### 📊 Prévia")
        
        if nome_simulacao:
            st.info(f"""
            **Simulação:** {nome_simulacao}
            
            **Categoria:** {categoria}
            
            **Período:** Mês {periodo[0]} a {periodo[1]}
            
            **Crescimento:** {taxa_crescimento}%
            
            **Volatilidade:** {volatilidade}%
            
            **Cenários:** {'Otimista ' if otimista else ''}{'Realista ' if realista else ''}{'Pessimista' if pessimista else ''}
            """)
        else:
            st.info("Preencha os dados ao lado para ver a prévia")
        
        # Gráfico de simulação
        st.markdown("#### Gráfico Simulado")
        fig = criar_grafico_simulacao()
        st.plotly_chart(fig, use_container_width=True)


def minhas_simulacoes():
    """Exibe simulações salvas do usuário"""
    
    st.markdown("#### Suas Simulações Salvas")
    
    simulacoes_exemplo = [
        {
            'Nome': 'Simulação Q1 2025',
            'Data': '15/01/2025',
            'Categoria': 'Pessoa Física',
            'Status': '✓ Ativa'
        },
        {
            'Nome': 'Simulação Cenário Pessimista',
            'Data': '10/01/2025',
            'Categoria': 'Cartão de Crédito',
            'Status': '✓ Ativa'
        },
        {
            'Nome': 'Simulação Baseline 2024',
            'Data': '01/12/2024',
            'Categoria': 'Renda Fixa',
            'Status': 'Inativa'
        }
    ]
    
    df_simulacoes = pd.DataFrame(simulacoes_exemplo)
    
    col_search = st.columns(1)[0]
    with col_search:
        busca = st.text_input("🔍 Buscar simulação", placeholder="Digite o nome da simulação")
    
    if busca:
        df_simulacoes = df_simulacoes[df_simulacoes['Nome'].str.contains(busca, case=False)]
    
    if len(df_simulacoes) > 0:
        for idx, sim in df_simulacoes.iterrows():
            col_info, col_actions = st.columns([4, 1])
            
            with col_info:
                st.markdown(f"""
                **{sim['Nome']}**
                
                Data: {sim['Data']} | Categoria: {sim['Categoria']} | {sim['Status']}
                """)
            
            with col_actions:
                col_edit, col_delete = st.columns(2)
                
                with col_edit:
                    if st.button("✏️", key=f"edit_{idx}"):
                        st.info(f"Editando: {sim['Nome']}")
                
                with col_delete:
                    if st.button("🗑️", key=f"delete_{idx}"):
                        st.warning(f"Deletar: {sim['Nome']}?")
            
            st.markdown("---")
    else:
        st.info("Nenhuma simulação encontrada")


def configuracoes_simulador():
    """Configurações do simulador"""
    
    st.markdown("#### Configurações do Simulador")
    
    col_config1, col_config2 = st.columns(2)
    
    with col_config1:
        st.markdown("##### Precisão de Cálculo")
        precisao = st.select_slider(
            "Nível de Precisão",
            options=['Baixa', 'Média', 'Alta'],
            value='Média',
            label_visibility="collapsed"
        )
    
    with col_config2:
        st.markdown("##### Modo de Simulação")
        modo = st.selectbox(
            "Modo",
            ['Simulação Rápida', 'Simulação Detalhada', 'Simulação Avançada'],
            label_visibility="collapsed"
        )
    
    st.markdown("---")
    
    st.markdown("##### Preferências")
    
    col_pref1, col_pref2 = st.columns(2)
    
    with col_pref1:
        auto_salvar = st.checkbox("Auto-salvar simulações", value=True)
    
    with col_pref2:
        notificacoes = st.checkbox("Ativar notificações", value=True)
    
    st.markdown("---")
    
    if st.button("💾 Salvar Configurações", use_container_width=True, type="primary"):
        st.success("✓ Configurações salvas com sucesso!")


def criar_grafico_simulacao():
    """Cria gráfico de simulação"""
    
    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun']
    base = [1000, 1050, 1102, 1157, 1215, 1276]
    otimista = [1100, 1165, 1237, 1316, 1401, 1494]
    pessimista = [900, 935, 972, 1011, 1052, 1096]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=meses, y=base,
        mode='lines+markers',
        name='Realista',
        line=dict(color='#2e8b57', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=meses, y=otimista,
        mode='lines+markers',
        name='Otimista',
        line=dict(color='#1f4788', width=2, dash='dot')
    ))
    
    fig.add_trace(go.Scatter(
        x=meses, y=pessimista,
        mode='lines+markers',
        name='Pessimista',
        line=dict(color='#ff6b6b', width=2, dash='dash')
    ))
    
    fig.update_layout(
        hovermode='x unified',
        template='plotly_white',
        height=300,
        font=dict(size=10),
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig
