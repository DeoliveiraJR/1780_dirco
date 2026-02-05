# frontend/utils_ext/series.py
import pandas as pd
import numpy as np
import unicodedata

def _norm_txt(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.strip().lower()

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