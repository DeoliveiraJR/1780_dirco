# frontend/services/aggregations.py
import pandas as pd
import numpy as np
import streamlit as st

from utils_ext.series import (
    _norm_txt, _mes_to_num, _ensure_cli_n, _ensure_normalized_columns, _mask_trailing_zeros,
    _produto_eh_equivalente
)


def _filtrar_categoria_produto(dff: pd.DataFrame, categoria: str, produto: str) -> pd.DataFrame:
    """Filtra por categoria e, opcionalmente, por produto.

    Quando produto for vazio ou 'TODOS', agrega todos os produtos da categoria.
    """
    dff = dff[dff["CAT_N"] == _norm_txt(categoria)]
    produto_norm = _norm_txt(produto)
    if produto_norm and produto_norm != "todos":
        if "PROD_N" in dff.columns and produto_norm in set(dff["PROD_N"].dropna().unique()):
            dff = dff[dff["PROD_N"] == produto_norm]
        else:
            # Fallback para equivalencia singular/plural e codificacoes legadas.
            mask = dff["PRODUTO"].apply(lambda x: _produto_eh_equivalente(x, produto))
            dff = dff[mask]
    return dff


def _aplicar_filtros_dimensao(
    dff: pd.DataFrame,
    cd_tip_agpd: str = "Todos",
    tip_td: str = "Todos",
) -> pd.DataFrame:
    """Aplica filtros de dimensão quando as colunas existem na base."""
    out = dff
    if (
        "CD_TIP_AGPD" in out.columns
        and cd_tip_agpd
        and str(cd_tip_agpd).strip()
        and str(cd_tip_agpd) != "Todos"
    ):
        alvo = _norm_txt(cd_tip_agpd)
        col_norm = "CD_TIP_AGPD_N" if "CD_TIP_AGPD_N" in out.columns else "CD_TIP_AGPD"
        if col_norm == "CD_TIP_AGPD_N":
            out = out[out[col_norm] == alvo]
        else:
            out = out[out[col_norm].astype(str).apply(_norm_txt) == alvo]

    if (
        "TIP_TD" in out.columns
        and tip_td
        and str(tip_td).strip()
        and str(tip_td) != "Todos"
    ):
        alvo = _norm_txt(tip_td)
        col_norm = "TIP_TD_N" if "TIP_TD_N" in out.columns else "TIP_TD"
        if col_norm == "TIP_TD_N":
            out = out[out[col_norm] == alvo]
        else:
            out = out[out[col_norm].astype(str).apply(_norm_txt) == alvo]

    return out

@st.cache_data(show_spinner=False)
def _carregar_curvas_base(
    df_upload: pd.DataFrame,
    cliente: str,
    categoria: str,
    produto: str,
    cd_tip_agpd: str = "Todos",
    tip_td: str = "Todos",
):
    if df_upload is None or len(df_upload) == 0:
        return [0.0]*12, [0.0]*12, None
    
    # Validar colunas essenciais
    colunas_requeridas = ["PROJETADO_ANALITICO", "PROJETADO_MERCADO"]
    if not all(col in df_upload.columns for col in colunas_requeridas):
        return [0.0]*12, [0.0]*12, None
    
    dff = _ensure_normalized_columns(df_upload)

    if cliente and cliente != "Todos":
        dff = dff[dff["CLI_N"] == _norm_txt(cliente)]
    dff = _aplicar_filtros_dimensao(dff, cd_tip_agpd=cd_tip_agpd, tip_td=tip_td)
    dff = _filtrar_categoria_produto(dff, categoria, produto)
    if dff.empty:
        return [0.0]*12, [0.0]*12, None

    ano = int(dff["ANO_NUM"].max())
    base_ano = dff[(dff["ANO_NUM"] == ano) & (pd.to_numeric(dff["MES_NUM"], errors="coerce").between(1, 12))]
    if base_ano.empty:
        return [0.0]*12, [0.0]*12, ano

    grp = (base_ano.groupby("MES_NUM", as_index=True)[["PROJETADO_ANALITICO","PROJETADO_MERCADO"]]
                   .sum()
                   .reindex(range(1,13))
                   .fillna(0.0))

    ana = (grp["PROJETADO_ANALITICO"].astype(float).tolist() + [0.0]*12)[:12]
    mer = (grp["PROJETADO_MERCADO"].astype(float).tolist() + [0.0]*12)[:12]
    return ana, mer, ano

