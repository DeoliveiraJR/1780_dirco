# frontend/utils_ext/series.py
import pandas as pd
import numpy as np
import unicodedata
import re

def _norm_txt(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.strip().lower()


def _normalizar_codigo_produto(valor: str) -> str:
    texto = str(valor or "")
    if ":" in texto:
        texto = texto.split(":", 1)[0]
    return re.sub(r"\D", "", texto)


def _extrair_descricao_produto(valor: str) -> str:
    texto = str(valor or "")
    if ":" in texto:
        texto = texto.split(":", 1)[1]
    return _norm_txt(texto)


def _normalizar_tokens_produto(texto: str) -> set:
    if not texto:
        return set()

    tokens = set(re.findall(r"[a-z0-9]+", _norm_txt(texto)))
    norm_tokens = set()
    for token in tokens:
        token_norm = token
        # Regras de plural em português
        if len(token_norm) > 4 and token_norm.endswith("ais"):
            # especial → especiais: troca "ais" por "al"
            token_norm = token_norm[:-3] + "al"
        elif len(token_norm) > 4 and token_norm.endswith("eis"):
            # papel → papeis: troca "eis" por "el"
            token_norm = token_norm[:-3] + "el"
        elif len(token_norm) > 4 and token_norm.endswith("ois"):
            # caracol → caracois: troca "ois" por "ol"
            token_norm = token_norm[:-3] + "ol"
        elif len(token_norm) > 4 and token_norm.endswith("uis"):
            # azul → azuis: troca "uis" por "ul"
            token_norm = token_norm[:-3] + "ul"
        elif len(token_norm) > 4 and token_norm.endswith("es"):
            # Para palavras como "cheques", remover apenas o "s" (não os dois caracteres)
            # Checa se a letra antes do "e" é uma vogal
            vogais = {"a", "e", "i", "o", "u"}
            if len(token_norm) >= 3 and token_norm[-3] in vogais:
                token_norm = token_norm[:-1]
            else:
                token_norm = token_norm[:-2]
        elif len(token_norm) > 3 and token_norm.endswith("s"):
            token_norm = token_norm[:-1]
        norm_tokens.add(token_norm)
    return norm_tokens


def _produto_eh_equivalente(valor_base: str, valor_filtro: str) -> bool:
    if not valor_base or not valor_filtro:
        return False

    base_norm = _norm_txt(valor_base)
    filtro_norm = _norm_txt(valor_filtro)
    if base_norm == filtro_norm:
        return True

    base_cod = _normalizar_codigo_produto(valor_base)
    filtro_cod = _normalizar_codigo_produto(valor_filtro)
    if base_cod and filtro_cod and (
        base_cod == filtro_cod
        or base_cod.startswith(filtro_cod)
        or filtro_cod.startswith(base_cod)
    ):
        return True

    base_desc = _extrair_descricao_produto(valor_base)
    filtro_desc = _extrair_descricao_produto(valor_filtro)
    if base_desc and filtro_desc:
        if base_desc == filtro_desc:
            return True

        base_tokens = _normalizar_tokens_produto(base_desc)
        filtro_tokens = _normalizar_tokens_produto(filtro_desc)
        if base_tokens and filtro_tokens:
            if base_tokens == filtro_tokens:
                return True
            if base_tokens.issubset(filtro_tokens) or filtro_tokens.issubset(base_tokens):
                return True

    return False

def _mes_to_num(x):
    if pd.isna(x): return np.nan
    s = str(x).strip()
    try:
        n = int(s);  return n if 1 <= n <= 12 else np.nan
    except Exception:
        pass
    s3 = s.upper()[:3]
    mapa = {"JAN":1,"FEV":2,"MAR":3,"ABR":4,"MAI":5,"JUN":6,"JUL":7,"AGO":8,"SET":9,"OUT":10,"NOV":11,"DEZ":12}
    return mapa.get(s3, np.nan)

def _variacao_mensal(series_12):
    out, prev = [], None
    for i, v in enumerate(series_12):
        v = 0.0 if pd.isna(v) else float(v)
        out.append(0.0 if i == 0 or prev in (None, 0) else (v - prev) / abs(prev))
        prev = v
    return out

def _ensure_cli_n(df: pd.DataFrame) -> pd.DataFrame:
    dff = df.copy()
    if "CLI_N" in dff.columns:
        return dff
    if "TIPO_CLIENTE" in dff.columns:
        dff["CLI_N"] = dff["TIPO_CLIENTE"].astype(str).apply(_norm_txt)
    elif "TP_CLIENTE" in dff.columns:
        dff["CLI_N"] = dff["TP_CLIENTE"].astype(str).apply(_norm_txt)
        if "TIPO_CLIENTE" not in dff.columns:
            dff["TIPO_CLIENTE"] = dff["TP_CLIENTE"]
    else:
        dff["CLI_N"] = ""
    return dff


def _ensure_normalized_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona colunas normalizadas de filtro se ainda não existirem."""
    if df is None or df.empty:
        return df

    dff = df.copy()
    dff = _ensure_cli_n(dff)

    if "CAT_N" not in dff.columns and "CATEGORIA" in dff.columns:
        dff["CAT_N"] = dff["CATEGORIA"].astype(str).apply(_norm_txt)

    if "PROD_N" not in dff.columns and "PRODUTO" in dff.columns:
        dff["PROD_N"] = dff["PRODUTO"].astype(str).apply(_norm_txt)

    if "MES_N" not in dff.columns and "MES" in dff.columns:
        dff["MES_N"] = dff["MES"].astype(str).apply(_norm_txt)

    if "MES" in dff.columns:
        computed_mes = dff["MES"].apply(_mes_to_num).fillna(0).astype(int)
        if "MES_NUM" not in dff.columns:
            dff["MES_NUM"] = computed_mes
        else:
            mask_invalid = ~dff["MES_NUM"].apply(lambda x: str(x).isdigit() and 1 <= int(x) <= 12)
            dff.loc[mask_invalid, "MES_NUM"] = computed_mes[mask_invalid]
    elif "MES_NUM" not in dff.columns:
        dff["MES_NUM"] = pd.Series([0] * len(dff))

    if "ANO_NUM" not in dff.columns:
        if "ANO" in dff.columns:
            dff["ANO_NUM"] = pd.to_numeric(dff["ANO"], errors="coerce")
        else:
            dff["ANO_NUM"] = pd.Series([0] * len(dff))
        if "DATA_COMPLETA" in dff.columns:
            data_dt = pd.to_datetime(dff["DATA_COMPLETA"], errors="coerce", dayfirst=True)
            mask = dff["ANO_NUM"].isna() & data_dt.notna()
            dff.loc[mask, "ANO_NUM"] = data_dt.dt.year[mask]
        dff["ANO_NUM"] = dff["ANO_NUM"].fillna(0).astype(int)

    if "TIP_TD_N" not in dff.columns and "TIP_TD" in dff.columns:
        dff["TIP_TD_N"] = dff["TIP_TD"].astype(str).apply(_norm_txt)

    if "CD_TIP_AGPD_N" not in dff.columns and "CD_TIP_AGPD" in dff.columns:
        dff["CD_TIP_AGPD_N"] = dff["CD_TIP_AGPD"].astype(str).apply(_norm_txt)

    return dff


def _mask_trailing_zeros(vals: list):
    """
    Converte zeros APÓS o último valor != 0 em np.nan (quebra a linha no gráfico).
    Mantém zeros 'no meio' e no início (se existirem).
    """
    if not vals:
        return vals
    arr = list(vals)
    last_real = -1
    for i, v in enumerate(arr):
        try:
            fv = float(v)
        except Exception:
            fv = np.nan
        if np.isfinite(fv) and fv != 0.0:
            last_real = i
    if last_real >= 0 and last_real + 1 < len(arr):
        for j in range(last_real + 1, len(arr)):
            try:
                fv = float(arr[j])
            except Exception:
                fv = np.nan
            if np.isfinite(fv) and fv == 0.0:
                arr[j] = np.nan
    return arr