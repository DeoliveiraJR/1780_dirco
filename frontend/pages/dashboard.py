"""
Página de Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta


def renderizar():
    """Renderiza página do dashboard"""
    
    st.markdown("### 📊 Dashboard - Análise de Projeções Financeiras")
    st.markdown("---")
    
    # Gerar dados mockados para demonstração
    dados_demo = gerar_dados_demo()
    
    # KPIs principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Realizado",
            value="R$ 45.2M",
            delta="+12.5%",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="Projeção Analítica",
            value="R$ 52.8M",
            delta="+8.2%",
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            label="Projeção Mercado",
            value="R$ 48.5M",
            delta="-2.1%",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="Projeção Ajustada",
            value="R$ 51.3M",
            delta="+6.8%",
            delta_color="normal"
        )
    
    st.markdown("---")
    
    # Gráficos
    col_grafico1, col_grafico2 = st.columns(2)
    
    with col_grafico1:
        st.markdown("#### Evolução de Projeções (últimos 12 meses)")
        fig_linha = criar_grafico_linha()
        st.plotly_chart(fig_linha, use_container_width=True)
    
    with col_grafico2:
        st.markdown("#### Distribuição por Categoria")
        fig_pizza = criar_grafico_pizza()
        st.plotly_chart(fig_pizza, use_container_width=True)
    
    st.markdown("---")
    
    # Tabela de dados
    st.markdown("#### 📋 Últimos Registros")
    
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        categoria_selecionada = st.selectbox(
            "Categoria",
            ["Todas", "Pessoa Física", "Pessoa Jurídica", "Financiamento Imobiliário", 
             "Cartão de Crédito", "Empréstimo Pessoal"]
        )
    
    with col_filter2:
        mes_selecionado = st.selectbox(
            "Mês",
            ["Todos", "janeiro", "fevereiro", "março", "abril", "maio", "junho"]
        )
    
    with col_filter3:
        ano_selecionado = st.selectbox(
            "Ano",
            ["2025", "2024"]
        )
    
    # Filtrar dados
    dados_filtrados = dados_demo.copy()
    
    if categoria_selecionada != "Todas":
        dados_filtrados = dados_filtrados[dados_filtrados['Categoria'] == categoria_selecionada]
    
    if mes_selecionado != "Todos":
        dados_filtrados = dados_filtrados[dados_filtrados['Mês'] == mes_selecionado]
    
    dados_filtrados = dados_filtrados[dados_filtrados['Ano'] == ano_selecionado]
    
    st.dataframe(dados_filtrados, use_container_width=True)
    
    # Estatísticas adicionais
    st.markdown("---")
    st.markdown("#### 📈 Estatísticas")
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        st.info(f"**Total de Registros:** {len(dados_filtrados)}")
    
    with col_stat2:
        st.info(f"**Categorias Únicas:** {dados_filtrados['Categoria'].nunique()}")
    
    with col_stat3:
        media_realizado = dados_filtrados['Realizado'].mean()
        st.info(f"**Média Realizado:** R$ {media_realizado:,.2f}")


def gerar_dados_demo():
    """Gera dados de demonstração"""
    
    categorias = ['Pessoa Física', 'Pessoa Jurídica', 'Financiamento Imobiliário', 
                  'Cartão de Crédito', 'Empréstimo Pessoal', 'Renda Fixa']
    meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho']
    
    dados = []
    
    for ano in [2024, 2025]:
        for mes in meses:
            for categoria in categorias:
                valor_base = np.random.uniform(1000, 5000)
                
                dados.append({
                    'Data': f"01/{meses.index(mes)+1:02d}/{ano}",
                    'Mês': mes,
                    'Ano': str(ano),
                    'Categoria': categoria,
                    'Realizado': valor_base * np.random.uniform(0.9, 1.1),
                    'Projeção Analítica': valor_base * np.random.uniform(0.95, 1.05),
                    'Projeção Mercado': valor_base * np.random.uniform(0.85, 1.15),
                    'Projeção Ajustada': valor_base * np.random.uniform(0.95, 1.05),
                })
    
    return pd.DataFrame(dados)


def criar_grafico_linha():
    """Cria gráfico de linha das projeções"""
    
    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun']
    realizado = [35000, 36500, 38200, 40100, 42300, 45200]
    analitica = [37000, 38500, 40200, 42100, 44300, 47200]
    mercado = [33000, 34500, 36200, 38100, 40300, 43200]
    ajustada = [36500, 38000, 39800, 41700, 43900, 46300]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=meses, y=realizado,
        mode='lines+markers',
        name='Realizado',
        line=dict(color='#1f4788', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=meses, y=analitica,
        mode='lines+markers',
        name='Projeção Analítica',
        line=dict(color='#2e8b57', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=meses, y=mercado,
        mode='lines+markers',
        name='Projeção Mercado',
        line=dict(color='#ff6b6b', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=meses, y=ajustada,
        mode='lines+markers',
        name='Projeção Ajustada',
        line=dict(color='#ffd93d', width=3)
    ))
    
    fig.update_layout(
        hovermode='x unified',
        template='plotly_white',
        height=400,
        font=dict(size=11)
    )
    
    return fig


def criar_grafico_pizza():
    """Cria gráfico de pizza de distribuição"""
    
    categorias = ['Pessoa Física', 'Pessoa Jurídica', 'Financiamento', 
                  'Cartão de Crédito', 'Empréstimo', 'Renda Fixa']
    valores = [25, 20, 18, 15, 12, 10]
    cores = ['#1f4788', '#2d5aa8', '#667eea', '#764ba2', '#ff6b6b', '#ffd93d']
    
    fig = go.Figure(
        data=[go.Pie(
            labels=categorias,
            values=valores,
            marker=dict(colors=cores),
            hovertemplate='<b>%{label}</b><br>%{value}%<extra></extra>'
        )]
    )
    
    fig.update_layout(
        template='plotly_white',
        height=400,
        font=dict(size=11),
        showlegend=True
    )
    
    return fig