@st.cache_data(show_spinner=False)
def _carregar_curvas_por_ano(
    df_upload: pd.DataFrame,
    cliente: str,
    categoria: str,
    produto: str,
    ano_proj: int,
    cd_tip_agpd: str = "Todos",
    tip_td: str = "Todos",
):
    """
    Carrega curvas analítica, mercado e ajustada para um ano específico.
    Retorna: (ana[12], mer[12], ajustada[12])
    """
    if df_upload is None or df_upload.empty:
        return [0.0]*12, [0.0]*12, [0.0]*12
    
    dff = _ensure_normalized_columns(df_upload)

    if cliente and cliente != "Todos":
        dff = dff[dff["CLI_N"] == _norm_txt(cliente)]
    dff = _aplicar_filtros_dimensao(dff, cd_tip_agpd=cd_tip_agpd, tip_td=tip_td)
    
    dff = _filtrar_categoria_produto(dff, categoria, produto)
    dff = dff[(dff["ANO_NUM"] == int(ano_proj)) & (pd.to_numeric(dff["MES_NUM"], errors="coerce").between(1, 12))]
    
    if dff.empty:
        return [0.0]*12, [0.0]*12, [0.0]*12

    grp = dff.groupby("MES_NUM", as_index=True).agg(
        PROJETADO_ANALITICO=("PROJETADO_ANALITICO", "sum"),
        PROJETADO_MERCADO=("PROJETADO_MERCADO", "sum"),
        PROJETADO_AJUSTADO=("PROJETADO_AJUSTADO", "sum") if "PROJETADO_AJUSTADO" in dff.columns else ("PROJETADO_ANALITICO", "sum")
    ).reindex(range(1, 13)).fillna(0.0)

    ana = (grp["PROJETADO_ANALITICO"].astype(float).tolist() + [0.0]*12)[:12]
    mer = (grp["PROJETADO_MERCADO"].astype(float).tolist() + [0.0]*12)[:12]
    ajs = (grp["PROJETADO_AJUSTADO"].astype(float).tolist() + [0.0]*12)[:12]
    
    return ana, mer, ajs


@st.cache_data(show_spinner=False)
def _carregar_proximos_12_meses(
    df_upload: pd.DataFrame,
    cliente: str,
    categoria: str,
    produto: str,
    mes_atual: int,
    ano_atual: int,
    mascarar_zeros_finais: bool = True,
    cd_tip_agpd: str = "Todos",
    tip_td: str = "Todos",
):
    """
    Carrega dados para os próximos 12 meses, combinando anos se necessário.
    
    Retorna:
    {
        "meses": ["Mar 2026", "Abr 2026", ..., "Mar 2027"],
        "meses_num": [3, 4, ..., 12, 1, 2, 3],
        "anos": [2026, 2026, ..., 2027],
        "rlzd": [value, ...],      # Realizado (se houver)
        "ana": [value, ...],       # Projeção Analítica
        "mer": [value, ...],       # Projeção Mercado
        "ajs": [value, ...],       # Projeção Ajustada
    }
    """
    from utils_ext.constants import MESES_ABR_LIST
    
    if df_upload is None or df_upload.empty:
        return None
    
    resultado = {
        "meses": [],
        "meses_num": [],
        "anos": [],
        "rlzd": [],
        "ana": [],
        "mer": [],
        "ajs": []
    }
    
    # Carrega realizados para ambos os anos
    r_ano_atual = _obter_realizados_por_ano(
        df_upload,
        cliente,
        categoria,
        produto,
        mascarar_zeros_finais=mascarar_zeros_finais,
        cd_tip_agpd=cd_tip_agpd,
        tip_td=tip_td,
    )
    
    # Carrega projeções para ano atual e próximo ano
    ana_atual, mer_atual, ajs_atual = _carregar_curvas_por_ano(
        df_upload,
        cliente,
        categoria,
        produto,
        ano_atual,
        cd_tip_agpd=cd_tip_agpd,
        tip_td=tip_td,
    )
    ano_proximo = ano_atual + 1
    ana_proximo, mer_proximo, ajs_proximo = _carregar_curvas_por_ano(
        df_upload,
        cliente,
        categoria,
        produto,
        ano_proximo,
        cd_tip_agpd=cd_tip_agpd,
        tip_td=tip_td,
    )
    
    rlzd_ano_atual = r_ano_atual.get(ano_atual, [0.0]*12) if r_ano_atual else [0.0]*12
    rlzd_ano_proximo = r_ano_atual.get(ano_proximo, [0.0]*12) if r_ano_atual else [0.0]*12
    
    # Constrói 12 meses a partir do mês atual até 12 meses à frente
    for i in range(12):
        # Mês no intervalo de 0-11
        mes_idx_absoluto = (mes_atual - 1 + i)  # 0-23 (depe do mês_atual)
        ano = ano_atual if mes_idx_absoluto < 12 else ano_proximo
        
        # Mês em 1-12 para o ano específico
        mes_num = (mes_idx_absoluto % 12) + 1  # 1-12
        mes_idx = mes_num - 1  # 0-11 para indexação de array
        
        # Valor realizado
        if ano == ano_atual:
            rlzd_val = rlzd_ano_atual[mes_idx] if mes_idx < len(rlzd_ano_atual) else 0.0
        else:
            rlzd_val = rlzd_ano_proximo[mes_idx] if mes_idx < len(rlzd_ano_proximo) else 0.0
        
        # Projeções
        if ano == ano_atual:
            ana_val = ana_atual[mes_idx] if mes_idx < len(ana_atual) else 0.0
            mer_val = mer_atual[mes_idx] if mes_idx < len(mer_atual) else 0.0
            ajs_val = ajs_atual[mes_idx] if mes_idx < len(ajs_atual) else 0.0
        else:
            ana_val = ana_proximo[mes_idx] if mes_idx < len(ana_proximo) else 0.0
            mer_val = mer_proximo[mes_idx] if mes_idx < len(mer_proximo) else 0.0
            ajs_val = ajs_proximo[mes_idx] if mes_idx < len(ajs_proximo) else 0.0
        
        # Regra: se mês já passou E tem realizado, usar realizado
        if ano == ano_atual and mes_num <= mes_atual and rlzd_val != 0.0:
            ana_val = rlzd_val
            mer_val = rlzd_val
            ajs_val = rlzd_val
        
        resultado["meses"].append(f"{MESES_ABR_LIST[mes_num-1]} {ano}")
        resultado["meses_num"].append(mes_num)
        resultado["anos"].append(ano)
        resultado["rlzd"].append(rlzd_val)
        resultado["ana"].append(ana_val)
        resultado["mer"].append(mer_val)
        resultado["ajs"].append(ajs_val)
    
    return resultado


