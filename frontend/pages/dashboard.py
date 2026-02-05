# frontend/pages/dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# === PATH raiz do projeto (para importar helpers) ===
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_manager import get_dados_upload, get_metricas_dashboard

# =========================
# Helpers e constantes
# =========================
MESES_ABREV = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
MESES_FULL_UPPER = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
                    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]

PLOTLY_CONFIG = {
    "displaylogo": False,
    "scrollZoom": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines"]
}

def _safe_to_datetime(series: pd.Series) -> pd.Series:
    """
    Converte datas com formatos possivelmente mistos sem gerar warnings.
    Usa dayfirst=True e errors='coerce' (sem format rígido).
    """
    try:
        return pd.to_datetime(series, errors="coerce", dayfirst=True)
    except Exception:
        return pd.to_datetime(series, errors="coerce", dayfirst=True)

def _ensure_numeric(s: pd.Series) -> pd.Series:
    """Garante série numérica float, convertendo strings problemáticas para NaN->0.0."""
    return pd.to_numeric(s, errors="coerce").fillna(0.0).astype(float)

def _mes_from_df(df: pd.DataFrame) -> pd.Series:
    """
    Obtém mês numérico com prioridade:
    1) coluna sanitizada MES_NUM (1..12) vinda do Upload
    2) derivado de DATA_COMPLETA (fallback)
    """
    if "MES_NUM" in df.columns:
        return pd.to_numeric(df["MES_NUM"], errors="coerce").astype("Int64")
    if "DATA_COMPLETA" in df.columns:
        return _safe_to_datetime(df["DATA_COMPLETA"]).dt.month.astype("Int64")
    return pd.Series([pd.NA] * len(df), index=df.index, dtype="Int64")

def _ano_from_df(df: pd.DataFrame) -> pd.Series:
    """
    Obtém ano numérico com prioridade:
    1) coluna sanitizada ANO_NUM vinda do Upload
    2) derivado de ANO
    3) derivado de DATA_COMPLETA
    """
    if "ANO_NUM" in df.columns:
        return pd.to_numeric(df["ANO_NUM"], errors="coerce").astype("Int64")
    if "ANO" in df.columns:
        s = pd.to_numeric(df["ANO"], errors="coerce").astype("Int64")
        if s.notna().any():
            return s
    if "DATA_COMPLETA" in df.columns:
        return _safe_to_datetime(df["DATA_COMPLETA"]).dt.year.astype("Int64")
    return pd.Series([pd.NA] * len(df), index=df.index, dtype="Int64")

