import streamlit as st
import pandas as pd
import numpy as np
import json
import sys
import os
import plotly.graph_objects as go
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
    """Aba para criar nova simulação COM INTERATIVIDADE DE ARRASTO"""
    
    col_form, col_preview = st.columns([1.2, 1.8], gap="large")
    
    with col_form:
        st.markdown("#### 📝 Dados da Simulação")
        st.markdown("*Formulário desabilitado - Em desenvolvimento*")
        
        nome = st.text_input(
            "Nome da Simulacao",
            value="Ex: Simulacao Q1 2025",
            placeholder="Digite um nome descritivo"
        )
        
        categoria = st.selectbox(
            "Categoria",
            ["Credito PF", "Credito PJ", "Investimentos", "Seguros", "Cambio"]
        )
        
        produto = st.selectbox(
            "Produto",
            ["Credito Pessoal", "Emprestimo", "Fundo de Investimento", "Seguro Residencial", "Dolar"]
        )
        
        st.markdown("**Parametros de Simulacao**")
        
        taxa_crescimento = st.slider(
            "Taxa de Crescimento (%)",
            min_value=-20,
            max_value=50,
            value=10,
            step=1
        )
        
        volatilidade = st.slider(
            "Volatilidade (%)",
            min_value=0,
            max_value=30,
            value=5,
            step=1
        )
        
        st.markdown("**Cenarios**")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            otimista = st.checkbox("Otimista (+10%)", value=False)
        with col_c2:
            realista = st.checkbox("Realista (Base)", value=True)
        with col_c3:
            pessimista = st.checkbox("Pessimista (-10%)", value=False)
        
        cenarios = {
            "Otimista": otimista,
            "Realista": realista,
            "Pessimista": pessimista
        }
        
        st.markdown("---")
        
        if st.button("💾 Salvar Simulacao", use_container_width=True, type="primary"):
            # Gerar dados do gráfico
            meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun']
            base_value = 1000
            
            dados_grafico = {}
            for cenario, ativo in cenarios.items():
                if ativo:
                    if cenario == "Otimista":
                        valores = [base_value * (1 + (taxa_crescimento + 10) / 100) ** (i / 6) for i in range(len(meses))]
                    elif cenario == "Pessimista":
                        valores = [base_value * (1 + (taxa_crescimento - 10) / 100) ** (i / 6) for i in range(len(meses))]
                    else:  # Realista
                        valores = [base_value * (1 + taxa_crescimento / 100) ** (i / 6) for i in range(len(meses))]
                    
                    dados_grafico[cenario] = [float(v) for v in valores]
            
            sim = adicionar_simulacao(
                nome=nome,
                categoria=categoria,
                produto=produto,
                taxa_crescimento=taxa_crescimento,
                volatilidade=volatilidade,
                cenarios=cenarios,
                dados_grafico=dados_grafico
            )
            
            st.success(f"✅ Simulacao '{nome}' salva com sucesso!")
            st.balloons()
    
    with col_preview:
        st.markdown("#### 📊 Previa da Projecao")
        
        # Inicializar dados editáveis na session_state
        if 'valores_editaveis' not in st.session_state:
            meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun']
            base_value = 1000
            st.session_state.valores_editaveis = {
                'meses': meses,
                'realista': [base_value * (1 + taxa_crescimento / 100) ** (i / 6) for i in range(len(meses))],
                'otimista': [base_value * (1 + (taxa_crescimento + 10) / 100) ** (i / 6) for i in range(len(meses))],
                'pessimista': [base_value * (1 + (taxa_crescimento - 10) / 100) ** (i / 6) for i in range(len(meses))]
            }
        
        # Atualizar valores baseado nos sliders (recalcular)
        meses = st.session_state.valores_editaveis['meses']
        base_value = 1000
        st.session_state.valores_editaveis['realista'] = [base_value * (1 + taxa_crescimento / 100) ** (i / 6) for i in range(len(meses))]
        st.session_state.valores_editaveis['otimista'] = [base_value * (1 + (taxa_crescimento + 10) / 100) ** (i / 6) for i in range(len(meses))]
        st.session_state.valores_editaveis['pessimista'] = [base_value * (1 + (taxa_crescimento - 10) / 100) ** (i / 6) for i in range(len(meses))]
        
        y_realista = st.session_state.valores_editaveis['realista']
        y_otimista = st.session_state.valores_editaveis['otimista']
        y_pessimista = st.session_state.valores_editaveis['pessimista']
        
        # Criar figura com Plotly EDITÁVEL (drag points)
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=meses, y=y_realista,
            name='Realista',
            line=dict(color='#06b6d4', width=3),
            mode='lines+markers',
            marker=dict(size=12, line=dict(width=2, color='white')),
            hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=meses, y=y_otimista,
            name='Otimista',
            line=dict(color='#10b981', width=2, dash='dash'),
            mode='lines+markers',
            marker=dict(size=10, line=dict(width=2, color='white')),
            hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=meses, y=y_pessimista,
            name='Pessimista',
            line=dict(color='#ef4444', width=2, dash='dot'),
            mode='lines+markers',
            marker=dict(size=10, line=dict(width=2, color='white')),
            hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            height=450,
            margin=dict(l=10, r=10, t=40, b=10),
            hovermode='x unified',
            plot_bgcolor='rgba(240, 249, 252, 0.5)',
            paper_bgcolor='rgba(255, 255, 255, 0)',
            showlegend=True,
            legend=dict(x=0.02, y=0.98, bgcolor='rgba(255,255,255,0.8)'),
            dragmode='pan',
            xaxis=dict(fixedrange=False),
            yaxis=dict(fixedrange=False, tickformat=',.0f', tickprefix='R$ '),
            title=dict(
                text='<b>Arraste os pontos para editar valores</b>',
                font=dict(size=14, color='#64748b'),
                x=0.5,
                xanchor='center'
            )
        )
        
        # Renderizar gráfico com config editável
        config = {
            'editable': True,
            'edits': {'shapePosition': True},
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToAdd': ['drawopenpath', 'eraseshape'],
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }
        
        st.plotly_chart(fig, use_container_width=True, config=config, key='grafico_interativo')
        
        st.info("💡 **Dica:** Use o mouse para arrastar os pontos do gráfico e ajustar as projeções em tempo real!")
        
        # Tabela de valores atualizada
        st.markdown("#### 📋 Valores Projetados")
        
        col_tab1, col_tab2 = st.columns([2, 1])
        
        with col_tab1:
            tabela_dados = {
                'Mês': meses,
                'Realista': [f'R$ {v:,.0f}' for v in y_realista],
                'Otimista': [f'R$ {v:,.0f}' for v in y_otimista],
                'Pessimista': [f'R$ {v:,.0f}' for v in y_pessimista]
            }
            
            df_preview = pd.DataFrame(tabela_dados)
            st.dataframe(
                df_preview, 
                use_container_width=True, 
                hide_index=True,
                height=250
            )
        
        with col_tab2:
            st.markdown("**Resumo**")
            st.metric("Média Realista", f"R$ {np.mean(y_realista):,.0f}")
            st.metric("Total 6 Meses", f"R$ {sum(y_realista):,.0f}")
            variacao = ((y_realista[-1] - y_realista[0]) / y_realista[0]) * 100
            st.metric("Variação", f"{variacao:.1f}%", delta=f"{variacao:.1f}%")