@st.cache_data(show_spinner=False)
def _carregar_ajustada_produto(
    df_upload: pd.DataFrame,
    cliente: str,
    categoria: str,
    produto: str,
    ano_proj: int,
    cd_tip_agpd: str = "Todos",
    tip_td: str = "Todos",
):
    """
    Série [12] do produto/ano: PROJETADO_AJUSTADO (fallback Analítico).
    """
    if df_upload is None or df_upload.empty:
        return None
    dff = _ensure_cli_n(df_upload)
    if cliente and cliente != "Todos":
        dff = dff[dff["CLI_N"] == _norm_txt(cliente)]
    dff = _aplicar_filtros_dimensao(dff, cd_tip_agpd=cd_tip_agpd, tip_td=tip_td)
    if "CAT_N" not in dff.columns:
        dff["CAT_N"] = dff["CATEGORIA"].astype(str).apply(_norm_txt)
    if "PROD_N" not in dff.columns:
        dff["PROD_N"] = dff["PRODUTO"].astype(str).apply(_norm_txt)
    dff = _filtrar_categoria_produto(dff, categoria, produto)
    if dff.empty:
        return None

    if "MES_NUM" not in dff.columns:
        dff["MES_NUM"] = dff["MES"].apply(_mes_to_num) if "MES" in dff.columns else np.nan
    if "ANO_NUM" not in dff.columns:
        dff["ANO_NUM"] = pd.to_numeric(dff.get("ANO", 0), errors="coerce").fillna(0).astype(int)

    dff = dff[(dff["ANO_NUM"] == int(ano_proj)) & (pd.to_numeric(dff["MES_NUM"], errors="coerce").between(1,12))]
    if dff.empty:
        return None

    col = "PROJETADO_AJUSTADO" if "PROJETADO_AJUSTADO" in dff.columns else "PROJETADO_ANALITICO"
    s = (dff.groupby("MES_NUM", as_index=True)[col]
            .sum().reindex(range(1,13)).fillna(0.0).astype(float))
    return (s.tolist() + [0.0]*12)[:12]

