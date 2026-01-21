import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_manager import get_dados_upload, get_metricas_dashboard

def renderizar():
    st.markdown("# 📊 Dashboard de Analises")
    st.markdown("**Visao geral de dados financeiros e projecoes de mercado**")
    
    st.markdown("---")
    
    # Carregar dados do upload se disponível
    df_upload = get_dados_upload()
    metricas = get_metricas_dashboard()
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        valor_total = metricas.get('valor_total', 2480000)
        st.metric(
            label="Valor Total Projetado", 
            value=f"R$ {valor_total/1000000:.2f}M" if valor_total > 0 else "R$ 2.48M",
            delta="+12.5%"
        )
    
    with col2:
        realizado = metricas.get('realizado_atual', 1850000)
        st.metric(
            label="Realizado Atual", 
            value=f"R$ {realizado/1000000:.2f}M" if realizado > 0 else "R$ 1.85M",
            delta="+8.3%"
        )
    
    with col3:
        acuracia = metricas.get('taxa_acuracia', 87.2)
        st.metric(
            label="Taxa de Acuracia", 
            value=f"{acuracia:.1f}%" if acuracia > 0 else "87.2%",
            delta="+2.1%"
        )
    
    with col4:
        sim_ativas = metricas.get('simulacoes_ativas', 156)
        st.metric(
            label="Simulacoes Ativas", 
            value=str(sim_ativas) if sim_ativas > 0 else "156",
            delta="+24"
        )
    
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("#### 📈 Evolucao de Valores")
        
        np.random.seed(42)
        dias_recentes = pd.date_range('2025-08-01', periods=60, freq='D')
        valores_realizados = 1000000 + np.cumsum(np.random.randn(60) * 5000)
        valores_projetados = valores_realizados * 1.2
        
        fig_evolucao = go.Figure()
        
        fig_evolucao.add_trace(go.Scatter(
            x=dias_recentes, y=valores_realizados,
            name='Realizado',
            line=dict(color='#06b6d4', width=3),
            fill='tozeroy',
            fillcolor='rgba(6, 182, 212, 0.2)'
        ))
        
        fig_evolucao.add_trace(go.Scatter(
            x=dias_recentes, y=valores_projetados,
            name='Projetado',
            line=dict(color='#0c3a66', width=3, dash='dash'),
            fill='tonexty',
            fillcolor='rgba(12, 58, 102, 0.1)'
        ))
        
        fig_evolucao.update_layout(
            hovermode='x unified',
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor='rgba(240, 249, 252, 0.5)',
            paper_bgcolor='rgba(255, 255, 255, 0)'
        )
        
        st.plotly_chart(fig_evolucao, use_container_width=True)
    
    with col_chart2:
        st.markdown("#### 💹 Distribuicao por Categoria")
        
        if df_upload is not None and 'CATEGORIA' in df_upload.columns:
            categoria_sum = df_upload.groupby('CATEGORIA')['PROJETADO_AJUSTADO'].sum()
        else:
            categoria_sum = pd.Series({
                'Credito PF': 850000,
                'Credito PJ': 920000,
                'Investimentos': 710000
            })
        
        cores = ['#06b6d4', '#0c3a66', '#ec4899']
        
        fig_dist = go.Figure(data=[go.Pie(
            labels=categoria_sum.index,
            values=categoria_sum.values,
            marker=dict(colors=cores),
            hole=0.4,
            textposition='inside',
            textinfo='label+percent'
        )])
        
        fig_dist.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(255, 255, 255, 0)'
        )
        
        st.plotly_chart(fig_dist, use_container_width=True)
    
    st.markdown("---")
    
    col_chart3, col_chart4 = st.columns(2)
    
    with col_chart3:
        st.markdown("#### 📊 Comparacao Realizado vs Projetado")
        
        if df_upload is not None and 'MES' in df_upload.columns:
            mes_data = df_upload.groupby('MES').agg({
                'CURVA_REALIZADO': 'sum',
                'PROJETADO_ANALITICO': 'sum'
            }).reset_index()
            meses = mes_data['MES'].tolist()
            realizado = mes_data['CURVA_REALIZADO'].tolist()
            projetado = mes_data['PROJETADO_ANALITICO'].tolist()
        else:
            meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun']
            realizado = [450000, 520000, 480000, 550000, 490000, 610000]
            projetado = [500000, 550000, 520000, 580000, 540000, 650000]
        
        fig_comp = go.Figure(data=[
            go.Bar(name='Realizado', x=meses, y=realizado, marker_color='#06b6d4'),
            go.Bar(name='Projetado', x=meses, y=projetado, marker_color='#0c3a66')
        ])
        
        fig_comp.update_layout(
            barmode='group',
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            hovermode='x unified',
            plot_bgcolor='rgba(240, 249, 252, 0.5)',
            paper_bgcolor='rgba(255, 255, 255, 0)'
        )
        
        st.plotly_chart(fig_comp, use_container_width=True)
    
    with col_chart4:
        st.markdown("#### 🎯 Taxa de Crescimento por Produto")
        
        if df_upload is not None and 'PRODUTO' in df_upload.columns:
            prod_data = df_upload.groupby('PRODUTO').agg({
                'CURVA_REALIZADO': 'sum',
                'PROJETADO_AJUSTADO': 'sum'
            }).reset_index()
            prod_data['Taxa_Crescimento'] = ((prod_data['PROJETADO_AJUSTADO'] - prod_data['CURVA_REALIZADO']) / prod_data['CURVA_REALIZADO'] * 100).round(2)
            produtos = prod_data['PRODUTO'].tolist()
            taxas = prod_data['Taxa_Crescimento'].tolist()
        else:
            produtos = ['Credito Pessoal', 'Emprestimo', 'Fundo Invest.']
            taxas = [12.5, 18.3, 15.7]
        
        colors_taxa = ['#06b6d4' if x > 10 else '#a855f7' for x in taxas]
        
        fig_taxa = go.Figure(data=[
            go.Bar(y=produtos, x=taxas, orientation='h', marker_color=colors_taxa)
        ])
        
        fig_taxa.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title='Taxa de Crescimento (%)',
            plot_bgcolor='rgba(240, 249, 252, 0.5)',
            paper_bgcolor='rgba(255, 255, 255, 0)'
        )
        
        st.plotly_chart(fig_taxa, use_container_width=True)
    
    st.markdown("---")
    
    # Tabela de Variação Mensal
    st.markdown("#### 📈 Variacao Mensal por Ano")
    
    gerar_tabela_variacao()


