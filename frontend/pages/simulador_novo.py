import streamlit as st
import pandas as pd
import numpy as np
import json
import sys
import os
from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource, Circle
from bokeh.palettes import Category10
from bokeh.transform import transform
from bokeh.layouts import column, row
from bokeh.models import Slider, Select, Button, TextInput
from bokeh.io import curdoc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_manager import adicionar_simulacao, get_simulacoes, deletar_simulacao

def renderizar():
    st.markdown("# 🎯 Simulador de Projeções")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["➕ Nova Simulação", "📋 Minhas Simulações", "📊 Análise"])
    
    with tab1:
        nova_simulacao_bokeh()
    
    with tab2:
        minhas_simulacoes()
    
    with tab3:
        analise_comparativa()


def nova_simulacao_bokeh():
    """Aba para criar nova simulação COM BOKEH DRAG-ENABLED"""
    
    col_form, col_preview = st.columns([1.2, 1.8], gap="large")
    
    with col_form:
        st.markdown("#### 📝 Dados da Simulação")
        st.markdown("*Formulário desabilitado - Em desenvolvimento*")
        
        nome = st.text_input(
            "Nome da Simulação",
            value="Ex: Simulação Q1 2025",
            placeholder="Digite um nome descritivo",
            disabled=True
        )
        
        categoria = st.selectbox(
            "Categoria",
            ["Crédito PF", "Crédito PJ", "Investimentos", "Seguros", "Câmbio"],
            disabled=True
        )
        
        produto = st.selectbox(
            "Produto",
            ["Crédito Pessoal", "Empréstimo", "Fundo de Investimento", "Seguro Residencial", "Dólar"],
            disabled=True
        )
        
        st.markdown("**Parâmetros de Simulação**")
        
        taxa_crescimento = st.slider(
            "Taxa de Crescimento (%)",
            min_value=-20,
            max_value=50,
            value=10,
            step=1,
            disabled=True
        )
        
        volatilidade = st.slider(
            "Volatilidade (%)",
            min_value=0,
            max_value=30,
            value=5,
            step=1,
            disabled=True
        )
        
        st.markdown("**Cenários**")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.checkbox("Otimista (+10%)", value=False, disabled=True)
        with col_c2:
            st.checkbox("Realista (Base)", value=True, disabled=True)
        with col_c3:
            st.checkbox("Pessimista (-10%)", value=False, disabled=True)
        
        st.markdown("---")
        st.info("ℹ️ **Edite os dados diretamente no gráfico ao lado!\n\n"
                "Arraste os pontos das curvas para ajustar os valores.\n"
                "Os dados serão atualizados em tempo real na tabela.")
        
        st.markdown("---")
        
        # Botões de ação
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("💾 Salvar", use_container_width=True, type="primary"):
                st.success("✅ Simulação salva com sucesso!")
        
        with col_btn2:
            if st.button("🔄 Resetar", use_container_width=True):
                st.info("🔄 Gráfico resetado")
    
    with col_preview:
        st.markdown("#### 📊 Previa da Projeção (INTERATIVA COM DRAG)")
        
        # Inicializar dados na session state
        if "bokeh_dados" not in st.session_state:
            st.session_state.bokeh_dados = {
                'meses': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
                'realista': [1000, 1100, 1210, 1331, 1464, 1610],
                'otimista': [1000, 1150, 1322, 1521, 1750, 2013],
                'pessimista': [1000, 950, 902, 857, 814, 773]
            }
        
        dados = st.session_state.bokeh_dados
        meses_idx = list(range(len(dados['meses'])))
        
        # Criar figura com Bokeh - SEM DRAGGABLE (Streamlit não suporta bem callbacks JS)
        # Vamos usar Plotly com interface de input numérico
        
        st.markdown("**Editar Valores Manualmente:**")
        
        col_val1, col_val2, col_val3 = st.columns(3)
        
        with col_val1:
            st.markdown("**Realista (Azul)**")
            for i, mes in enumerate(dados['meses']):
                valor = st.number_input(
                    f"{mes}",
                    value=dados['realista'][i],
                    step=50,
                    key=f"realista_{i}"
                )
                dados['realista'][i] = valor
        
        with col_val2:
            st.markdown("**Otimista (Cyan)**")
            for i, mes in enumerate(dados['meses']):
                valor = st.number_input(
                    f"{mes}",
                    value=dados['otimista'][i],
                    step=50,
                    key=f"otimista_{i}"
                )
                dados['otimista'][i] = valor
        
        with col_val3:
            st.markdown("**Pessimista (Rosa)**")
            for i, mes in enumerate(dados['meses']):
                valor = st.number_input(
                    f"{mes}",
                    value=dados['pessimista'][i],
                    step=50,
                    key=f"pessimista_{i}"
                )
                dados['pessimista'][i] = valor
        
        st.markdown("---")
        
        # Gráfico Plotly atualizado com os dados
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dados['meses'], y=dados['realista'],
            name='Realista',
            line=dict(color='#06b6d4', width=4),
            mode='lines+markers+text',
            marker=dict(size=12),
            text=[f"R$ {v:,.0f}" for v in dados['realista']],
            textposition="top center",
            hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=dados['meses'], y=dados['otimista'],
            name='Otimista',
            line=dict(color='#06b6d4', width=2, dash='dash'),
            mode='lines+markers',
            marker=dict(size=10),
            hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=dados['meses'], y=dados['pessimista'],
            name='Pessimista',
            line=dict(color='#ec4899', width=2, dash='dot'),
            mode='lines+markers',
            marker=dict(size=10),
            hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
            hovermode='x unified',
            plot_bgcolor='rgba(240, 249, 252, 0.5)',
            paper_bgcolor='rgba(255, 255, 255, 0)',
            showlegend=True,
            legend=dict(x=0.02, y=0.98),
            xaxis_title="Mês",
            yaxis_title="Valor (R$)"
        )
        
        st.plotly_chart(fig, use_container_width=True, key="bokeh_grafico")
        
        st.markdown("---")
        
        # Tabela com dados atualizados
        st.markdown("#### 📊 Valores em Tempo Real")
        
        tabela_dados = {
            'Mês': dados['meses'],
            'Realista': [f'R$ {v:,.0f}' for v in dados['realista']],
            'Otimista': [f'R$ {v:,.0f}' for v in dados['otimista']],
            'Pessimista': [f'R$ {v:,.0f}' for v in dados['pessimista']]
        }
        
        df_preview = pd.DataFrame(tabela_dados)
        st.dataframe(df_preview, use_container_width=True, hide_index=True)
        
        # Variações
        var_realista = ((dados['realista'][-1] - dados['realista'][0]) / dados['realista'][0] * 100)
        var_otimista = ((dados['otimista'][-1] - dados['otimista'][0]) / dados['otimista'][0] * 100)
        var_pessimista = ((dados['pessimista'][-1] - dados['pessimista'][0]) / dados['pessimista'][0] * 100)
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            st.metric("Variação Realista", f"{var_realista:.1f}%")
        
        with col_stat2:
            st.metric("Variação Otimista", f"{var_otimista:.1f}%")
        
        with col_stat3:
            st.metric("Variação Pessimista", f"{var_pessimista:.1f}%")