@st.cache_data(show_spinner=False)
def _obter_realizados_por_ano(
    df_upload: pd.DataFrame,
    cliente: str,
    categoria: str,
    produto: str,
    mascarar_zeros_finais: bool = True,
    cd_tip_agpd: str = "Todos",
    tip_td: str = "Todos",
):
    result = {}
    if df_upload is None or df_upload.empty:
        return result
    dff = _ensure_cli_n(df_upload)
    if "CAT_N" not in dff.columns:
        dff["CAT_N"] = dff["CATEGORIA"].astype(str).apply(_norm_txt)
    if "PROD_N" not in dff.columns:
        dff["PROD_N"] = dff["PRODUTO"].astype(str).apply(_norm_txt)
    if "MES_NUM" not in dff.columns:
        dff["MES_NUM"] = dff["MES"].apply(_mes_to_num) if "MES" in dff.columns else np.nan
    if "ANO_NUM" not in dff.columns:
        dff["ANO_NUM"] = pd.to_numeric(dff.get("ANO", 0), errors="coerce").fillna(0).astype(int)

    col_realizado = "CURVA_REALIZADO" if "CURVA_REALIZADO" in dff.columns else ("REALIZADO" if "REALIZADO" in dff.columns else None)
    if not col_realizado:
        return result

    if cliente and cliente != "Todos":
        dff = dff[dff["CLI_N"] == _norm_txt(cliente)]
    dff = _aplicar_filtros_dimensao(dff, cd_tip_agpd=cd_tip_agpd, tip_td=tip_td)
    dff = _filtrar_categoria_produto(dff, categoria, produto)
    dff = dff[pd.to_numeric(dff["MES_NUM"], errors="coerce").between(1, 12)]
    dff = dff[pd.to_numeric(dff["ANO_NUM"], errors="coerce") >= 2022]
    if dff.empty:
        return result

    grp = (dff.groupby(["ANO_NUM","MES_NUM"], as_index=True)[col_realizado]
             .sum().unstack(fill_value=0.0)
             .reindex(columns=range(1,13), fill_value=0.0))
    for ano in sorted(grp.index.tolist()):
        serie = (grp.loc[ano].astype(float).tolist() + [0.0]*12)[:12]
        result[int(ano)] = _mask_trailing_zeros(serie) if mascarar_zeros_finais else serie
    return result

