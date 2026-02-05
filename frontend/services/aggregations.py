# frontend/services/aggregations.py
import pandas as pd
import numpy as np

from utils_ext.series import (
    _norm_txt, _mes_to_num, _ensure_cli_n, _mask_trailing_zeros
)

def _carregar_curvas_base(df_upload: pd.DataFrame, cliente: str, categoria: str, produto: str):
    if df_upload is None or len(df_upload) == 0:
        return [0.0]*12, [0.0]*12, None
    dff = _ensure_cli_n(df_upload)
    if "CAT_N" not in dff.columns:
        dff["CAT_N"] = dff["CATEGORIA"].astype(str).apply(_norm_txt)
    if "PROD_N" not in dff.columns:
        dff["PROD_N"] = dff["PRODUTO"].astype(str).apply(_norm_txt)
    if "MES_NUM" not in dff.columns:
        dff["MES_NUM"] = dff["MES"].apply(_mes_to_num) if "MES" in dff.columns else np.nan
    if "ANO_NUM" not in dff.columns and "ANO" in dff.columns:
        dff["ANO_NUM"] = pd.to_numeric(dff["ANO"], errors="coerce").fillna(0).astype(int)
    elif "ANO_NUM" not in dff.columns:
        dff["ANO_NUM"] = 0

    if cliente and cliente != "Todos":
        dff = dff[dff["CLI_N"] == _norm_txt(cliente)]
    dff = dff[(dff["CAT_N"] == _norm_txt(categoria)) & (dff["PROD_N"] == _norm_txt(produto))]
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

def _carregar_ajustada_produto(df_upload: pd.DataFrame, cliente: str, categoria: str, produto: str, ano_proj: int):
    """
    Série [12] do produto/ano: PROJETADO_AJUSTADO (fallback Analítico).
    """
    if df_upload is None or df_upload.empty:
        return None
    dff = _ensure_cli_n(df_upload)
    if cliente and cliente != "Todos":
        dff = dff[dff["CLI_N"] == _norm_txt(cliente)]
    if "CAT_N" not in dff.columns:
        dff["CAT_N"] = dff["CATEGORIA"].astype(str).apply(_norm_txt)
    if "PROD_N" not in dff.columns:
        dff["PROD_N"] = dff["PRODUTO"].astype(str).apply(_norm_txt)
    dff = dff[(dff["CAT_N"] == _norm_txt(categoria)) & (dff["PROD_N"] == _norm_txt(produto))]
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

def _obter_realizados_por_ano(df_upload: pd.DataFrame, cliente: str, categoria: str, produto: str, mascarar_zeros_finais: bool = True):
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
    dff = dff[(dff["CAT_N"] == _norm_txt(categoria)) & (dff["PROD_N"] == _norm_txt(produto))]
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

def _agregados_por_categoria(df_upload: pd.DataFrame, cliente: str, ano_proj: int, mascarar_zeros_finais: bool = True):
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
        rl  = (dff[dff["ANO_NUM"] == int(ano_r)]  .groupby(["CATEGORIA","MES_NUM"], as_index=False)[col_real].sum()) if ano_r  is not None else dff.iloc[0:0]
        rlp = (dff[dff["ANO_NUM"] == int(ano_rp)].groupby(["CATEGORIA","MES_NUM"], as_index=False)[col_real].sum()) if ano_rp is not None else dff.iloc[0:0]
    else:
        rl  = dff.iloc[0:0]
        rlp = dff.iloc[0:0]

    categorias = list(pd.concat([grp_proj["CATEGORIA"], grp_prev["CATEGORIA"]], ignore_index=True).dropna().astype(str).unique())

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

        ana_p  = arr(grp_prev, cat, "PROJETADO_ANALITICO")
        mer_p  = arr(grp_prev, cat, "PROJETADO_MERCADO")
        ajs_p  = arr(grp_prev, cat, "PROJETADO_AJUSTADO") if has_ajs else ana_p[:]
        rlz_p  = arr(rlp,      cat, col_real) if not rlp.empty else [0.0]*12

        out[cat] = {
            "ana": ana, "mer": mer, "ajs": ajs, "rlzd": rlz,
            "prev": {"ana": ana_p, "mer": mer_p, "ajs": ajs_p, "rlzd": rlz_p}
        }
    return out


def _agregados_por_produto(df_upload: pd.DataFrame, cliente: str, categoria: str, produto: str, ano_proj: int, mascarar_zeros_finais: bool = True):
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