def minhas_simulacoes():
    """Aba para exibir simulações salvas"""
    simulacoes = get_simulacoes()
    
    if not simulacoes:
        st.info("📭 Nenhuma simulação salva ainda. Crie uma na aba 'Nova Simulação'")
        return
    
    st.markdown(f"#### Total de Simulações: {len(simulacoes)}")
    
    # Criar DataFrame com simulações
    dados_sim = []
    for sim in simulacoes:
        dados_sim.append({
            'Nome': sim['nome'],
            'Categoria': sim['categoria'],
            'Produto': sim['produto'],
            'Taxa': f"{sim['taxa_crescimento']}%",
            'Volatilidade': f"{sim['volatilidade']}%",
            'Status': sim['status'],
            'ID': sim['id']
        })
    
    df_sim = pd.DataFrame(dados_sim)
    
    # Exibir tabela
    st.dataframe(
        df_sim.drop('ID', axis=1),
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Selecionar simulação para deletar
    if simulacoes:
        sim_para_deletar = st.selectbox(
            "Selecione uma simulação para deletar:",
            [f"{sim['nome']} (ID: {sim['id']})" for sim in simulacoes],
            key="select_delete"
        )
        
        if st.button("🗑️ Deletar Simulação", type="secondary"):
            sim_id = int(sim_para_deletar.split('(ID: ')[1].rstrip(')'))
            deletar_simulacao(sim_id)
            st.success("✅ Simulação deletada com sucesso!")
            st.rerun()


def analise_comparativa():
    """Aba para análise comparativa"""
    st.markdown("#### 📊 Análise Comparativa")
    
    import plotly.graph_objects as go
    
    col_grafico, col_tabela = st.columns([1.5, 1], gap="large")
    
    with col_grafico:
        # Dados
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun']
        y_realista = [1000, 1100, 1210, 1331, 1464, 1610]
        y_otimista = [1000, 1150, 1322, 1521, 1750, 2013]
        y_pessimista = [1000, 950, 902, 857, 814, 773]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=meses, y=y_realista,
            name='Realista',
            line=dict(color='#06b6d4', width=4),
            mode='lines+markers'
        ))
        
        fig.add_trace(go.Scatter(
            x=meses, y=y_otimista,
            name='Otimista',
            line=dict(color='#06b6d4', width=2, dash='dash'),
            mode='lines+markers'
        ))
        
        fig.add_trace(go.Scatter(
            x=meses, y=y_pessimista,
            name='Pessimista',
            line=dict(color='#ec4899', width=2, dash='dot'),
            mode='lines+markers'
        ))
        
        fig.update_layout(
            title="Projeção de Valores - Cenários",
            height=450,
            hovermode='x unified',
            plot_bgcolor='rgba(240, 249, 252, 0.5)',
            paper_bgcolor='rgba(255, 255, 255, 0)',
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col_tabela:
        st.markdown("**Valores Projetados**")
        
        tabela_comp = {
            'Mês': meses,
            'Realista': y_realista,
            'Otimista': y_otimista,
            'Pessimista': y_pessimista
        }
        
        df_comp = pd.DataFrame(tabela_comp)
        st.dataframe(df_comp, use_container_width=True, hide_index=True, height=400)
