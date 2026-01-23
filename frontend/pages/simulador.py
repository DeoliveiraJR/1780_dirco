import streamlit as st
import pandas as pd
import numpy as np
import json
import sys
import os
import plotly.graph_objects as go
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, PointDrawTool, CustomJS, Button, Div
from bokeh.layouts import column, row

try:
    from streamlit_bokeh_events import streamlit_bokeh_events
    BOKEH_EVENTS = True
except ImportError:
    try:
        from streamlit_bokeh import streamlit_bokeh
        BOKEH_EVENTS = False
    except ImportError:
        st.error("🚫 Instale: pip install streamlit-bokeh")
        BOKEH_EVENTS = None

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
        st.markdown("#### 📊 Previa da Projecao - Arraste os Pontos")
        
        if BOKEH_EVENTS is None:
            st.error("❌ streamlit-bokeh não instalado. Execute: pip install streamlit-bokeh")
            return
        
        # Cores
        COR_REALISTA = "#06b6d4"
        COR_OTIMISTA = "#10b981" 
        COR_PESSIMISTA = "#ef4444"
        
        # Dados base
        meses_num = list(range(1, 7))
        meses_label = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun']
        base_value = 1000
        
        # Calcular valores iniciais
        valores_realista = [base_value * (1 + taxa_crescimento / 100) ** (i / 6) for i in range(6)]
        valores_otimista = [base_value * (1 + (taxa_crescimento + 10) / 100) ** (i / 6) for i in range(6)]
        valores_pessimista = [base_value * (1 + (taxa_crescimento - 10) / 100) ** (i / 6) for i in range(6)]
        
        # Inicializar session_state
        if 'bokeh_realista' not in st.session_state or st.session_state.get('last_taxa_bokeh') != taxa_crescimento:
            st.session_state.bokeh_realista = valores_realista[:]
            st.session_state.last_taxa_bokeh = taxa_crescimento
        
        # ColumnDataSource EDITÁVEL
        source_realista = ColumnDataSource(data=dict(
            x=meses_num,
            y=st.session_state.bokeh_realista
        ))
        
        # ColumnDataSources estáticas
        source_otimista = ColumnDataSource(data=dict(x=meses_num, y=valores_otimista))
        source_pessimista = ColumnDataSource(data=dict(x=meses_num, y=valores_pessimista))
        
        # Criar figura Bokeh
        p = figure(
            title="👆 Clique e arraste os pontos azuis para ajustar valores",
            x_axis_label="Mês",
            y_axis_label="Valor (R$)",
            width=900,
            height=450,
            toolbar_location="right",
            x_range=(0.5, 6.5),
            y_range=(min(valores_pessimista) * 0.85, max(valores_otimista) * 1.15)
        )
        
        # Linhas estáticas
        p.line('x', 'y', source=source_otimista, color=COR_OTIMISTA, 
               line_width=2, line_dash='dashed', legend_label='Otimista (+10%)', alpha=0.7)
        p.line('x', 'y', source=source_pessimista, color=COR_PESSIMISTA, 
               line_width=2, line_dash='dotted', legend_label='Pessimista (-10%)', alpha=0.7)
        
        # Linha e pontos EDITÁVEIS
        p.line('x', 'y', source=source_realista, color=COR_REALISTA, 
               line_width=4, legend_label='Realista (Arraste)', alpha=0.9)
        renderer = p.circle('x', 'y', source=source_realista, size=16, 
                           color=COR_REALISTA, alpha=0.9, line_color='white', line_width=3)
        
        # Adicionar PointDrawTool
        draw_tool = PointDrawTool(renderers=[renderer], empty_value='nan')
        p.add_tools(draw_tool)
        p.toolbar.active_tap = draw_tool
        
        # Estilo
        p.legend.location = "top_left"
        p.legend.click_policy = "hide"
        p.background_fill_color = "#f0f9fc"
        p.background_fill_alpha = 0.5
        p.outline_line_color = None
        p.grid.grid_line_alpha = 0.3
        p.title.text_font_size = "13pt"
        
        # Botão Reset
        btn_reset = Button(label="🔄 Resetar", button_type="warning", width=150)
        btn_reset.js_on_click(CustomJS(args=dict(src=source_realista, vals=valores_realista), code="""
            for (let i = 0; i < src.data['y'].length; i++) {
                src.data['y'][i] = vals[i];
            }
            src.change.emit();
        """))
        
        # Info box
        info_div = Div(text="""
        <div style="background: #dbeafe; padding: 12px; border-radius: 8px; border-left: 4px solid #06b6d4;">
            <b>💡 Como usar:</b> Clique e arraste os pontos <b style="color:#06b6d4;">azuis (●)</b> 
            no gráfico para ajustar os valores da projeção Realista!
        </div>
        """)
        
        # Layout
        layout_bokeh = column(
            p,
            row(btn_reset, info_div, sizing_mode="stretch_width"),
            sizing_mode="stretch_width"
        )
        
        # Renderizar
        if BOKEH_EVENTS:
            result = streamlit_bokeh_events(
                layout_bokeh,
                events="tap,reset",
                key="bokeh_plot",
                refresh_on_update=False,
                debounce_time=0
            )
        else:
            from streamlit_bokeh import streamlit_bokeh
            streamlit_bokeh(layout_bokeh, key="bokeh_plot")
        
        st.markdown("---")
        
        # Tabela e resumo
        st.markdown("#### 📋 Valores Projetados")
        
        col_tab, col_resume = st.columns([2.5, 1.5])
        
        with col_tab:
            # Usar valores atuais do source
            y_atual = source_realista.data['y']
            
            tabela_dados = {
                'Mês': meses_label,
                'Realista': [f'R$ {v:,.0f}' for v in y_atual],
                'Otimista': [f'R$ {v:,.0f}' for v in valores_otimista],
                'Pessimista': [f'R$ {v:,.0f}' for v in valores_pessimista]
            }
            
            df_preview = pd.DataFrame(tabela_dados)
            st.dataframe(df_preview, use_container_width=True, hide_index=True, height=250)
        
        with col_resume:
            st.markdown("**📊 Resumo Realista**")
            st.metric("Média", f"R$ {np.mean(y_atual):,.0f}")
            st.metric("Total 6 Meses", f"R$ {sum(y_atual):,.0f}")
            variacao = ((y_atual[-1] - y_atual[0]) / y_atual[0]) * 100
            st.metric("Variação", f"{variacao:.1f}%", delta=f"{variacao:.1f}%")
        
        # ============== OPÇÃO ALTERNATIVA: SLIDERS ==============
        st.markdown("---")
        st.markdown("### ✏️ Opção Alternativa: Ajuste Fino com Sliders")
        
        with st.expander("🎯 Clique para abrir os Sliders de Edição", expanded=False):
            st.info("💡 Use os sliders abaixo para ajustar cada mês individualmente com precisão numérica!")
            
            # Inicializar valores dos sliders
            if 'slider_valores' not in st.session_state:
                st.session_state.slider_valores = y_atual[:]
            
            col_s1, col_s2, col_s3 = st.columns(3)
            
            with col_s1:
                st.session_state.slider_valores[0] = st.slider(
                    f"📅 {meses_label[0]}",
                    min_value=int(base_value * 0.7),
                    max_value=int(base_value * 1.5),
                    value=int(st.session_state.slider_valores[0]),
                    step=10,
                    format="R$ %d",
                    key="slider_jan"
                )
                
                st.session_state.slider_valores[1] = st.slider(
                    f"📅 {meses_label[1]}",
                    min_value=int(base_value * 0.7),
                    max_value=int(base_value * 1.5),
                    value=int(st.session_state.slider_valores[1]),
                    step=10,
                    format="R$ %d",
                    key="slider_fev"
                )
            
            with col_s2:
                st.session_state.slider_valores[2] = st.slider(
                    f"📅 {meses_label[2]}",
                    min_value=int(base_value * 0.7),
                    max_value=int(base_value * 1.5),
                    value=int(st.session_state.slider_valores[2]),
                    step=10,
                    format="R$ %d",
                    key="slider_mar"
                )
                
                st.session_state.slider_valores[3] = st.slider(
                    f"📅 {meses_label[3]}",
                    min_value=int(base_value * 0.7),
                    max_value=int(base_value * 1.5),
                    value=int(st.session_state.slider_valores[3]),
                    step=10,
                    format="R$ %d",
                    key="slider_abr"
                )
            
            with col_s3:
                st.session_state.slider_valores[4] = st.slider(
                    f"📅 {meses_label[4]}",
                    min_value=int(base_value * 0.7),
                    max_value=int(base_value * 1.5),
                    value=int(st.session_state.slider_valores[4]),
                    step=10,
                    format="R$ %d",
                    key="slider_mai"
                )
                
                st.session_state.slider_valores[5] = st.slider(
                    f"📅 {meses_label[5]}",
                    min_value=int(base_value * 0.7),
                    max_value=int(base_value * 1.5),
                    value=int(st.session_state.slider_valores[5]),
                    step=10,
                    format="R$ %d",
                    key="slider_jun"
                )
            
            # Resumo dos sliders
            st.markdown("**Valores dos Sliders:**")
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                st.metric("Média", f"R$ {np.mean(st.session_state.slider_valores):,.0f}")
            with col_r2:
                st.metric("Total", f"R$ {sum(st.session_state.slider_valores):,.0f}")
            with col_r3:
                var_slider = ((st.session_state.slider_valores[-1] - st.session_state.slider_valores[0]) / st.session_state.slider_valores[0]) * 100
                st.metric("Variação", f"{var_slider:.1f}%")


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
    """Aba para análise comparativa com gráfico interativo drag-and-drop"""
    st.markdown("#### 📊 Análise Comparativa - Drag-and-Drop Interativo")
    
    st.markdown("---")
    
    if BOKEH_EVENTS is None:
        st.warning("⚠️ streamlit-bokeh não disponível.")
        col_grafico, col_tabela = st.columns([1.5, 1], gap="large")
        
        with col_grafico:
            st.markdown("**Gráfico Interativo - Zoom, Pan e Análise**")
            
            meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun']
            y_realista = [1000, 1100, 1210, 1331, 1464, 1610]
            y_otimista = [1000, 1150, 1322, 1521, 1750, 2013]
            y_pessimista = [1000, 950, 902, 857, 814, 773]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=meses, y=y_realista, name='Realista', line=dict(color='#06b6d4', width=4), mode='lines+markers'))
            fig.add_trace(go.Scatter(x=meses, y=y_otimista, name='Otimista', line=dict(color='#10b981', width=2, dash='dash'), mode='lines+markers'))
            fig.add_trace(go.Scatter(x=meses, y=y_pessimista, name='Pessimista', line=dict(color='#ec4899', width=2, dash='dot'), mode='lines+markers'))
            fig.update_layout(title="Projeção", height=450)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_tabela:
            tabela_comp = {'Mês': meses, 'Realista': y_realista, 'Otimista': y_otimista, 'Pessimista': y_pessimista}
            st.dataframe(pd.DataFrame(tabela_comp), use_container_width=True, hide_index=True)
        return
    
    # ============== BOKEH DRAG-AND-DROP ==============
    
    meses_num = list(range(1, 7))
    meses_label = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun']
    
    # Inicializar
    if 'analise_realista' not in st.session_state:
        st.session_state.analise_realista = [1000, 1100, 1210, 1331, 1464, 1610]
        st.session_state.analise_otimista = [1000, 1150, 1322, 1521, 1750, 2013]
        st.session_state.analise_pessimista = [1000, 950, 902, 857, 814, 773]
    
    col_grafico, col_tabela = st.columns([1.6, 1.4], gap="large")
    
    with col_grafico:
        st.markdown("**👆 Arraste os Pontos Coloridos para Ajustar**")
        
        source_realista = ColumnDataSource(data=dict(x=meses_num, y=st.session_state.analise_realista))
        source_otimista = ColumnDataSource(data=dict(x=meses_num, y=st.session_state.analise_otimista))
        source_pessimista = ColumnDataSource(data=dict(x=meses_num, y=st.session_state.analise_pessimista))
        
        p = figure(title="Projeção - Arraste para Editar", x_axis_label="Mês", y_axis_label="R$",
                  width=900, height=480, toolbar_location="right", x_range=(0.5, 6.5),
                  y_range=(700, 2100))
        
        p.line('x', 'y', source=source_otimista, color="#10b981", line_width=3, legend_label='Otimista', alpha=0.8, line_dash='dashed')
        renderer_o = p.circle('x', 'y', source=source_otimista, size=14, color="#10b981", alpha=0.9, line_color='white', line_width=2)
        
        p.line('x', 'y', source=source_realista, color="#06b6d4", line_width=4, legend_label='Realista', alpha=0.9)
        renderer_r = p.circle('x', 'y', source=source_realista, size=16, color="#06b6d4", alpha=0.9, line_color='white', line_width=3)
        
        p.line('x', 'y', source=source_pessimista, color="#ef4444", line_width=3, legend_label='Pessimista', alpha=0.8, line_dash='dotted')
        renderer_p = p.circle('x', 'y', source=source_pessimista, size=14, color="#ef4444", alpha=0.9, line_color='white', line_width=2)
        
        tool_r = PointDrawTool(renderers=[renderer_r], empty_value='nan')
        tool_o = PointDrawTool(renderers=[renderer_o], empty_value='nan')
        tool_p = PointDrawTool(renderers=[renderer_p], empty_value='nan')
        
        p.add_tools(tool_r, tool_o, tool_p)
        p.toolbar.active_tap = tool_r
        p.legend.location = "top_left"
        p.background_fill_color = "#f0f9fc"
        p.outline_line_color = None
        p.grid.grid_line_alpha = 0.3
        
        btn_reset = Button(label="🔄 Resetar", button_type="warning", width=120)
        btn_reset.js_on_click(CustomJS(args=dict(
            r=source_realista, o=source_otimista, p=source_pessimista,
            vr=[1000, 1100, 1210, 1331, 1464, 1610], vo=[1000, 1150, 1322, 1521, 1750, 2013], vp=[1000, 950, 902, 857, 814, 773]
        ), code="""
            for (let i = 0; i < 6; i++) {
                r.data['y'][i] = vr[i];
                o.data['y'][i] = vo[i];
                p.data['y'][i] = vp[i];
            }
            r.change.emit(); o.change.emit(); p.change.emit();
        """))
        
        info = Div(text="""
        <div style="background:#dbeafe; padding:10px; border-radius:8px; border-left:4px solid #06b6d4;">
            <b>💡 Dicas:</b> • Arraste pontos <b style="color:#06b6d4;">●</b> <b style="color:#10b981;">●</b> <b style="color:#ef4444;">●</b><br>
            • Zoom com mouse • Tabela atualiza em tempo real!
        </div>
        """)
        
        layout = column(p, row(btn_reset, info, sizing_mode="stretch_width"), sizing_mode="stretch_width")
        
        if BOKEH_EVENTS:
            from streamlit_bokeh_events import streamlit_bokeh_events
            streamlit_bokeh_events(layout, events="tap,reset", key="analise_bokeh", refresh_on_update=False, debounce_time=0)
        else:
            from streamlit_bokeh import streamlit_bokeh
            streamlit_bokeh(layout, key="analise_bokeh")
    
    with col_tabela:
        st.markdown("**📋 Valores (Atualiza em Tempo Real)**")
        
        y_r = source_realista.data['y']
        y_o = source_otimista.data['y']
        y_p = source_pessimista.data['y']
        
        df = pd.DataFrame({
            'Mês': meses_label,
            'Realista': [f'R$ {v:,.0f}' for v in y_r],
            'Otimista': [f'R$ {v:,.0f}' for v in y_o],
            'Pessimista': [f'R$ {v:,.0f}' for v in y_p]
        })
        st.dataframe(df, use_container_width=True, hide_index=True, height=330)
        
        st.markdown("---")
        st.markdown("**📊 Estatísticas**")
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Var. Realista", f"{((y_r[-1]-y_r[0])/y_r[0]*100):.1f}%", delta=f"+R$ {(y_r[-1]-y_r[0]):,.0f}")
            st.metric("Var. Otimista", f"{((y_o[-1]-y_o[0])/y_o[0]*100):.1f}%", delta=f"+R$ {(y_o[-1]-y_o[0]):,.0f}")
        with c2:
            st.metric("Var. Pessimista", f"{((y_p[-1]-y_p[0])/y_p[0]*100):.1f}%", delta=f"{(y_p[-1]-y_p[0]):,.0f}")
            dif = y_o[-1] - y_p[-1]
            st.metric("Dif. O/P", f"R$ {dif:,.0f}", delta=f"{(dif/y_p[-1]*100):.1f}%")
        
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