@st.cache_data(show_spinner=False)
def _agregados_por_categoria(
    df_upload: pd.DataFrame,
    cliente: str,
    ano_proj: int,
    mascarar_zeros_finais: bool = True,
    cd_tip_agpd: str = "Todos",
    tip_td: str = "Todos",
):
    """
    Retorna:
      { categoria: {
          "ana":[12], "mer":[12], "ajs":[12], "rlzd":[12],
          "prev": {"ana":[12], "mer":[12], "ajs":[12], "rlzd":[12]}
        } }
    """
    out = {}
    if df_upload is None or df_upload.empty:
        return out

    dff = _ensure_cli_n(df_upload).copy()
    if cliente and cliente != "Todos":
        dff = dff[dff["CLI_N"] == _norm_txt(cliente)]
    dff = _aplicar_filtros_dimensao(dff, cd_tip_agpd=cd_tip_agpd, tip_td=tip_td)

    if "CAT_N" not in dff.columns:
        dff["CAT_N"] = dff["CATEGORIA"].astype(str).apply(_norm_txt)
    if "MES_NUM" not in dff.columns:
        dff["MES_NUM"] = dff["MES"].apply(_mes_to_num) if "MES" in dff.columns else np.nan
    if "ANO_NUM" not in dff.columns:
        dff["ANO_NUM"] = pd.to_numeric(dff.get("ANO", 0), errors="coerce").fillna(0).astype(int)
    dff = dff[pd.to_numeric(dff["MES_NUM"], errors="coerce").between(1,12)]
    dff = dff[pd.to_numeric(dff["ANO_NUM"], errors="coerce") >= 2022]

    col_real = "CURVA_REALIZADO" if "CURVA_REALIZADO" in dff.columns else ("REALIZADO" if "REALIZADO" in dff.columns else None)
    has_ajs = "PROJETADO_AJUSTADO" in dff.columns

    # Ano corrente
    proj = dff[dff["ANO_NUM"] == int(ano_proj)].copy()
    if proj.empty:
        proj = dff.iloc[0:0].copy()

    grp_proj = (proj.groupby(["CATEGORIA","MES_NUM"], as_index=False)
                    .agg(PROJETADO_ANALITICO=("PROJETADO_ANALITICO","sum"),
                         PROJETADO_MERCADO=("PROJETADO_MERCADO","sum"),
                         PROJETADO_AJUSTADO=("PROJETADO_AJUSTADO","sum") if has_ajs else ("PROJETADO_ANALITICO","sum")))

    # Ano anterior
    prev_year = int(ano_proj) - 1 if ano_proj else None
    if prev_year is not None:
        proj_prev = dff[dff["ANO_NUM"] == prev_year].copy()
        if proj_prev.empty: proj_prev = dff.iloc[0:0].copy()
        grp_prev = (proj_prev.groupby(["CATEGORIA","MES_NUM"], as_index=False)
                        .agg(PROJETADO_ANALITICO=("PROJETADO_ANALITICO","sum"),
                             PROJETADO_MERCADO=("PROJETADO_MERCADO","sum"),
                             PROJETADO_AJUSTADO=("PROJETADO_AJUSTADO","sum") if has_ajs else ("PROJETADO_ANALITICO","sum")))
    else:
        grp_prev = dff.iloc[0:0].copy()

    # Realizado ref/prev
    if col_real:
        anos_r = sorted(dff["ANO_NUM"].unique())
        ano_r  = ano_proj if (ano_proj in anos_r) else (anos_r[-1] if anos_r else ano_proj)
        ano_rp = prev_year if (prev_year in anos_r) else (max([a for a in anos_r if a < (ano_proj or 9999)], default=None))
        # Referência principal para cards: 2025; fallback para último ano anterior disponível.
        if 2025 in anos_r:
            ano_ref_cards = 2025
        else:
            ano_ref_cards = max([a for a in anos_r if a < (ano_proj or 9999)], default=(anos_r[-1] if anos_r else None))
        rl  = (dff[dff["ANO_NUM"] == int(ano_r)]  .groupby(["CATEGORIA","MES_NUM"], as_index=False)[col_real].sum()) if ano_r  is not None else dff.iloc[0:0]
        rlp = (dff[dff["ANO_NUM"] == int(ano_rp)].groupby(["CATEGORIA","MES_NUM"], as_index=False)[col_real].sum()) if ano_rp is not None else dff.iloc[0:0]
        rlr = (dff[dff["ANO_NUM"] == int(ano_ref_cards)].groupby(["CATEGORIA","MES_NUM"], as_index=False)[col_real].sum()) if ano_ref_cards is not None else dff.iloc[0:0]
    else:
        ano_ref_cards = None
        rl  = dff.iloc[0:0]
        rlp = dff.iloc[0:0]
        rlr = dff.iloc[0:0]

    categorias = list(
        pd.concat(
            [
                grp_proj.get("CATEGORIA", pd.Series(dtype=str)),
                grp_prev.get("CATEGORIA", pd.Series(dtype=str)),
                rl.get("CATEGORIA", pd.Series(dtype=str)),
                rlr.get("CATEGORIA", pd.Series(dtype=str)),
            ],
            ignore_index=True,
        )
        .dropna()
        .astype(str)
        .unique()
    )

    def arr(df_, cat, col):
        if df_.empty or col not in df_.columns:
            return [0.0]*12
        s = (df_[df_["CATEGORIA"] == cat].set_index("MES_NUM")[col]
                .reindex(range(1,13)).fillna(0.0).astype(float))
        return (s.tolist() + [0.0]*12)[:12]

    for cat in categorias:
        ana   = arr(grp_proj, cat, "PROJETADO_ANALITICO")
        mer   = arr(grp_proj, cat, "PROJETADO_MERCADO")
        ajs   = arr(grp_proj, cat, "PROJETADO_AJUSTADO") if has_ajs else ana[:]
        rlz   = arr(rl,       cat, col_real) if not rl.empty else [0.0]*12
        if mascarar_zeros_finais:
            rlz = _mask_trailing_zeros(rlz)
        rlz_ref = arr(rlr, cat, col_real) if not rlr.empty else [0.0] * 12
        if mascarar_zeros_finais:
            rlz_ref = _mask_trailing_zeros(rlz_ref)

        ana_p  = arr(grp_prev, cat, "PROJETADO_ANALITICO")
        mer_p  = arr(grp_prev, cat, "PROJETADO_MERCADO")
        ajs_p  = arr(grp_prev, cat, "PROJETADO_AJUSTADO") if has_ajs else ana_p[:]
        rlz_p  = arr(rlp,      cat, col_real) if not rlp.empty else [0.0]*12

        out[cat] = {
            "ana": ana, "mer": mer, "ajs": ajs, "rlzd": rlz,
            "prev": {"ana": ana_p, "mer": mer_p, "ajs": ajs_p, "rlzd": rlz_p},
            "rlzd_ref": rlz_ref,
            "rlzd_ref_ano": int(ano_ref_cards) if ano_ref_cards is not None else None,
        }
    return out