def minhas_simulacoes():
    """Aba para exibir simulações salvas"""
    simulacoes = get_simulacoes()
    
    if not simulacoes:
        st.info("📭 Nenhuma simulacao salva ainda. Crie uma na aba 'Nova Simulacao'")
        return
    
    st.markdown(f"#### Total de Simulacoes: {len(simulacoes)}")
    
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
    sim_para_deletar = st.selectbox(
        "Selecione uma simulacao para deletar:",
        [f"{sim['nome']} (ID: {sim['id']})" for sim in simulacoes],
        key="select_delete"
    )
    
    if st.button("🗑️ Deletar Simulacao", type="secondary"):
        sim_id = int(sim_para_deletar.split('(ID: ')[1].rstrip(')'))
        deletar_simulacao(sim_id)
        st.success("✅ Simulacao deletada com sucesso!")
        st.rerun()


def analise_comparativa():
    """Aba para análise comparativa com gráfico interativo"""
    st.markdown("#### 📊 Análise Comparativa - Gráfico Interativo")
    
    col_grafico, col_tabela = st.columns([1.5, 1], gap="large")
    
    with col_grafico:
        st.markdown("**Gráfico Interativo - Zoom, Pan e Análise**")
        
        # Dados iniciais
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun']
        
        # Valores iniciais
        y_realista = [1000, 1100, 1210, 1331, 1464, 1610]
        y_otimista = [1000, 1150, 1322, 1521, 1750, 2013]
        y_pessimista = [1000, 950, 902, 857, 814, 773]
        
        # Criar figura com Plotly (funciona melhor no Streamlit)
        fig = go.Figure()
        
        # Linha Realista
        fig.add_trace(go.Scatter(
            x=meses, y=y_realista,
            name='Realista',
            line=dict(color='#06b6d4', width=4),
            mode='lines+markers',
            marker=dict(size=10)
        ))
        
        # Linha Otimista (tracejada)
        fig.add_trace(go.Scatter(
            x=meses, y=y_otimista,
            name='Otimista',
            line=dict(color='#06b6d4', width=2, dash='dash'),
            mode='lines+markers',
            marker=dict(size=8)
        ))
        
        # Linha Pessimista (pontilhada)
        fig.add_trace(go.Scatter(
            x=meses, y=y_pessimista,
            name='Pessimista',
            line=dict(color='#ec4899', width=2, dash='dot'),
            mode='lines+markers',
            marker=dict(size=8)
        ))
        
        # Customizar layout
        fig.update_layout(
            title="Projeção de Valores - Cenários (Arrastar para Zoom, Duplo-clique para Reset)",
            height=450,
            hovermode='x unified',
            plot_bgcolor='rgba(240, 249, 252, 0.5)',
            paper_bgcolor='rgba(255, 255, 255, 0)',
            font=dict(family="Arial, sans-serif", size=12),
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(200, 200, 200, 0.2)'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(200, 200, 200, 0.2)'
            ),
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#06b6d4',
                borderwidth=1
            )
        )
        
        # Exibir figura
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("💡 **Dica Interativa:** \n"
                "- 🔍 Arraste para fazer zoom\n"
                "- 📍 Duplo-clique para resetar\n"
                "- 👆 Passe o mouse para ver valores exatos")
    
    with col_tabela:
        st.markdown("**Valores Projetados**")
        
        tabela_comp = {
            'Mes': meses,
            'Realista': y_realista,
            'Otimista': y_otimista,
            'Pessimista': y_pessimista
        }
        
        df_comp = pd.DataFrame(tabela_comp)
        
        # Formatar com cores
        st.dataframe(
            df_comp,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        st.markdown("---")
        st.markdown("**Estatísticas**")
        
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric(
                "Variação Realista",
                f"{((y_realista[-1] - y_realista[0]) / y_realista[0] * 100):.1f}%",
                delta=f"+R$ {y_realista[-1] - y_realista[0]:,.0f}"
            )
            st.metric(
                "Variação Otimista",
                f"{((y_otimista[-1] - y_otimista[0]) / y_otimista[0] * 100):.1f}%",
                delta=f"+R$ {y_otimista[-1] - y_otimista[0]:,.0f}"
            )
        
        with col_stat2:
            st.metric(
                "Variação Pessimista",
                f"{((y_pessimista[-1] - y_pessimista[0]) / y_pessimista[0] * 100):.1f}%",
                delta=f"+R$ {y_pessimista[-1] - y_pessimista[0]:,.0f}"
            )
            st.metric(
                "Diferenca O/P",
                f"R$ {y_otimista[-1] - y_pessimista[-1]:,.0f}",
                delta=f"{((y_otimista[-1] - y_pessimista[-1]) / y_pessimista[-1] * 100):.1f}%"
            )
    
    st.markdown("---")
    
    st.markdown("#### 💾 Salvar Simulacao Editada")
    
    col_save1, col_save2 = st.columns([2, 1])
    
    with col_save1:
        nome_salvar = st.text_input(
            "Nome para salvar esta simulacao",
            value="Simulacao Analise Q1",
            key="nome_save"
        )
    
    with col_save2:
        if st.button("💾 Salvar", use_container_width=True, type="primary"):
            dados_grafico = {
                "Realista": y_realista,
                "Otimista": y_otimista,
                "Pessimista": y_pessimista
            }
            
            sim = adicionar_simulacao(
                nome=nome_salvar,
                categoria="Analise Comparativa",
                produto="Multiplo",
                taxa_crescimento=10,
                volatilidade=5,
                cenarios={"Realista": True, "Otimista": True, "Pessimista": True},
                dados_grafico=dados_grafico
            )
            
            st.success(f"✅ Simulacao salva com sucesso!")
            
            # Salvar no localStorage
            js_code = f"""
            <script>
                const simulacao = {json.dumps(sim, default=str)};
                localStorage.setItem('ultima_simulacao', JSON.stringify(simulacao));
                console.log('Simulação salva no localStorage:', simulacao.nome);
            </script>
            """
            st.components.v1.html(js_code, height=0)
