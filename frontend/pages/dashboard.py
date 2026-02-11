# frontend/pages/dashboard.py
"""
Dashboard Analítico Avançado
Página principal com KPIs, Curva ABC/Pareto, Heatmap, Treemap, Waterfall e mais
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_manager import get_dados_upload
from utils_ext.series import _norm_txt, _mes_to_num, _ensure_cli_n
from utils_ext.constants import MESES_ABR_LIST, CAT_COLORS

# ==============================
# Constantes e Configurações
# ==============================
CORES_DASHBOARD = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "success": "#2ca02c",
    "danger": "#d62728",
    "warning": "#ffbb33",
    "info": "#17a2b8",
    "light": "#f8f9fa",
    "dark": "#343a40",
    "gradient": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]
}

PARETO_COLORS = {
    "A": "#2ca02c",  # Verde - 80% do valor
    "B": "#ffbb33",  # Amarelo - 15% do valor
    "C": "#d62728"   # Vermelho - 5% do valor
}


# ==============================
# Funções Auxiliares
# ==============================
def _preparar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara e normaliza os dados para análise."""
    if df is None or df.empty:
        return pd.DataFrame()
    
    dff = df.copy()
    
    # Normalizar colunas
    if "MES_NUM" not in dff.columns and "MES" in dff.columns:
        dff["MES_NUM"] = dff["MES"].apply(_mes_to_num)
    
    if "ANO_NUM" not in dff.columns and "ANO" in dff.columns:
        dff["ANO_NUM"] = pd.to_numeric(dff["ANO"], errors="coerce").fillna(0).astype(int)
    
    # Garantir colunas numéricas
    for col in ["CURVA_REALIZADO", "PROJETADO_ANALITICO", "PROJETADO_MERCADO", "PROJETADO_AJUSTADO"]:
        if col in dff.columns:
            dff[col] = pd.to_numeric(dff[col], errors="coerce").fillna(0)
    
    return dff


def _formatar_valor(valor: float, prefixo: str = "R$") -> str:
    """Formata valores monetários brasileiros."""
    if abs(valor) >= 1e9:
        return f"{prefixo} {valor/1e9:.2f}B"
    elif abs(valor) >= 1e6:
        return f"{prefixo} {valor/1e6:.2f}M"
    elif abs(valor) >= 1e3:
        return f"{prefixo} {valor/1e3:.2f}K"
    else:
        return f"{prefixo} {valor:,.2f}"


def _calcular_variacao(atual: float, anterior: float) -> tuple:
    """Calcula variação percentual e retorna (valor, cor, seta)."""
    if anterior == 0:
        return (0, "gray", "→")
    var = ((atual - anterior) / anterior) * 100
    if var > 0:
        return (var, "#2ca02c", "↑")
    elif var < 0:
        return (var, "#d62728", "↓")
    else:
        return (0, "gray", "→")


# ==============================
# Componentes de KPI
# ==============================
def _render_kpi_card(titulo: str, valor: str, variacao: float = None, icon: str = "📊"):
    """Renderiza um card de KPI usando st.metric."""
    delta_val = None
    if variacao is not None and abs(variacao) > 0.01:
        delta_val = f"{variacao:.1f}%"
    st.metric(label=f"{icon} {titulo}", value=valor, delta=delta_val)


def _render_kpis_section(df: pd.DataFrame, ano_selecionado: int):
    """Renderiza seção de KPIs principais."""
    st.markdown("### 📊 Indicadores Chave de Performance")
    
    df_ano = df[df["ANO_NUM"] == ano_selecionado] if "ANO_NUM" in df.columns else df
    df_ano_ant = df[df["ANO_NUM"] == ano_selecionado - 1] if "ANO_NUM" in df.columns else pd.DataFrame()
    
    # Cálculos
    total_realizado = df_ano["CURVA_REALIZADO"].sum() if "CURVA_REALIZADO" in df_ano.columns else 0
    total_projetado = df_ano["PROJETADO_ANALITICO"].sum() if "PROJETADO_ANALITICO" in df_ano.columns else 0
    total_mercado = df_ano["PROJETADO_MERCADO"].sum() if "PROJETADO_MERCADO" in df_ano.columns else 0
    total_ajustado = df_ano["PROJETADO_AJUSTADO"].sum() if "PROJETADO_AJUSTADO" in df_ano.columns else 0
    
    # Variações
    real_ant = df_ano_ant["CURVA_REALIZADO"].sum() if not df_ano_ant.empty and "CURVA_REALIZADO" in df_ano_ant.columns else 0
    var_real, _, _ = _calcular_variacao(total_realizado, real_ant)
    
    proj_ant = df_ano_ant["PROJETADO_ANALITICO"].sum() if not df_ano_ant.empty and "PROJETADO_ANALITICO" in df_ano_ant.columns else 0
    var_proj, _, _ = _calcular_variacao(total_projetado, proj_ant)
    
    # Aderência (realizado vs projetado)
    aderencia = (total_realizado / total_projetado * 100) if total_projetado > 0 else 0
    
    # Número de produtos e categorias
    n_produtos = df_ano["PRODUTO"].nunique() if "PRODUTO" in df_ano.columns else 0
    n_categorias = df_ano["CATEGORIA"].nunique() if "CATEGORIA" in df_ano.columns else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        _render_kpi_card("Total Realizado", _formatar_valor(total_realizado), var_real, "💰")
    with col2:
        _render_kpi_card("Projeção Analítica", _formatar_valor(total_projetado), var_proj, "📈")
    with col3:
        _render_kpi_card("Aderência", f"{aderencia:.1f}%", None, "🎯")
    with col4:
        _render_kpi_card("Produtos Ativos", f"{n_produtos}", None, "📦")
    
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    
    col5, col6, col7, col8 = st.columns(4)
    
    gap_realizado_proj = total_realizado - total_projetado
    var_gap = (gap_realizado_proj / total_projetado * 100) if total_projetado > 0 else 0
    
    with col5:
        _render_kpi_card("Projeção Mercado", _formatar_valor(total_mercado), None, "🏪")
    with col6:
        _render_kpi_card("Projeção Ajustada", _formatar_valor(total_ajustado), None, "⚙️")
    with col7:
        gap_cor = var_gap if var_gap != 0 else None
        _render_kpi_card("Gap Real vs Proj", _formatar_valor(gap_realizado_proj), gap_cor, "📉")
    with col8:
        _render_kpi_card("Categorias", f"{n_categorias}", None, "📁")