def _agregados_por_produto(
    df_upload: pd.DataFrame,
    cliente: str,
    categoria: str,
    produto: str,
    ano_proj: int,
    mascarar_zeros_finais: bool = True,
    cd_tip_agpd: str = "Todos",
    tip_td: str = "Todos",
):
    """
    Retorna dados agregados para um produto específico:
      {
          "ana":[12], "mer":[12], "ajs":[12], "rlzd":[12],
          "prev": {"ana":[12], "mer":[12], "ajs":[12], "rlzd":[12]}
      }
    """
    empty = {
        "ana": [0.0]*12, "mer": [0.0]*12, "ajs": [0.0]*12, "rlzd": [0.0]*12,
        "prev": {"ana": [0.0]*12, "mer": [0.0]*12, "ajs": [0.0]*12, "rlzd": [0.0]*12}
    }
    
    if df_upload is None or df_upload.empty:
        return empty

    dff = _ensure_cli_n(df_upload).copy()
    
    # Filtro por cliente
    if cliente and cliente != "Todos":
        dff = dff[dff["CLI_N"] == _norm_txt(cliente)]
    dff = _aplicar_filtros_dimensao(dff, cd_tip_agpd=cd_tip_agpd, tip_td=tip_td)

    # Normaliza colunas
    if "CAT_N" not in dff.columns:
        dff["CAT_N"] = dff["CATEGORIA"].astype(str).apply(_norm_txt)
    if "PROD_N" not in dff.columns:
        dff["PROD_N"] = dff["PRODUTO"].astype(str).apply(_norm_txt)
    if "MES_NUM" not in dff.columns:
        dff["MES_NUM"] = dff["MES"].apply(_mes_to_num) if "MES" in dff.columns else np.nan
    if "ANO_NUM" not in dff.columns:
        dff["ANO_NUM"] = pd.to_numeric(dff.get("ANO", 0), errors="coerce").fillna(0).astype(int)
    
    # Filtra por categoria e produto
    dff = dff[(dff["CAT_N"] == _norm_txt(categoria)) & (dff["PROD_N"] == _norm_txt(produto))]
    dff = dff[pd.to_numeric(dff["MES_NUM"], errors="coerce").between(1,12)]
    dff = dff[pd.to_numeric(dff["ANO_NUM"], errors="coerce") >= 2022]
    
    if dff.empty:
        return empty

    col_real = "CURVA_REALIZADO" if "CURVA_REALIZADO" in dff.columns else ("REALIZADO" if "REALIZADO" in dff.columns else None)
    has_ajs = "PROJETADO_AJUSTADO" in dff.columns

    def arr_from_df(df_, col):
        if df_.empty or col not in df_.columns:
            return [0.0]*12
        s = (df_.groupby("MES_NUM")[col].sum()
                .reindex(range(1,13)).fillna(0.0).astype(float))
        return (s.tolist() + [0.0]*12)[:12]

    # Ano corrente
    proj = dff[dff["ANO_NUM"] == int(ano_proj)].copy() if ano_proj else dff.iloc[0:0]
    
    ana = arr_from_df(proj, "PROJETADO_ANALITICO")
    mer = arr_from_df(proj, "PROJETADO_MERCADO")
    ajs = arr_from_df(proj, "PROJETADO_AJUSTADO") if has_ajs else ana[:]
    rlz = arr_from_df(proj, col_real) if col_real else [0.0]*12
    if mascarar_zeros_finais:
        rlz = _mask_trailing_zeros(rlz)

    # Ano anterior
    prev_year = int(ano_proj) - 1 if ano_proj else None
    proj_prev = dff[dff["ANO_NUM"] == prev_year].copy() if prev_year else dff.iloc[0:0]
    
    ana_p = arr_from_df(proj_prev, "PROJETADO_ANALITICO")
    mer_p = arr_from_df(proj_prev, "PROJETADO_MERCADO")
    ajs_p = arr_from_df(proj_prev, "PROJETADO_AJUSTADO") if has_ajs else ana_p[:]
    rlz_p = arr_from_df(proj_prev, col_real) if col_real else [0.0]*12

    return {
        "ana": ana, "mer": mer, "ajs": ajs, "rlzd": rlz,
        "prev": {"ana": ana_p, "mer": mer_p, "ajs": ajs_p, "rlzd": rlz_p}
    }