def gerar_tabela_variacao():
    """Gera tabela com variação percentual mensal por ano"""
    
    if get_dados_upload() is not None:
        df = get_dados_upload()
        
        # Agrupar por mês e ano
        df['MES_NUM'] = pd.to_datetime(df['DATA_COMPLETA'], format='%d/%m/%Y').dt.month
        df['MES_NOME'] = pd.to_datetime(df['DATA_COMPLETA'], format='%d/%m/%Y').dt.strftime('%B').str.upper()
        
        anos = sorted(df['ANO'].unique())
        meses_ordem = ['JANEIRO', 'FEVEREIRO', 'MARCO', 'ABRIL', 'MAIO', 'JUNHO', 
                       'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']
        
        # Criar pivot table
        pivot_data = df.pivot_table(
            values='CURVA_REALIZADO',
            index='MES_NOME',
            columns='ANO',
            aggfunc='sum'
        )
        
        # Reordenar por meses
        pivot_data = pivot_data.reindex([m for m in meses_ordem if m in pivot_data.index])
        
        # Calcular variação percentual
        tabela_variacao = pd.DataFrame(index=pivot_data.index)
        
        for ano in anos:
            if ano in pivot_data.columns:
                tabela_variacao[f'REALIZADO {ano}'] = pivot_data[ano].apply(
                    lambda x: f'R$ {x:,.0f}' if pd.notna(x) else 'R$ 0,00'
                )
                
                if ano > anos[0]:
                    ano_anterior = ano - 1
                    if ano_anterior in pivot_data.columns:
                        variacao = ((pivot_data[ano] - pivot_data[ano_anterior]) / pivot_data[ano_anterior] * 100).fillna(0)
                        tabela_variacao[f'% VARIACAO {ano}'] = variacao.apply(
                            lambda x: f'{x:.1f}%' if x != 0 else '0%'
                        )
        
        # Exibir tabela
        st.dataframe(
            tabela_variacao,
            use_container_width=True,
            height=400
        )
    else:
        # Dados de exemplo
        meses = ['JANEIRO', 'FEVEREIRO', 'MARCO', 'ABRIL', 'MAIO', 'JUNHO',
                 'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']
        
        dados_tabela = {
            'REALIZADO 2022': ['R$ 0,00'] * 12,
            '% VARIACAO 2023': ['0%'] * 12,
            'REALIZADO 2023': ['R$ 0,00'] * 12,
            '% VARIACAO 2024': ['0%'] * 12,
            'REALIZADO 2024': ['R$ 0,00'] * 12,
            '% VARIACAO 2025': ['0%'] * 12,
            'REALIZADO 2025': ['R$ 0,00'] * 12
        }
        
        df_exemplo = pd.DataFrame(dados_tabela, index=meses)
        
        st.dataframe(
            df_exemplo,
            use_container_width=True,
            height=400
        )
        
        st.info("ℹ️ Carregue dados na pagina 'Upload' para atualizar a tabela com valores reais.")