# ==============================
# Curva ABC / Pareto
# ==============================
def _grafico_curva_abc_pareto(df: pd.DataFrame, coluna_valor: str = "CURVA_REALIZADO", 
                              agrupamento: str = "PRODUTO"):
    """
    Cria gráfico de Curva ABC (Pareto) mostrando concentração de valores.
    Classifica itens em A (80%), B (15%), C (5%) do valor total.
    """
    if df.empty or coluna_valor not in df.columns:
        return None
    
    # Agregar por agrupamento
    df_agg = df.groupby(agrupamento, as_index=False)[coluna_valor].sum()
    df_agg = df_agg[df_agg[coluna_valor] > 0].sort_values(coluna_valor, ascending=False)
    
    if df_agg.empty:
        return None
    
    # Calcular percentuais e acumulados
    total = df_agg[coluna_valor].sum()
    df_agg["Percentual"] = df_agg[coluna_valor] / total * 100
    df_agg["Acumulado"] = df_agg["Percentual"].cumsum()
    
    # Classificação ABC
    def classificar_abc(row):
        if row["Acumulado"] <= 80:
            return "A"
        elif row["Acumulado"] <= 95:
            return "B"
        else:
            return "C"
    
    df_agg["Classe"] = df_agg.apply(classificar_abc, axis=1)
    df_agg["Cor"] = df_agg["Classe"].map(PARETO_COLORS)
    
    # Top 15 para visualização
    df_plot = df_agg.head(15).copy()
    
    # Criar figura com eixo secundário
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Barras de valor
    fig.add_trace(
        go.Bar(
            x=df_plot[agrupamento],
            y=df_plot[coluna_valor],
            name="Valor",
            marker_color=df_plot["Cor"],
            text=df_plot["Classe"],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Valor: R$ %{y:,.0f}<br>Classe: %{text}<extra></extra>"
        ),
        secondary_y=False
    )
    
    # Linha de percentual acumulado
    fig.add_trace(
        go.Scatter(
            x=df_plot[agrupamento],
            y=df_plot["Acumulado"],
            name="% Acumulado",
            mode="lines+markers",
            line=dict(color="#1f77b4", width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>Acumulado: %{y:.1f}%<extra></extra>"
        ),
        secondary_y=True
    )
    
    # Linhas de referência ABC
    fig.add_hline(y=80, line_dash="dash", line_color="green", 
                  annotation_text="80% (Classe A)", secondary_y=True)
    fig.add_hline(y=95, line_dash="dash", line_color="orange", 
                  annotation_text="95% (Classe B)", secondary_y=True)
    
    fig.update_layout(
        title=dict(text=f"📊 Curva ABC (Pareto) - Top 15 {agrupamento}s", font=dict(size=16)),
        xaxis=dict(tickangle=-45, title=""),
        yaxis=dict(title="Valor (R$)", tickformat=",.0f"),
        yaxis2=dict(title="% Acumulado", range=[0, 105]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=450,
        template="plotly_white",
        margin=dict(t=80, b=100)
    )
    
    return fig


def _tabela_abc_resumo(df: pd.DataFrame, coluna_valor: str = "CURVA_REALIZADO", 
                       agrupamento: str = "PRODUTO"):
    """Cria resumo estatístico da classificação ABC."""
    if df.empty or coluna_valor not in df.columns:
        return None
    
    df_agg = df.groupby(agrupamento, as_index=False)[coluna_valor].sum()
    df_agg = df_agg[df_agg[coluna_valor] > 0].sort_values(coluna_valor, ascending=False)
    
    if df_agg.empty:
        return None
    
    total = df_agg[coluna_valor].sum()
    df_agg["Acumulado"] = (df_agg[coluna_valor].cumsum() / total * 100)
    
    def classificar(row):
        if row["Acumulado"] <= 80:
            return "A"
        elif row["Acumulado"] <= 95:
            return "B"
        else:
            return "C"
    
    df_agg["Classe"] = df_agg.apply(classificar, axis=1)
    
    # Resumo por classe
    resumo = df_agg.groupby("Classe").agg({
        agrupamento: "count",
        coluna_valor: "sum"
    }).rename(columns={agrupamento: "Qtd Itens", coluna_valor: "Valor Total"})
    
    resumo["% Itens"] = resumo["Qtd Itens"] / resumo["Qtd Itens"].sum() * 100
    resumo["% Valor"] = resumo["Valor Total"] / resumo["Valor Total"].sum() * 100
    
    return resumo.reset_index()


# ==============================
# Heatmap Mensal
# ==============================
def _grafico_heatmap_mensal(df: pd.DataFrame, coluna_valor: str = "CURVA_REALIZADO"):
    """Cria heatmap de valores por categoria e mês."""
    if df.empty or coluna_valor not in df.columns or "CATEGORIA" not in df.columns:
        return None
    
    # Agregar por categoria e mês
    df_heat = df.groupby(["CATEGORIA", "MES_NUM"], as_index=False)[coluna_valor].sum()
    
    # Pivot para formato de matriz
    df_pivot = df_heat.pivot(index="CATEGORIA", columns="MES_NUM", values=coluna_valor).fillna(0)
    
    # Renomear colunas para meses
    meses_map = {i: MESES_ABR_LIST[i-1] if i <= len(MESES_ABR_LIST) else str(i) for i in range(1, 13)}
    df_pivot.columns = [meses_map.get(c, c) for c in df_pivot.columns]
    
    fig = px.imshow(
        df_pivot,
        labels=dict(x="Mês", y="Categoria", color="Valor"),
        aspect="auto",
        color_continuous_scale="Blues",
        title="🗓️ Heatmap de Valores por Categoria e Mês"
    )
    
    fig.update_layout(
        height=400,
        template="plotly_white",
        coloraxis_colorbar=dict(title="Valor (R$)", tickformat=",.0f"),
        xaxis=dict(side="bottom"),
        margin=dict(t=60)
    )
    
    # Adicionar valores no heatmap
    fig.update_traces(
        text=[[f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}K" for v in row] 
              for row in df_pivot.values],
        texttemplate="%{text}",
        textfont={"size": 10}
    )
    
    return fig


# ==============================
# Treemap de Categorias
# ==============================
def _grafico_treemap_categorias(df: pd.DataFrame, coluna_valor: str = "CURVA_REALIZADO"):
    """Cria treemap hierárquico de categorias e produtos."""
    if df.empty or coluna_valor not in df.columns:
        return None
    
    # Agregar por categoria e produto
    df_tree = df.groupby(["CATEGORIA", "PRODUTO"], as_index=False)[coluna_valor].sum()
    df_tree = df_tree[df_tree[coluna_valor] > 0]
    
    if df_tree.empty:
        return None
    
    fig = px.treemap(
        df_tree,
        path=["CATEGORIA", "PRODUTO"],
        values=coluna_valor,
        color=coluna_valor,
        color_continuous_scale="Viridis",
        title="🌳 Treemap - Distribuição por Categoria e Produto"
    )
    
    fig.update_layout(
        height=500,
        margin=dict(t=60, l=10, r=10, b=10)
    )
    
    fig.update_traces(
        textinfo="label+percent parent",
        hovertemplate="<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent:.1%} da categoria<extra></extra>"
    )
    
    return fig


# ==============================
# Gráfico Waterfall
# ==============================
def _grafico_waterfall_variacao(df: pd.DataFrame, ano_atual: int):
    """Cria gráfico waterfall mostrando variação entre anos por categoria."""
    if df.empty or "CATEGORIA" not in df.columns or "ANO_NUM" not in df.columns:
        return None
    
    ano_anterior = ano_atual - 1
    
    # Calcular totais por categoria e ano
    df_atual = df[df["ANO_NUM"] == ano_atual].groupby("CATEGORIA")["CURVA_REALIZADO"].sum()
    df_anterior = df[df["ANO_NUM"] == ano_anterior].groupby("CATEGORIA")["CURVA_REALIZADO"].sum()
    
    # Calcular variações
    categorias = list(set(df_atual.index) | set(df_anterior.index))
    variacoes = []
    
    for cat in categorias:
        atual = df_atual.get(cat, 0)
        anterior = df_anterior.get(cat, 0)
        variacoes.append({
            "Categoria": cat,
            "Variação": atual - anterior
        })
    
    df_var = pd.DataFrame(variacoes).sort_values("Variação", ascending=False)
    
    if df_var.empty:
        return None
    
    # Criar waterfall
    fig = go.Figure(go.Waterfall(
        name="Variação",
        orientation="v",
        measure=["relative"] * len(df_var),
        x=df_var["Categoria"],
        y=df_var["Variação"],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#2ca02c"}},
        decreasing={"marker": {"color": "#d62728"}},
        text=[f"{v/1e6:+.1f}M" if abs(v) >= 1e6 else f"{v/1e3:+.0f}K" for v in df_var["Variação"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Variação: R$ %{y:,.0f}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(text=f"📊 Variação por Categoria ({ano_anterior} → {ano_atual})", font=dict(size=16)),
        yaxis=dict(title="Variação (R$)", tickformat=",.0f"),
        xaxis=dict(tickangle=-45, title=""),
        height=400,
        template="plotly_white",
        showlegend=False,
        margin=dict(t=80, b=100)
    )
    
    return fig


# ==============================
# Gráfico de Gauge (Velocímetro)
# ==============================
def _grafico_gauge_aderencia(realizado: float, projetado: float, titulo: str = "Aderência"):
    """Cria gráfico de gauge/velocímetro mostrando aderência."""
    if projetado == 0:
        aderencia = 0
    else:
        aderencia = (realizado / projetado) * 100
    
    # Determinar cor baseado na aderência
    if aderencia >= 100:
        cor = "#2ca02c"  # Verde
    elif aderencia >= 80:
        cor = "#ffbb33"  # Amarelo
    else:
        cor = "#d62728"  # Vermelho
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=aderencia,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": titulo, "font": {"size": 16}},
        delta={"reference": 100, "increasing": {"color": "#2ca02c"}, "decreasing": {"color": "#d62728"}},
        number={"suffix": "%", "font": {"size": 32}},
        gauge={
            "axis": {"range": [0, 120], "tickwidth": 1, "tickcolor": "darkgray"},
            "bar": {"color": cor},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "gray",
            "steps": [
                {"range": [0, 60], "color": "rgba(214, 39, 40, 0.2)"},
                {"range": [60, 80], "color": "rgba(255, 187, 51, 0.2)"},
                {"range": [80, 100], "color": "rgba(44, 160, 44, 0.2)"},
                {"range": [100, 120], "color": "rgba(31, 119, 180, 0.2)"}
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": 100
            }
        }
    ))
    
    fig.update_layout(
        height=280,
        margin=dict(t=60, b=20, l=30, r=30)
    )
    
    return fig


# ==============================
# Gráfico de Tendência (Sparklines)
# ==============================
def _grafico_evolucao_mensal(df: pd.DataFrame, ano: int):
    """Cria gráfico de linha mostrando evolução mensal de todas as métricas."""
    if df.empty or "MES_NUM" not in df.columns:
        return None
    
    df_ano = df[df["ANO_NUM"] == ano] if "ANO_NUM" in df.columns else df
    
    # Agregar por mês
    colunas = ["CURVA_REALIZADO", "PROJETADO_ANALITICO", "PROJETADO_MERCADO", "PROJETADO_AJUSTADO"]
    colunas_presentes = [c for c in colunas if c in df_ano.columns]
    
    if not colunas_presentes:
        return None
    
    df_mensal = df_ano.groupby("MES_NUM", as_index=False)[colunas_presentes].sum()
    df_mensal = df_mensal.sort_values("MES_NUM")
    
    # Mapear meses
    df_mensal["Mês"] = df_mensal["MES_NUM"].map(
        lambda x: MESES_ABR_LIST[int(x)-1] if 1 <= x <= 12 else str(x)
    )
    
    fig = go.Figure()
    
    cores = {
        "CURVA_REALIZADO": "#1f77b4",
        "PROJETADO_ANALITICO": "#ff7f0e",
        "PROJETADO_MERCADO": "#2ca02c",
        "PROJETADO_AJUSTADO": "#9467bd"
    }
    
    nomes = {
        "CURVA_REALIZADO": "Realizado",
        "PROJETADO_ANALITICO": "Proj. Analítica",
        "PROJETADO_MERCADO": "Proj. Mercado",
        "PROJETADO_AJUSTADO": "Proj. Ajustada"
    }
    
    for col in colunas_presentes:
        fig.add_trace(go.Scatter(
            x=df_mensal["Mês"],
            y=df_mensal[col],
            name=nomes.get(col, col),
            mode="lines+markers",
            line=dict(color=cores.get(col, "#333"), width=2),
            marker=dict(size=8),
            hovertemplate=f"<b>{nomes.get(col, col)}</b><br>Mês: %{{x}}<br>Valor: R$ %{{y:,.0f}}<extra></extra>"
        ))
    
    fig.update_layout(
        title=dict(text=f"📈 Evolução Mensal - {ano}", font=dict(size=16)),
        xaxis=dict(title=""),
        yaxis=dict(title="Valor (R$)", tickformat=",.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=380,
        template="plotly_white",
        hovermode="x unified",
        margin=dict(t=80)
    )
    
    return fig


# ==============================
# Gráfico de Barras Comparativo
# ==============================
def _grafico_barras_comparativo_categorias(df: pd.DataFrame, ano: int):
    """Cria gráfico de barras comparando métricas por categoria."""
    if df.empty or "CATEGORIA" not in df.columns:
        return None
    
    df_ano = df[df["ANO_NUM"] == ano] if "ANO_NUM" in df.columns else df
    
    # Agregar por categoria
    colunas = ["CURVA_REALIZADO", "PROJETADO_ANALITICO", "PROJETADO_MERCADO"]
    colunas_presentes = [c for c in colunas if c in df_ano.columns]
    
    if not colunas_presentes:
        return None
    
    df_cat = df_ano.groupby("CATEGORIA", as_index=False)[colunas_presentes].sum()
    df_cat = df_cat.sort_values(colunas_presentes[0], ascending=False).head(10)
    
    fig = go.Figure()
    
    cores = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    nomes = {
        "CURVA_REALIZADO": "Realizado",
        "PROJETADO_ANALITICO": "Proj. Analítica",
        "PROJETADO_MERCADO": "Proj. Mercado"
    }
    
    for i, col in enumerate(colunas_presentes):
        fig.add_trace(go.Bar(
            name=nomes.get(col, col),
            x=df_cat["CATEGORIA"],
            y=df_cat[col],
            marker_color=cores[i],
            hovertemplate=f"<b>{nomes.get(col, col)}</b><br>%{{x}}<br>Valor: R$ %{{y:,.0f}}<extra></extra>"
        ))
    
    fig.update_layout(
        title=dict(text=f"📊 Comparativo por Categoria (Top 10) - {ano}", font=dict(size=16)),
        barmode="group",
        xaxis=dict(tickangle=-45, title=""),
        yaxis=dict(title="Valor (R$)", tickformat=",.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420,
        template="plotly_white",
        margin=dict(t=80, b=100)
    )
    
    return fig


# ==============================
# Gráfico Sunburst
# ==============================
def _grafico_sunburst(df: pd.DataFrame, coluna_valor: str = "CURVA_REALIZADO"):
    """Cria gráfico sunburst hierárquico."""
    if df.empty or coluna_valor not in df.columns:
        return None
    
    # Verificar colunas necessárias
    colunas_hier = []
    if "TIPO_CLIENTE" in df.columns or "TP_CLIENTE" in df.columns:
        col_cliente = "TIPO_CLIENTE" if "TIPO_CLIENTE" in df.columns else "TP_CLIENTE"
        colunas_hier.append(col_cliente)
    if "CATEGORIA" in df.columns:
        colunas_hier.append("CATEGORIA")
    
    if len(colunas_hier) < 1:
        return None
    
    # Agregar dados
    df_sun = df.groupby(colunas_hier, as_index=False)[coluna_valor].sum()
    df_sun = df_sun[df_sun[coluna_valor] > 0]
    
    if df_sun.empty:
        return None
    
    fig = px.sunburst(
        df_sun,
        path=colunas_hier,
        values=coluna_valor,
        color=coluna_valor,
        color_continuous_scale="Blues",
        title="☀️ Sunburst - Distribuição Hierárquica"
    )
    
    fig.update_layout(
        height=500,
        margin=dict(t=60, l=10, r=10, b=10)
    )
    
    return fig


# ==============================
# Análise de Concentração
# ==============================
def _grafico_concentracao(df: pd.DataFrame, coluna_valor: str = "CURVA_REALIZADO"):
    """Cria gráfico de análise de concentração (Lorenz/Gini)."""
    if df.empty or coluna_valor not in df.columns or "PRODUTO" not in df.columns:
        return None
    
    # Agregar por produto
    df_prod = df.groupby("PRODUTO", as_index=False)[coluna_valor].sum()
    df_prod = df_prod[df_prod[coluna_valor] > 0].sort_values(coluna_valor)
    
    if len(df_prod) < 2:
        return None
    
    # Calcular curva de Lorenz
    valores = df_prod[coluna_valor].values
    n = len(valores)
    
    # Percentuais acumulados
    pop_pct = np.arange(1, n + 1) / n * 100
    valor_pct = np.cumsum(valores) / valores.sum() * 100
    
    # Calcular coeficiente de Gini
    area_sob_lorenz = np.trapz(valor_pct, pop_pct) / 100
    area_igualdade = 50  # área sob a linha de igualdade perfeita (triângulo)
    gini = (area_igualdade - area_sob_lorenz) / area_igualdade
    
    fig = go.Figure()
    
    # Linha de igualdade perfeita
    fig.add_trace(go.Scatter(
        x=[0, 100],
        y=[0, 100],
        mode="lines",
        name="Igualdade Perfeita",
        line=dict(color="gray", dash="dash", width=2),
        hoverinfo="skip"
    ))
    
    # Curva de Lorenz
    fig.add_trace(go.Scatter(
        x=np.insert(pop_pct, 0, 0),
        y=np.insert(valor_pct, 0, 0),
        mode="lines",
        name=f"Curva de Lorenz (Gini={gini:.3f})",
        line=dict(color="#1f77b4", width=3),
        fill="tozeroy",
        fillcolor="rgba(31, 119, 180, 0.2)",
        hovertemplate="%{x:.1f}% dos produtos<br>%{y:.1f}% do valor<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(text=f"📐 Análise de Concentração (Gini = {gini:.3f})", font=dict(size=16)),
        xaxis=dict(title="% Acumulado de Produtos", range=[0, 100]),
        yaxis=dict(title="% Acumulado de Valor", range=[0, 100]),
        height=400,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=80)
    )
    
    return fig


# ==============================
# Box Plot de Distribuição
# ==============================
def _grafico_boxplot_categorias(df: pd.DataFrame, coluna_valor: str = "CURVA_REALIZADO"):
    """Cria box plot mostrando distribuição de valores por categoria."""
    if df.empty or coluna_valor not in df.columns or "CATEGORIA" not in df.columns:
        return None
    
    # Filtrar valores positivos e top categorias
    df_box = df[df[coluna_valor] > 0].copy()
    
    top_cats = df_box.groupby("CATEGORIA")[coluna_valor].sum().nlargest(8).index.tolist()
    df_box = df_box[df_box["CATEGORIA"].isin(top_cats)]
    
    if df_box.empty:
        return None
    
    fig = px.box(
        df_box,
        x="CATEGORIA",
        y=coluna_valor,
        color="CATEGORIA",
        title="📦 Distribuição de Valores por Categoria (Top 8)",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig.update_layout(
        xaxis=dict(tickangle=-45, title=""),
        yaxis=dict(title="Valor (R$)", tickformat=",.0f"),
        height=400,
        template="plotly_white",
        showlegend=False,
        margin=dict(t=60, b=100)
    )
    
    return fig


# ==============================
# Radar Chart
# ==============================
def _grafico_radar_categorias(df: pd.DataFrame, ano: int):
    """Cria gráfico radar comparando métricas normalizadas por categoria."""
    if df.empty or "CATEGORIA" not in df.columns:
        return None
    
    df_ano = df[df["ANO_NUM"] == ano] if "ANO_NUM" in df.columns else df
    
    # Verificar se temos a coluna CURVA_REALIZADO
    if "CURVA_REALIZADO" not in df_ano.columns:
        return None
    
    # Top 6 categorias para radar legível
    try:
        top_cats = df_ano.groupby("CATEGORIA")["CURVA_REALIZADO"].sum().nlargest(6).index.tolist()
    except Exception:
        return None
    
    if not top_cats:
        return None
    
    df_radar = df_ano[df_ano["CATEGORIA"].isin(top_cats)].copy()
    
    if df_radar.empty:
        return None
    
    # Agregar por categoria
    colunas = ["CURVA_REALIZADO", "PROJETADO_ANALITICO", "PROJETADO_MERCADO"]
    colunas_presentes = [c for c in colunas if c in df_radar.columns]
    
    if len(colunas_presentes) < 2:
        return None
    
    df_cat = df_radar.groupby("CATEGORIA", as_index=False)[colunas_presentes].sum()
    
    if df_cat.empty:
        return None
    
    # Normalizar valores (0-100)
    for col in colunas_presentes:
        max_val = df_cat[col].max()
        if max_val > 0:
            df_cat[col] = df_cat[col] / max_val * 100
        else:
            df_cat[col] = 0
    
    fig = go.Figure()
    
    cores = px.colors.qualitative.Set2
    
    nomes_metricas = []
    for col in colunas_presentes:
        if col == "CURVA_REALIZADO":
            nomes_metricas.append("Realizado")
        elif col == "PROJETADO_ANALITICO":
            nomes_metricas.append("Proj. Analítica")
        elif col == "PROJETADO_MERCADO":
            nomes_metricas.append("Proj. Mercado")
        else:
            nomes_metricas.append(col)
    
    # Fechar o polígono
    nomes_metricas_fechado = nomes_metricas + [nomes_metricas[0]]
    
    for i, idx in enumerate(df_cat.index):
        row = df_cat.loc[idx]
        categoria = row["CATEGORIA"]
        
        valores = []
        for col in colunas_presentes:
            valores.append(float(row[col]))
        valores.append(valores[0])  # Fechar polígono
        
        fig.add_trace(go.Scatterpolar(
            r=valores,
            theta=nomes_metricas_fechado,
            fill="toself",
            name=str(categoria),
            line=dict(color=cores[i % len(cores)]),
            opacity=0.7
        ))
    
    fig.update_layout(
        title=dict(text=f"🎯 Radar - Top 6 Categorias - {ano}", font=dict(size=16)),
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100])
        ),
        height=450,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=80, b=80)
    )
    
    return fig


# ==============================
# Função Principal de Renderização
# ==============================
def renderizar():
    """Renderiza o dashboard completo."""
    
    st.markdown("""
    <style>
        .main > div { padding-top: 1rem; }
        div[data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
        h1 { margin-bottom: 1rem !important; }
        h2 { margin: 1rem 0 0.5rem 0 !important; font-size: 1.4rem !important; }
        h3 { margin: 0.75rem 0 0.5rem 0 !important; font-size: 1.2rem !important; }
        .stPlotlyChart { margin-bottom: 1rem; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("# 📊 Dashboard Analítico")
    
    # Carregar dados
    df_upload = get_dados_upload()
    
    if df_upload is None or df_upload.empty:
        st.warning("⚠️ Nenhum dado carregado. Vá em **Upload** e importe o arquivo Excel.")
        
        # Mostrar dashboard de exemplo/demo
        st.info("📌 **Dica:** Após carregar os dados, você terá acesso a:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            **📈 Análises de Performance**
            - KPIs Principais
            - Evolução Mensal
            - Comparativos
            """)
        with col2:
            st.markdown("""
            **📊 Análises Avançadas**
            - Curva ABC/Pareto
            - Análise de Concentração
            - Heatmaps
            """)
        with col3:
            st.markdown("""
            **🎯 Visualizações**
            - Treemap Hierárquico
            - Gráficos Radar
            - Gauges de Aderência
            """)
        return
    
    # Preparar dados
    df = _preparar_dados(df_upload)
    
    if df.empty:
        st.error("Erro ao processar os dados.")
        return
    
    # ==================== FILTROS ====================
    st.markdown("---")
    
    col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns([1.5, 1.5, 1.5, 1])
    
    with col_filtro1:
        anos_disponiveis = sorted(df["ANO_NUM"].dropna().unique().astype(int).tolist(), reverse=True)
        if not anos_disponiveis:
            anos_disponiveis = [2024]
        ano_selecionado = st.selectbox("📅 Ano", anos_disponiveis, index=0, key="dash_ano")
    
    with col_filtro2:
        categorias = ["Todas"] + sorted(df["CATEGORIA"].dropna().astype(str).unique().tolist())
        categoria_selecionada = st.selectbox("📁 Categoria", categorias, index=0, key="dash_categoria")
    
    with col_filtro3:
        metricas = {
            "Realizado": "CURVA_REALIZADO",
            "Proj. Analítica": "PROJETADO_ANALITICO",
            "Proj. Mercado": "PROJETADO_MERCADO",
            "Proj. Ajustada": "PROJETADO_AJUSTADO"
        }
        metrica_nome = st.selectbox("📊 Métrica Principal", list(metricas.keys()), index=0, key="dash_metrica")
        metrica_selecionada = metricas[metrica_nome]
    
    with col_filtro4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        atualizar = st.button("🔄 Atualizar", use_container_width=True)
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if categoria_selecionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado["CATEGORIA"] == categoria_selecionada]
    
    st.markdown("---")
    
    # ==================== KPIs ====================
    _render_kpis_section(df_filtrado, ano_selecionado)
    
    st.markdown("---")
    
    # ==================== Gauges de Aderência ====================
    st.markdown("### 🎯 Aderência por Tipo de Projeção")
    
    df_ano = df_filtrado[df_filtrado["ANO_NUM"] == ano_selecionado]
    total_real = df_ano["CURVA_REALIZADO"].sum() if "CURVA_REALIZADO" in df_ano.columns else 0
    total_ana = df_ano["PROJETADO_ANALITICO"].sum() if "PROJETADO_ANALITICO" in df_ano.columns else 0
    total_mer = df_ano["PROJETADO_MERCADO"].sum() if "PROJETADO_MERCADO" in df_ano.columns else 0
    total_ajust = df_ano["PROJETADO_AJUSTADO"].sum() if "PROJETADO_AJUSTADO" in df_ano.columns else 0
    
    col_g1, col_g2, col_g3 = st.columns(3)
    
    with col_g1:
        fig_gauge1 = _grafico_gauge_aderencia(total_real, total_ana, "Real vs Analítica")
        if fig_gauge1:
            st.plotly_chart(fig_gauge1, use_container_width=True)
    
    with col_g2:
        fig_gauge2 = _grafico_gauge_aderencia(total_real, total_mer, "Real vs Mercado")
        if fig_gauge2:
            st.plotly_chart(fig_gauge2, use_container_width=True)
    
    with col_g3:
        fig_gauge3 = _grafico_gauge_aderencia(total_real, total_ajust, "Real vs Ajustada")
        if fig_gauge3:
            st.plotly_chart(fig_gauge3, use_container_width=True)
    
    st.markdown("---")
    
    # ==================== Evolução Mensal ====================
    st.markdown("### 📈 Evolução Mensal")
    
    fig_evolucao = _grafico_evolucao_mensal(df_filtrado, ano_selecionado)
    if fig_evolucao:
        st.plotly_chart(fig_evolucao, use_container_width=True)
    
    st.markdown("---")
    
    # ==================== Curva ABC / Pareto ====================
    st.markdown("### 📊 Análise de Curva ABC (Pareto)")
    
    col_abc1, col_abc2 = st.columns([2, 1])
    
    with col_abc1:
        fig_pareto = _grafico_curva_abc_pareto(df_ano, metrica_selecionada, "PRODUTO")
        if fig_pareto:
            st.plotly_chart(fig_pareto, use_container_width=True)
    
    with col_abc2:
        st.markdown("#### Resumo ABC")
        resumo_abc = _tabela_abc_resumo(df_ano, metrica_selecionada, "PRODUTO")
        if resumo_abc is not None:
            st.markdown("""
            <style>
                .abc-table { font-size: 14px; }
                .abc-a { background-color: rgba(44, 160, 44, 0.2); }
                .abc-b { background-color: rgba(255, 187, 51, 0.2); }
                .abc-c { background-color: rgba(214, 39, 40, 0.2); }
            </style>
            """, unsafe_allow_html=True)
            
            for _, row in resumo_abc.iterrows():
                classe = row["Classe"]
                cor_bg = PARETO_COLORS.get(classe, "#gray")
                st.markdown(f"""
                <div style="
                    background: linear-gradient(90deg, {cor_bg}33, transparent);
                    padding: 12px;
                    border-radius: 8px;
                    margin-bottom: 8px;
                    border-left: 4px solid {cor_bg};
                ">
                    <div style="font-weight:700; font-size:18px;">Classe {classe}</div>
                    <div style="display:flex; justify-content:space-between; margin-top:8px;">
                        <div><b>{int(row['Qtd Itens'])}</b> itens ({row['% Itens']:.1f}%)</div>
                        <div><b>{_formatar_valor(row['Valor Total'])}</b> ({row['% Valor']:.1f}%)</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ==================== Heatmap e Treemap ====================
    st.markdown("### 🗺️ Análises Visuais")
    
    col_vis1, col_vis2 = st.columns(2)
    
    with col_vis1:
        fig_heatmap = _grafico_heatmap_mensal(df_ano, metrica_selecionada)
        if fig_heatmap:
            st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with col_vis2:
        fig_treemap = _grafico_treemap_categorias(df_ano, metrica_selecionada)
        if fig_treemap:
            st.plotly_chart(fig_treemap, use_container_width=True)
    
    st.markdown("---")
    
    # ==================== Comparativo e Waterfall ====================
    st.markdown("### 📊 Análises Comparativas")
    
    col_comp1, col_comp2 = st.columns(2)
    
    with col_comp1:
        fig_barras = _grafico_barras_comparativo_categorias(df_filtrado, ano_selecionado)
        if fig_barras:
            st.plotly_chart(fig_barras, use_container_width=True)
    
    with col_comp2:
        fig_waterfall = _grafico_waterfall_variacao(df_filtrado, ano_selecionado)
        if fig_waterfall:
            st.plotly_chart(fig_waterfall, use_container_width=True)
        else:
            st.info("📊 Gráfico Waterfall requer dados de anos anteriores para comparação.")
    
    st.markdown("---")
    
    # ==================== Concentração e Radar ====================
    st.markdown("### 🎯 Análises Avançadas")
    
    col_adv1, col_adv2 = st.columns(2)
    
    with col_adv1:
        fig_concentracao = _grafico_concentracao(df_ano, metrica_selecionada)
        if fig_concentracao:
            st.plotly_chart(fig_concentracao, use_container_width=True)
    
    with col_adv2:
        fig_radar = _grafico_radar_categorias(df_filtrado, ano_selecionado)
        if fig_radar:
            st.plotly_chart(fig_radar, use_container_width=True)
    
    st.markdown("---")
    
    # ==================== Sunburst e BoxPlot ====================
    st.markdown("### 📈 Distribuições")
    
    col_dist1, col_dist2 = st.columns(2)
    
    with col_dist1:
        fig_sunburst = _grafico_sunburst(df_ano, metrica_selecionada)
        if fig_sunburst:
            st.plotly_chart(fig_sunburst, use_container_width=True)
    
    with col_dist2:
        fig_boxplot = _grafico_boxplot_categorias(df_ano, metrica_selecionada)
        if fig_boxplot:
            st.plotly_chart(fig_boxplot, use_container_width=True)
    
    st.markdown("---")
    
    # ==================== Rodapé ====================
    st.markdown("""
    <div style="
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 12px;
    ">
        📊 Dashboard Analítico | Última atualização: {data}
    </div>
    """.format(data=pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)