def renderizar():
    st.markdown("# 📈 Dashboard de Análises")
    st.markdown("**Visão geral de análise dos dados e projeções**")
    st.markdown("---")

    # ============= Carregar base e métricas =============
    df_upload = get_dados_upload()
    metricas = get_metricas_dashboard() or {}

    # ================= KPIs =================
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        valor_total = metricas.get("valor_total", 2_480_000)
        st.metric(
            label="Valor Total Projetado",
            value=f"R$ {valor_total/1_000_000:.2f}M" if valor_total > 0 else "R$ 2,48M",
            delta="+12,5%"
        )

    with col2:
        realizado_kpi = metricas.get("realizado_atual", 1_850_000)
        st.metric(
            label="Realizado Atual",
            value=f"R$ {realizado_kpi/1_000_000:.2f}M" if realizado_kpi > 0 else "R$ 1,85M",
            delta="+8,3%"
        )

    with col3:
        acuracia = metricas.get("taxa_acuracia", 87.2)
        st.metric(
            label="Taxa de Acurácia",
            value=f"{acuracia:.1f}%" if acuracia > 0 else "87,2%",
            delta="+2,1%"
        )

    with col4:
        sim_ativas = metricas.get("simulacoes_ativas", 156)
        st.metric(
            label="Simulações Ativas",
            value=str(sim_ativas) if sim_ativas > 0 else "156",
            delta="+24"
        )

    st.markdown("---")

    col_chart1, col_chart2 = st.columns(2)

    # ================= Gráfico 1: Evolução =================
    with col_chart1:
        st.markdown("#### 📈 Evolução de Valores")

        # Mock de série diária (pode trocar pelo seu dado real quando tiver)
        np.random.seed(42)
        dias = pd.date_range("2025-08-01", periods=60, freq="D")
        valores_realizados = 1_000_000 + np.cumsum(np.random.randn(60) * 5_000)
        valores_projetados = valores_realizados * 1.2

        fig_evolucao = go.Figure()
        fig_evolucao.add_trace(go.Scatter(
            x=dias, y=valores_realizados,
            name="Realizado",
            line=dict(color="#06b6d4", width=3),
            fill="tozeroy",
            fillcolor="rgba(6, 182, 212, 0.2)"
        ))
        fig_evolucao.add_trace(go.Scatter(
            x=dias, y=valores_projetados,
            name="Projetado",
            line=dict(color="#0c3a66", width=3, dash="dash"),
            fill="tonexty",
            fillcolor="rgba(12, 58, 102, 0.1)"
        ))
        fig_evolucao.update_layout(
            hovermode="x unified",
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor="rgba(240, 249, 252, 0.5)",
            paper_bgcolor="rgba(255, 255, 255, 0)"
        )
        st.plotly_chart(fig_evolucao, use_container_width=True, config=PLOTLY_CONFIG)

    # ================= Gráfico 2: Distribuição por Categoria =================
    with col_chart2:
        st.markdown("#### 💹 Distribuição por Categoria")

        if df_upload is not None and "CATEGORIA" in df_upload.columns:
            dfc = df_upload.copy()
            # Garante numérico
            if "PROJETADO_AJUSTADO" in dfc.columns:
                dfc["PROJETADO_AJUSTADO"] = _ensure_numeric(dfc["PROJETADO_AJUSTADO"])
            else:
                dfc["PROJETADO_AJUSTADO"] = 0.0
            categoria_sum = dfc.groupby("CATEGORIA")["PROJETADO_AJUSTADO"].sum().sort_values(ascending=False)
        else:
            categoria_sum = pd.Series({
                "Crédito PF": 850000.0,
                "Crédito PJ": 920000.0,
                "Investimentos": 710000.0
            })

        cores = ["#06b6d4", "#0c3a66", "#ec4899", "#10b981", "#f59e0b"]

        fig_dist = go.Figure(data=[go.Pie(
            labels=categoria_sum.index,
            values=categoria_sum.values,
            marker=dict(colors=cores[:len(categoria_sum)]),
            hole=0.4,
            textposition="inside",
            textinfo="label+percent"
        )])
        fig_dist.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(255, 255, 255, 0)"
        )
        st.plotly_chart(fig_dist, use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("---")

    col_chart3, col_chart4 = st.columns(2)

    # ================= Gráfico 3: Realizado vs Projetado (por mês) =================
    with col_chart3:
        st.markdown("#### 📊 Comparação Realizado vs Projetado")

        if df_upload is not None and {"CURVA_REALIZADO", "PROJETADO_ANALITICO"}.issubset(df_upload.columns):
            dfc = df_upload.copy()
            dfc["MES_NUM"] = _mes_from_df(dfc)
            # Mantém somente meses válidos 1..12
            dfc = dfc[dfc["MES_NUM"].between(1, 12)]
            dfc["CURVA_REALIZADO"] = _ensure_numeric(dfc["CURVA_REALIZADO"])
            dfc["PROJETADO_ANALITICO"] = _ensure_numeric(dfc["PROJETADO_ANALITICO"])

            mes_data = dfc.groupby("MES_NUM").agg({
                "CURVA_REALIZADO": "sum",
                "PROJETADO_ANALITICO": "sum"
            }).reset_index().sort_values("MES_NUM")

            meses = [MESES_ABREV[m-1] for m in mes_data["MES_NUM"]]
            realizado = mes_data["CURVA_REALIZADO"].tolist()
            projetado = mes_data["PROJETADO_ANALITICO"].tolist()
        else:
            meses = MESES_ABREV[:6]
            realizado = [450000, 520000, 480000, 550000, 490000, 610000]
            projetado = [500000, 550000, 520000, 580000, 540000, 650000]

        fig_comp = go.Figure(data=[
            go.Bar(name="Realizado", x=meses, y=realizado, marker_color="#06b6d4"),
            go.Bar(name="Projetado", x=meses, y=projetado, marker_color="#0c3a66")
        ])
        fig_comp.update_layout(
            barmode="group",
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            hovermode="x unified",
            plot_bgcolor="rgba(240, 249, 252, 0.5)",
            paper_bgcolor="rgba(255, 255, 255, 0)"
        )
        st.plotly_chart(fig_comp, use_container_width=True, config=PLOTLY_CONFIG)

    # ================= Gráfico 4: Taxa de Crescimento por Produto =================
    with col_chart4:
        st.markdown("#### 🎯 Taxa de Crescimento por Produto")

        if df_upload is not None and {"PRODUTO", "CURVA_REALIZADO", "PROJETADO_AJUSTADO"}.issubset(df_upload.columns):
            dfp = df_upload.copy()
            dfp["CURVA_REALIZADO"] = _ensure_numeric(dfp["CURVA_REALIZADO"])
            dfp["PROJETADO_AJUSTADO"] = _ensure_numeric(dfp["PROJETADO_AJUSTADO"])

            prod_data = dfp.groupby("PRODUTO").agg({
                "CURVA_REALIZADO": "sum",
                "PROJETADO_AJUSTADO": "sum"
            }).reset_index()

            # Evita divisão por zero
            denom = prod_data["CURVA_REALIZADO"].replace(0, np.nan)
            taxas = ((prod_data["PROJETADO_AJUSTADO"] - prod_data["CURVA_REALIZADO"]) / denom * 100).fillna(0.0).round(2)

            produtos = prod_data["PRODUTO"].tolist()
            cores_taxa = ["#06b6d4" if x > 10 else "#a855f7" for x in taxas]

        else:
            produtos = ["Crédito Pessoal", "Empréstimo", "Fundo Invest."]
            taxas = pd.Series([12.5, 18.3, 15.7])
            cores_taxa = ["#06b6d4" if x > 10 else "#a855f7" for x in taxas]

        fig_taxa = go.Figure(data=[
            go.Bar(y=produtos, x=taxas, orientation="h", marker_color=cores_taxa)
        ])
        fig_taxa.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title="Taxa de Crescimento (%)",
            plot_bgcolor="rgba(240, 249, 252, 0.5)",
            paper_bgcolor="rgba(255, 255, 255, 0)"
        )
        st.plotly_chart(fig_taxa, use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("---")

    # ================= Tabela: Variação Mensal por Ano =================
    st.markdown("#### 📈 Variação Mensal por Ano")
    gerar_tabela_variacao()


def gerar_tabela_variacao():
    """
    Gera tabela com variação percentual mês-a-mês por ano.
    Usa colunas sanitizadas do Upload (MES_NUM, ANO_NUM).
    Fallback com to_datetime sem 'format' rígido se necessário.
    """
    df = get_dados_upload()
    if df is None or len(df) == 0:
        # Dados de exemplo
        meses = MESES_FULL_UPPER
        dados_tabela = {
            "REALIZADO 2024": ["R$ 0,00"] * 12,
            "% VARIAÇÃO 2025": ["0%"] * 12,
            "REALIZADO 2025": ["R$ 0,00"] * 12,
            "% VARIAÇÃO 2026": ["0%"] * 12,
            "REALIZADO 2026": ["R$ 0,00"] * 12,
        }
        df_exemplo = pd.DataFrame(dados_tabela, index=meses)
        st.dataframe(df_exemplo, use_container_width=True, height=400)
        st.info("ℹ️ Carregue dados na página **Upload** para atualizar com valores reais.")
        return

    dff = df.copy()

    # Mes/ano seguros
    dff["MES_NUM"] = _mes_from_df(dff)
    dff["ANO_NUM"] = _ano_from_df(dff)

    # Filtra registros válidos
    dff = dff[dff["MES_NUM"].between(1, 12) & dff["ANO_NUM"].notna()].copy()

    # Garante numérico para a métrica base
    base_col = "CURVA_REALIZADO" if "CURVA_REALIZADO" in dff.columns else None
    if base_col is None:
        st.info("ℹ️ Coluna 'CURVA_REALIZADO' não encontrada. Exibindo tabela vazia.")
        st.dataframe(pd.DataFrame(index=MESES_FULL_UPPER), use_container_width=True, height=400)
        return

    dff[base_col] = _ensure_numeric(dff[base_col])

    # Agrega por mês/ano
    piv = dff.pivot_table(values=base_col, index="MES_NUM", columns="ANO_NUM", aggfunc="sum").sort_index()
    # Reindexa 1..12 para forçar ordem
    piv = piv.reindex(range(1, 13))
    piv.index = MESES_FULL_UPPER  # nomes exibidos

    anos = sorted([c for c in piv.columns if pd.notna(c)])

    # Monta tabela formatada + variação contra ano anterior quando possível
    tabela = pd.DataFrame(index=piv.index)
    for i, ano in enumerate(anos):
        col_fmt = piv[ano].fillna(0.0).apply(lambda x: f"R$ {x:,.0f}")
        tabela[f"REALIZADO {int(ano)}"] = col_fmt

        if i > 0:
            ano_ant = anos[i - 1]
            base_ant = piv[ano_ant].replace(0, np.nan)
            variacao = ((piv[ano] - base_ant) / base_ant * 100).fillna(0.0)
            tabela[f"% VARIAÇÃO {int(ano)}"] = variacao.apply(lambda x: f"{x:.1f}%")

    st.dataframe(tabela, use_container_width=True, height=400)