"""
Módulo de Funções de Cálculo Nativas para DRE Gerencial

Implementa funções de cálculo semelhante ao Excel para uso em fórmulas de metodologias:
- SOMA: Soma todos os valores
- MEDIA: Calcula a média aritmética
- MINIMO: Encontra o valor mínimo
- MAXIMO: Encontra o valor máximo

Sintaxe Básica:
    SOMA(TD71)              # Soma os 12 meses de TD71
    MEDIA(TD71;TD72)        # Média dos valores de TD71 e TD72 combinados
    MINIMO(TD71:TD90)       # Valor mínimo entre TD71 e TD90 (intervalo)
    MAXIMO(TD71;TD72;TD87)  # Valor máximo dos códigos especificados

Sintaxe com Janela Temporal:
    SOMA(TD71; 7)           # Soma dos PRÓXIMOS 7 meses reais após o mês base
    MEDIA(TD72; -7)         # Média dos ÚLTIMOS 7 meses reais antes do mês base
    MINIMO(TD71; -12)       # Valor mínimo dos últimos 12 meses na linha do tempo real

Sistema de Sazonalidade (Fixo vs Variável):
    FIXO: Mesmo período para todos os meses
        {tipo: FIXO, mes_inicio: 1, mes_fim: 7}  → Always Jan-Jul
    VARIÁVEL: Período móvel por mês
        {tipo: VARIAVEL, quantidade: 7, tipo_periodo: MES, periodoLinha: ULTIMO}
        → Cada mês calcula seus últimos 7 meses reais, sem wrap-around
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Union, Tuple, Optional


DEBUG_CALC_LOGS = False
_INDICES_12M_CACHE: Optional[Dict[str, List[float]]] = None
_INDICES_HIST_CACHE: Optional[Dict[str, List[Dict[str, float]]]] = None


def _log_calc(msg: str):
    if DEBUG_CALC_LOGS:
        print(msg)


def _coagir_numero_ou_none(valor: Any) -> Optional[float]:
    """Converte valores numericos preservando vazio logico como None."""
    if valor is None or isinstance(valor, bool):
        return None

    try:
        if pd.isna(valor):
            return None
    except Exception:
        pass

    if isinstance(valor, (int, float, np.number)):
        return float(valor)

    try:
        texto = str(valor).strip()
        if not texto:
            return None
        return float(texto)
    except Exception:
        return None


def _coletar_valores_excel(valores: List[Any]) -> List[float]:
    """Replica a semantica do Excel: ignora vazios e mantem zeros explicitos."""
    valores_validos: List[float] = []
    for valor in valores or []:
        numero = _coagir_numero_ou_none(valor)
        if numero is not None:
            valores_validos.append(numero)
    return valores_validos


def _normalizar_flags_item(item: Dict[str, Any], tamanho: int) -> List[bool]:
    """Obtém flags de preenchimento quando o contexto expõe vazio vs zero."""
    if not isinstance(item, dict) or tamanho <= 0:
        return [True] * max(int(tamanho), 0)

    candidatos = [
        item.get("valores_preenchidos"),
        item.get("projetado_preenchido"),
    ]
    for flags in candidatos:
        if isinstance(flags, list) and len(flags) >= tamanho:
            return [bool(v) for v in flags[:tamanho]]

    return [True] * tamanho


def _periodo_para_ordem(ano: int, mes: int) -> int:
    """Converte ano/mes em um indice cronologico monotônico."""
    return (int(ano) * 12) + int(mes)


def _ordem_para_periodo(ordem: int) -> Tuple[int, int]:
    """Converte o indice cronologico de volta para ano/mes."""
    ano = (int(ordem) - 1) // 12
    mes = (int(ordem) - 1) % 12 + 1
    return ano, mes


def _normalizar_serie_historica(serie: Optional[List[Dict[str, Any]]]) -> List[Dict[str, float]]:
    """
    Normaliza e agrega uma série histórica no formato:
    [{"ano": 2026, "mes": 5, "valor": 123.0}, ...]
    """
    if not serie:
        return []

    acumulado: Dict[Tuple[int, int], float] = {}
    for item in serie:
        if not isinstance(item, dict):
            continue

        try:
            ano = int(item.get("ano"))
            mes = int(item.get("mes"))
        except Exception:
            continue

        valor = _coagir_numero_ou_none(item.get("valor"))
        preenchido = bool(item.get("preenchido", valor is not None))
        if not preenchido or valor is None:
            continue

        if mes < 1 or mes > 12:
            continue

        chave = (ano, mes)
        acumulado[chave] = acumulado.get(chave, 0.0) + valor

    return [
        {"ano": ano, "mes": mes, "valor": float(valor)}
        for (ano, mes), valor in sorted(acumulado.items())
    ]


def _serie_historica_para_12_meses(serie_historica: List[Dict[str, float]], ano_referencia: int) -> List[float]:
    """Converte a série histórica para os 12 meses do ano de referência."""
    valores = [0.0] * 12
    for item in _normalizar_serie_historica(serie_historica):
        if int(item["ano"]) != int(ano_referencia):
            continue
        mes_idx = int(item["mes"]) - 1
        if 0 <= mes_idx < 12:
            valores[mes_idx] = float(item["valor"])
    return valores


def _obter_ano_referencia(contexto: Dict) -> int:
    meta = contexto.get("__meta__", {}) if isinstance(contexto, dict) else {}
    try:
        return int(meta.get("ano_referencia", datetime.now().year))
    except Exception:
        return datetime.now().year


def _obter_serie_historica_item(item: Dict[str, Any], ano_referencia: int) -> List[Dict[str, float]]:
    """Obtém a série histórica de um item do contexto ou usa o array do ano atual como fallback."""
    if not isinstance(item, dict):
        return []

    serie_historica = _normalizar_serie_historica(item.get("serie_historica"))
    if serie_historica:
        return serie_historica

    valores = item.get("valores", [0.0] * 12) or [0.0] * 12
    flags = _normalizar_flags_item(item, min(len(valores), 12))
    serie_fallback: List[Dict[str, float]] = []
    for idx, valor in enumerate(valores[:12]):
        if idx >= len(flags) or not flags[idx]:
            continue
        numero = _coagir_numero_ou_none(valor)
        if numero is None:
            continue
        serie_fallback.append(
            {"ano": int(ano_referencia), "mes": idx + 1, "valor": numero}
        )
    return serie_fallback


def _obter_valor_historico(
    item: Dict[str, Any],
    ano: int,
    mes: int,
    ano_referencia: int,
    fallback_mes_idx: Optional[int] = None,
) -> Optional[float]:
    """Busca um valor em ano/mes na série histórica, com fallback para o array de 12 meses."""
    for ponto in _obter_serie_historica_item(item, ano_referencia):
        if int(ponto["ano"]) == int(ano) and int(ponto["mes"]) == int(mes):
            return float(ponto["valor"])

    if int(ano) == int(ano_referencia):
        valores = item.get("valores", [0.0] * 12) or [0.0] * 12
        flags = _normalizar_flags_item(item, min(len(valores), 12))
        if fallback_mes_idx is None:
            fallback_mes_idx = int(mes) - 1
        if (
            0 <= fallback_mes_idx < len(valores)
            and fallback_mes_idx < len(flags)
            and flags[fallback_mes_idx]
        ):
            return _coagir_numero_ou_none(valores[fallback_mes_idx])

    return None


def _aplicar_resultados_parciais_na_referencia(
    item: Dict[str, Any],
    resultados_anteriores: List[float],
    ano_referencia: int,
    ate_mes_exclusivo: int,
) -> Dict[str, Any]:
    """Sobrescreve meses futuros já calculados para permitir encadeamento cronológico."""
    if not isinstance(item, dict) or not resultados_anteriores:
        return item

    item_override = dict(item)
    valores = list(item_override.get("valores") or [0.0] * 12)[:12]
    projetado = list(item_override.get("projetado") or valores)[:12]
    flags_valores = _normalizar_flags_item(item_override, 12)
    flags_proj = list(item_override.get("projetado_preenchido") or flags_valores)[:12]
    mes_corte = int(item_override.get("mes_corte", 0) or 0)
    serie_filtrada = []

    while len(valores) < 12:
        valores.append(0.0)
    while len(projetado) < 12:
        projetado.append(0.0)
    while len(flags_proj) < 12:
        flags_proj.append(False)

    limite = min(max(int(ate_mes_exclusivo) - 1, 0), 12)
    for idx in range(limite):
        mes = idx + 1
        if mes <= mes_corte:
            continue
        numero = _coagir_numero_ou_none(resultados_anteriores[idx])
        if numero is None:
            continue
        valores[idx] = numero
        projetado[idx] = numero
        flags_valores[idx] = True
        flags_proj[idx] = True

    for ponto in list(item_override.get("serie_historica") or []):
        if not isinstance(ponto, dict):
            continue
        try:
            if int(ponto.get("ano")) == int(ano_referencia) and 1 <= int(ponto.get("mes")) < int(ate_mes_exclusivo):
                continue
        except Exception:
            pass
        serie_filtrada.append(ponto)

    for idx in range(limite):
        if flags_valores[idx]:
            serie_filtrada.append({"ano": int(ano_referencia), "mes": idx + 1, "valor": float(valores[idx]), "preenchido": True})

    item_override["valores"] = valores
    item_override["valores_preenchidos"] = flags_valores
    item_override["projetado"] = projetado
    item_override["projetado_preenchido"] = flags_proj
    item_override["serie_historica"] = serie_filtrada
    return item_override


def _extrair_janela_historica_por_periodo(
    item: Dict[str, Any],
    ano_base: int,
    mes_base: int,
    janela: int,
    lag: int = 0,
    ano_referencia: Optional[int] = None,
) -> List[float]:
    """
    Extrai janelas cronológicas reais.

    Regras:
    - `janela < 0`: retorna os últimos N meses ANTERIORES ao mês base.
    - `janela > 0`: retorna os próximos N meses POSTERIORES ao mês base.
    - `lag`: desloca o mês base para trás antes de montar a janela.
    """
    if janela == 0:
        return []

    ano_ref = int(ano_referencia or ano_base)
    base_ord = _periodo_para_ordem(ano_base, mes_base) - int(lag or 0)
    quantidade = abs(int(janela))

    if janela < 0:
        ordens = [base_ord - passo for passo in range(quantidade, 0, -1)]
    else:
        ordens = [base_ord + passo for passo in range(1, quantidade + 1)]

    valores = []
    for ordem in ordens:
        ano, mes = _ordem_para_periodo(ordem)
        valores.append(_obter_valor_historico(item, ano, mes, ano_ref))
    return valores


def _extrair_sazonalidade_historica(
    item: Dict[str, Any],
    saz: Union[Dict, int, None],
    ano_base: int,
    mes_base: int,
    ano_referencia: Optional[int] = None,
) -> List[float]:
    """Aplica sazonalidade usando linha do tempo real em vez de um array circular."""
    saz_normalizada = normalizar_sazonalidade(saz)
    ano_ref = int(ano_referencia or ano_base)
    saz_tipo = saz_normalizada.get("tipo", "NENHUM")

    if saz_tipo == "NENHUM":
        return [_obter_valor_historico(item, ano_base, mes_base, ano_ref, mes_base - 1)]

    if saz_tipo == "FIXO":
        mes_inicio = max(1, int(saz_normalizada.get("mes_inicio", 1)))
        mes_fim = min(12, int(saz_normalizada.get("mes_fim", 12)))
        if mes_fim < mes_inicio:
            return []
        return [
            _obter_valor_historico(item, ano_base, mes, ano_ref, mes - 1)
            for mes in range(mes_inicio, mes_fim + 1)
        ]

    quantidade = max(1, int(saz_normalizada.get("quantidade", 1)))
    tipo_periodo = str(saz_normalizada.get("tipo_periodo", "MES")).upper()
    periodo_linha = str(saz_normalizada.get("periodoLinha", "ULTIMO")).upper()

    if tipo_periodo == "ANO":
        quantidade *= 12

    base_ord = _periodo_para_ordem(ano_base, mes_base)
    if periodo_linha == "ULTIMO":
        ordens = [base_ord - passo for passo in range(quantidade, 0, -1)]
    else:
        ordens = [base_ord + passo for passo in range(1, quantidade + 1)]

    valores = []
    for ordem in ordens:
        ano, mes = _ordem_para_periodo(ordem)
        valores.append(_obter_valor_historico(item, ano, mes, ano_ref))
    return valores


# ============================================================================
# FUNÇÕES NATIVAS DE CÁLCULO
# ============================================================================

def SOMA(valores: List[float]) -> float:
    """
    Calcula a soma total dos valores.
    
    Args:
        valores: Lista com valores mensais ou agregados
        
    Returns:
        float: Soma total
        
    Exemplo:
        SOMA([100, 200, 300]) → 600
    """
    try:
        return float(sum(_coletar_valores_excel(valores)))
    except Exception as e:
        print(f"[CALC] Erro em SOMA: {e}")
        return 0.0


def MEDIA(valores: List[float]) -> float:
    """
    Calcula a média aritmética dos valores.
    
    Args:
        valores: Lista com valores mensais ou agregados
        
    Returns:
        float: Média dos valores (0 se lista vazia)
        
    Exemplo:
        MEDIA([100, 200, 300]) → 200
    """
    try:
        valores_validos = _coletar_valores_excel(valores)
        if not valores_validos:
            return 0.0
        return float(sum(valores_validos) / len(valores_validos))
    except Exception as e:
        print(f"[CALC] Erro em MEDIA: {e}")
        return 0.0


def MEDIA_INTERNA(valores: List[float], percentual: float) -> float:
    """
    Calcula a media interna seguindo a regra do Excel/TRIMMEAN.

    O percentual indica o descarte total dos extremos. A quantidade descartada
    e arredondada para baixo ate o multiplo de 2 mais proximo, removendo a
    mesma quantidade do inicio e do fim da lista ordenada.
    """
    try:
        valores_validos = _coletar_valores_excel(valores)
        if not valores_validos:
            return 0.0

        percentual = float(percentual)
        if percentual < 0 or percentual > 1:
            _log_calc(f"[CALC] Percentual invalido em MEDIA_INTERNA: {percentual}")
            return 0.0

        total_valores = len(valores_validos)
        total_descartado = int(total_valores * percentual)
        total_descartado -= total_descartado % 2

        if total_descartado <= 0:
            return MEDIA(valores_validos)

        metade = total_descartado // 2
        valores_ordenados = sorted(valores_validos)
        valores_filtrados = valores_ordenados[metade: total_valores - metade]
        if not valores_filtrados:
            return 0.0

        return MEDIA(valores_filtrados)
    except Exception as e:
        print(f"[CALC] Erro em MEDIA_INTERNA: {e}")
        return 0.0


def MINIMO(valores: List[float]) -> float:
    """
    Encontra o valor mínimo dos valores.
    
    Args:
        valores: Lista com valores mensais ou agregados
        
    Returns:
        float: Valor mínimo (0 se lista vazia)
        
    Exemplo:
        MINIMO([100, 50, 300]) → 50
    """
    try:
        valores_validos = _coletar_valores_excel(valores)
        if not valores_validos:
            return 0.0
        return float(min(valores_validos))
    except Exception as e:
        print(f"[CALC] Erro em MINIMO: {e}")
        return 0.0


def MAXIMO(valores: List[float]) -> float:
    """
    Encontra o valor máximo dos valores.
    
    Args:
        valores: Lista com valores mensais ou agregados
        
    Returns:
        float: Valor máximo (0 se lista vazia)
        
    Exemplo:
        MAXIMO([100, 50, 300]) → 300
    """
    try:
        valores_validos = _coletar_valores_excel(valores)
        if not valores_validos:
            return 0.0
        return float(max(valores_validos))
    except Exception as e:
        print(f"[CALC] Erro em MAXIMO: {e}")
        return 0.0


def DESVIO_PADRAO(valores: List[float]) -> float:
    """
    Calcula o desvio padrão populacional dos valores.

    Args:
        valores: Lista com valores mensais ou agregados

    Returns:
        float: Desvio padrão (0 se lista vazia)
    """
    try:
        valores_validos = _coletar_valores_excel(valores)
        if not valores_validos:
            return 0.0
        return float(np.std(valores_validos, ddof=0))
    except Exception as e:
        print(f"[CALC] Erro em DESVIO_PADRAO: {e}")
        return 0.0


# ============================================================================
# PROCESSAMENTO DE SAZONALIDADE (INTERVALO TEMPORAL)
# ============================================================================

def processar_intervalo_temporal(argumentos_str: str) -> Tuple[str, int]:
    """
    Extrai o código e o intervalo temporal de um argumento com sazonalidade.
    
    Args:
        argumentos_str: String como "TD71; 7" ou "TD72; -7"
        
    Returns:
        Tuple[str, int]: (código, intervalo_temporal)
        - intervalo > 0: próximos N meses (futuro)
        - intervalo < 0: últimos N meses (passado)
        - intervalo = 0: todos os 12 meses
        
    Exemplos:
        "TD71; 7" → ("TD71", 7)
        "TD72; -7" → ("TD72", -7)
        "TD71" → ("TD71", 0)
    """
    # Remover espaços
    argumentos_str = argumentos_str.strip()
    
    # Verificar se tem intervalo temporal (contém ';')
    if ";" in argumentos_str:
        partes = [p.strip() for p in argumentos_str.split(";")]
        
        if len(partes) == 2:
            try:
                codigo = partes[0].strip().upper()
                intervalo = int(partes[1].strip())
                return codigo, intervalo
            except ValueError:
                _log_calc(f"[CALC] ⚠️ Intervalo temporal inválido: {partes[1]}")
                # Fallback: usar apenas o primeiro argumento
                return partes[0].strip().upper(), 0
    
    # Sem intervalo temporal - retornar com intervalo 0
    return argumentos_str.upper(), 0


def aplicar_intervalo_temporal(valores_12_meses: List[float], intervalo: int) -> List[float]:
    """
    Aplica filtro de intervalo temporal aos 12 meses de dados.
    
    Args:
        valores_12_meses: Lista com exatamente 12 valores (jan a dez)
        intervalo: 
            - 0: todos os 12 meses
            - 1 a 12: próximos N meses (a partir de jan)
            - -1 a -12: últimos N meses (meses precedentes)
            
    Returns:
        List[float]: Valores filtrados pelo intervalo
        
    Exemplos:
        valores_12_meses de 12 meses, intervalo=7 → primeiros 7 meses
        valores_12_meses de 12 meses, intervalo=-7 → últimos 7 meses
    """
    if not valores_12_meses or len(valores_12_meses) == 0:
        return []
    
    # Intervalo 0 ou ausente: retornar todos
    if intervalo == 0:
        return valores_12_meses[:12] if len(valores_12_meses) >= 12 else valores_12_meses
    
    # Intervalo positivo: próximos N meses
    if intervalo > 0:
        n_meses = min(abs(intervalo), 12)
        return valores_12_meses[:n_meses]
    
    # Intervalo negativo: últimos N meses
    if intervalo < 0:
        n_meses = min(abs(intervalo), 12)
        return valores_12_meses[-n_meses:] if n_meses > 0 else []
    
    return valores_12_meses[:12]


# ============================================================================
# NOVO SISTEMA: SAZONALIDADE FIXA vs VARIÁVEL
# ============================================================================

def normalizar_sazonalidade(saz: Union[Dict, int, None]) -> Dict:
    """
    Normaliza sazonalidade em cualquier formato a estructura estándar.
    
    Args:
        saz: Dict (nuevo formato), int (legacy), lista com dict, o None
        
    Returns:
        Dict com estructura padrao:
        {
            "tipo": "VARIAVEL" | "FIXO" | "NENHUM",
            "quantidade": int (VARIAVEL),
            "tipo_periodo": "MES" | "ANO" (VARIAVEL),
            "periodoLinha": "PRIMEIRO" | "ULTIMO" (VARIAVEL),
            "mes_inicio": int (FIXO),
            "mes_fim": int (FIXO),
        }
    """
    # Se for None ou 0, sem sazonalidade
    if saz is None or saz == 0 or saz == {}:
        return {"tipo": "NENHUM"}
    
    # Se for lista, tentar extrair primeiro elemento
    if isinstance(saz, list):
        if len(saz) > 0:
            saz = saz[0]  # Pegar primeiro elemento
        else:
            return {"tipo": "NENHUM"}  # Lista vazia
    
    # Após extrair de lista, checar novamente se é vazio
    if saz == {}:
        return {"tipo": "NENHUM"}
    
    # Se for int (legacy: -7 significa últimos 7 meses)
    if isinstance(saz, int):
        if saz == 0:
            return {"tipo": "NENHUM"}
        elif saz < 0:
            # Negativo: últimos N meses
            return {
                "tipo": "VARIAVEL",
                "quantidade": abs(saz),
                "tipo_periodo": "MES",
                "periodoLinha": "ULTIMO",
            }
        else:
            # Positivo: próximos N meses
            return {
                "tipo": "VARIAVEL",
                "quantidade": saz,
                "tipo_periodo": "MES",
                "periodoLinha": "PRIMEIRO",
            }
    
    # Se for dict, retornar como está (já normalizado)
    if isinstance(saz, dict):
        return saz
    
    return {"tipo": "NENHUM"}


def calcular_indices_por_mes(saz_normalizada: Dict, mes_idx: int) -> List[int]:
    """
    Calcula quais índices de meses usar para um mês específico.
    
    ⭐ NOVO: Suporta wrap-around para janeiro (simula dados do ano anterior)
    
    Args:
        saz_normalizada: Dictionário normalizado de sazonalidade
        mes_idx: Índice do mês (0-11, onde 0=Janeiro, 11=Dezembro)
        
    Returns:
        List[int]: Índices dos meses a usar com wrap-around (ex: [5,6,7,8,9,10,11] para jan+últimos7)
        
    Exemplos:
        FIXO jan-jul, mês 5 → [0,1,2,3,4,5,6]
        VARIÁVEL últimos 7, mês 10 (Nov) → [4,5,6,7,8,9,10]
        VARIÁVEL últimos 7, mês 0 (Jan) → [5,6,7,8,9,10,11] ⭐ WRAP-AROUND!
        VARIÁVEL primeiros 3, mês 11 (Dez) → [11,0,1] ⭐ WRAP-AROUND!
    """
    saz_tipo = saz_normalizada.get("tipo", "NENHUM")
    
    # Sem sazonalidade: usar todos os 12 meses
    if saz_tipo == "NENHUM":
        return list(range(12))
    
    # FIXO: sempre usar os mesmos meses
    if saz_tipo == "FIXO":
        mes_inicio = saz_normalizada.get("mes_inicio", 1)
        mes_fim = saz_normalizada.get("mes_fim", 12)
        # Converter para índices (1-based para 0-based)
        inicio_idx = int(mes_inicio) - 1
        fim_idx = int(mes_fim)
        # Range inclusivo: se quer jan-jul, retorna índices 0-6 (7 meses)
        return list(range(inicio_idx, fim_idx))
    
    # VARIÁVEL: adaptar conforme o mês
    if saz_tipo == "VARIAVEL":
        quantidade = saz_normalizada.get("quantidade", 1)
        tipo_periodo = saz_normalizada.get("tipo_periodo", "MES")
        periodoLinha = saz_normalizada.get("periodoLinha", "ULTIMO")
        
        # MES: usar últimos/primeiros N meses
        if tipo_periodo == "MES":
            if periodoLinha == "ULTIMO":
                # Últimos N meses até MÊS_IDX com wrap-around (suporta janeiro!)
                # Para janeiro (mes_idx=0) com quantidade=7: retorna índices [5,6,7,8,9,10,11]
                # Usa modulo 12 para simular "ano anterior" quando necessário
                indices = [(mes_idx - quantidade + 1 + i) % 12 for i in range(quantidade)]
                return indices
            else:  # PRIMEIRO
                # Primeiros N meses a partir de MÊS_IDX com wrap-around
                # Se ultrapassar dezembro, volta para janeiro (ano próximo)
                indices = [(mes_idx + i) % 12 for i in range(quantidade)]
                return indices
        
        # ANO: usar últimos/primeiros N anos (12 meses cada)
        # Para um ano único não faz sentido, então usar últimos 12 meses sempre
        else:  # ANO
            if periodoLinha == "ULTIMO":
                # Últimos 12 meses (o que temos disponível)
                return list(range(12))
            else:  # PRIMEIRO
                return list(range(12))
    
    return list(range(12))


def aplicar_sazonalidade_por_mes(
    valores_12_meses: List[float], 
    saz: Union[Dict, int, None],
    mes_idx: int
) -> List[float]:
    """
    Extrai valores para um mês específico de acordo com sazonalidade.
    
    FIXO: sempre pega os mesmos meses
    VARIÁVEL: adapta conforme o mês atual
    
    Args:
        valores_12_meses: Lista com 12 valores [jan...dez]
        saz: Sazonalidade (dict novo ou int legacy)
        mes_idx: Índice do mês (0-11)
        
    Returns:
        List[float]: Valores filtrados pela sazonalidade para este mês
        
    Exemplos:
        FIXO jan-jul, qualquer mês → [jan_valor, fev_valor, ..., jul_valor]
        VARIÁVEL últimos 7, mês 10 → valores dos índices [4,5,6,7,8,9,10]
    """
    saz_normalizada = normalizar_sazonalidade(saz)
    indices = calcular_indices_por_mes(saz_normalizada, mes_idx)
    
    # Extrair valores pelos índices
    valores_filtrados = [valores_12_meses[i] if i < len(valores_12_meses) else 0.0 for i in indices]
    
    if mes_idx == 0 or mes_idx == 1:
        _log_calc(f"[CALC] Mês {mes_idx}: saz={saz_normalizada}, indices={indices} → retorna {len(valores_filtrados)} valores")
    
    return valores_filtrados


# ============================================================================
# MAPEAMENTO DE FUNÇÕES DISPONÍVEIS
# ============================================================================

FUNCOES_NATIVAS = {
    "SOMA": SOMA,
    "MEDIA": MEDIA,
    "MEDIA_INTERNA": MEDIA_INTERNA,
    "TRIMMEAN": MEDIA_INTERNA,
    "MINIMO": MINIMO,
    "MAXIMO": MAXIMO,
    "DESVIO_PADRAO": DESVIO_PADRAO,
}

DESCRICOES_FUNCOES = {
    "SOMA": "Soma todos os valores (com suporte a intervalo temporal)",
    "MEDIA": "Calcula a média aritmética dos valores (com suporte a intervalo temporal)",
    "MEDIA_INTERNA": "Calcula a média interna estilo Excel/TRIMMEAN, descartando percentuais simétricos dos extremos",
    "TRIMMEAN": "Alias de MEDIA_INTERNA para compatibilidade com a nomenclatura do Excel em inglês",
    "MINIMO": "Encontra o valor mínimo entre os valores (com suporte a intervalo temporal)",
    "MAXIMO": "Encontra o valor máximo entre os valores (com suporte a intervalo temporal)",
    "DESVIO_PADRAO": "Calcula o desvio padrão populacional (com suporte a janela temporal)",
}

EXEMPLOS_FUNCOES = {
    "SOMA": "SOMA(TD71) ou SOMA(TD71; 7)     # Soma dos 12 meses ou próximos 7",
    "MEDIA": "MEDIA(TD71; -7)     # Média dos últimos 7 meses",
    "MEDIA_INTERNA": "MEDIA_INTERNA(TD21; 0.2; -6) # Media interna dos ultimos 6 meses com descarte de 20%",
    "TRIMMEAN": "TRIMMEAN(TD21; 0.2; -6)    # Alias da MEDIA_INTERNA",
    "MINIMO": "MINIMO(TD71; -12)   # Mínimo dos últimos 12 meses (ano anterior)",
    "MAXIMO": "MAXIMO(TD71; 7)     # Máximo dos próximos 7 meses",
    "DESVIO_PADRAO": "DESVIO_PADRAO(TD90; -5; 1) # Desvio dos últimos 5 meses com lag=1",
}


def parse_argumentos_temporais(argumentos_str: str) -> Tuple[List[str], Optional[int], int]:
    """
    Faz parse de argumentos de função com suporte a referências e parâmetros temporais.

    Sintaxe suportada:
    - "TD71"
    - "TD71;TD72;TD87"
    - "TD71:TD90"
    - "IPCA; -3"            (janela)
    - "IPCA; -3; 1"         (janela e lag)

    Returns:
        (referencias, janela, lag)
    """
    partes = [p.strip() for p in __import__("re").split(r"[;,]", argumentos_str) if p.strip()]

    referencias: List[str] = []
    numeros: List[int] = []
    lag = 0

    for parte in partes:
        try:
            numero = int(parte)
            numeros.append(numero)
            continue
        except ValueError:
            pass

        referencias.append(parte.upper())

    if not referencias and partes:
        referencias = [partes[0].upper()]

    janela: Optional[int] = None
    if len(numeros) >= 2:
        janela = numeros[0]
        lag = abs(numeros[1])
    elif len(numeros) == 1:
        if len(referencias) <= 1:
            janela = numeros[0]
        else:
            lag = abs(numeros[0])

    return referencias, janela, lag


def parse_argumentos_media_interna(argumentos_str: str) -> Tuple[List[str], float, Optional[int], int]:
    """
    Faz parse da sintaxe MEDIA_INTERNA(referencia; percentual; janela_opcional; lag_opcional).
    """
    partes = [p.strip() for p in argumentos_str.split(";") if p.strip()]
    if len(partes) < 2:
        raise ValueError("MEDIA_INTERNA requer ao menos referencia e percentual.")

    referencia_bruta = partes[0].upper()
    percentual = float(partes[1].replace(",", "."))

    referencias = [referencia_bruta]
    janela: Optional[int] = None
    lag = 0

    if len(partes) >= 3:
        janela = int(partes[2])
    if len(partes) >= 4:
        lag = abs(int(partes[3]))

    return referencias, percentual, janela, lag


def extrair_janela_por_mes(valores_12_meses: List[float], mes_idx: int, janela: int, lag: int = 0) -> List[float]:
    """
    Helper legado de janela circular de 12 meses.

    Mantido apenas por compatibilidade retroativa; o motor principal agora usa
    `_extrair_janela_historica_por_periodo()` para operar em série histórica real.
    """
    if not valores_12_meses:
        return []

    tamanho = len(valores_12_meses)
    if tamanho == 0:
        return []

    if janela == 0:
        return valores_12_meses[:]

    base_idx = (mes_idx - lag) % 12
    n = min(abs(janela), 12)

    if janela > 0:
        indices = [(base_idx + i) % 12 for i in range(n)]
    else:
        inicio = base_idx - n + 1
        indices = [(inicio + i) % 12 for i in range(n)]

    return [valores_12_meses[i] for i in indices]


# ============================================================================
# PARSER DE ARGUMENTOS DE FUNÇÕES
# ============================================================================

def parse_range_intervalo(intervalo: str, codigos_disponiveis: List[str]) -> List[str]:
    """
    Parse um intervalo de códigos como 'TD71:TD90' ou 'TD71;TD72;TD87'
    
    Args:
        intervalo: String com formato 'TD71:TD90' (intervalo) ou 'TD71;TD72' (separado por ;)
        codigos_disponiveis: Lista de códigos disponíveis na DRE
        
    Returns:
        List[str]: Lista de códigos a processar
        
    Exemplos:
        'TD71:TD90' → ['TD71', 'TD72', ..., 'TD90']
        'TD71;TD72;TD87' → ['TD71', 'TD72', 'TD87']
    """
    
    if ":" in intervalo:
        # Intervalo contínuo: TD71:TD90
        partes = intervalo.split(":")
        if len(partes) != 2:
            return []
        
        cod_inicio = partes[0].strip().upper()
        cod_fim = partes[1].strip().upper()
        
        # Encontrar índices
        try:
            idx_inicio = codigos_disponiveis.index(cod_inicio)
            idx_fim = codigos_disponiveis.index(cod_fim)
            
            start = min(idx_inicio, idx_fim)
            end = max(idx_inicio, idx_fim) + 1
            
            return codigos_disponiveis[start:end]
        except ValueError:
            _log_calc(f"[CALC] Códigos {cod_inicio}:{cod_fim} não encontrados")
            return []
    
    else:
        # Códigos separados por ponto-e-vírgula: TD71;TD72;TD87
        codigos = [c.strip().upper() for c in intervalo.split(";")]
        return [c for c in codigos if c in codigos_disponiveis]


# ============================================================================
# AVALIADOR DE FUNÇÕES (Integração com fórmulas)
# ============================================================================

def _detectar_indices_em_formula(formula: str) -> List[str]:
    """
    Detecta referências de índices econômicos em uma fórmula.
    
    Índices são nomes em UPPERCASE que NÃO são:
    - Códigos de DRE (TD71, MFB, MFBE, etc)
    - Funções nativas (SOMA, MEDIA, etc)
    - Operadores (**, +, -, *, /, (,), etc)
    
    Args:
        formula: String da fórmula (ex: "=MEDIA(TD71) + 0.05*IPCA")
        
    Returns:
        Lista de nomes de índices detectados (ex: ["IPCA"])
    """
    import re
    
    # Padrão: palavra composta por maiúsculas, números, e underscore
    padrao_indices = r'\b([A-Z][A-Z0-9_]*)\b'
    
    # Encontrar todas as palavras em uppercase
    palavras = re.findall(padrao_indices, formula)
    
    # Filtrar palavras que são funções nativas ou códigos DRE conhecidos
    funcoes_nativas_set = set(FUNCOES_NATIVAS.keys())
    
    codigos_dre_conhecidos = {
        "TD71", "TD72", "TD90", "TD91", "TD70", "TD87", "TD88", "TD95", "TD96", "TD97",
        "MFB", "TD11", "TD12", "MFBE", "TD76", "TD16", "TD92", "TD81",
        # Adicionar outros conforme necessário
    }
    
    indices_detectados = []
    for palavra in palavras:
        if (palavra not in funcoes_nativas_set and 
            palavra not in codigos_dre_conhecidos and
            palavra not in ["IF", "ELSE", "THEN", "AND", "OR"]):
            indices_detectados.append(palavra)
    
    # Remover duplicatas mantendo ordem
    indices_detectados = list(dict.fromkeys(indices_detectados))
    
    _log_calc(f"[CALC] Índices detectados na fórmula: {indices_detectados}")
    return indices_detectados


def _carregar_dados_indices_para_12_meses() -> Dict[str, List[float]]:
    """
    Carrega dados de TODOS os índices econômicos e agrega para 12 meses.
    
    Usa as funções de backend para ler índices.
    
    Returns:
        Dicionário {nome_indice: [12_valores]}
        Ex: {"IPCA": [0.48, 0.52, ..., 0.49], "TAXA_SELIC": [...]}
    """
    global _INDICES_12M_CACHE

    if _INDICES_12M_CACHE is not None:
        return _INDICES_12M_CACHE

    ano_referencia = datetime.now().year
    indices_12_meses = {
        nome_indice: _serie_historica_para_12_meses(serie_historica, ano_referencia)
        for nome_indice, serie_historica in _carregar_dados_indices_historicos().items()
    }
    _INDICES_12M_CACHE = indices_12_meses
    return indices_12_meses


def _carregar_dados_indices_historicos() -> Dict[str, List[Dict[str, float]]]:
    """Carrega a série histórica mensal dos índices econômicos disponíveis."""
    global _INDICES_HIST_CACHE

    if _INDICES_HIST_CACHE is not None:
        return _INDICES_HIST_CACHE

    try:
        import sys
        import os

        backend_path = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)

        from database import obter_lista_indices_disponiveis, obter_indices_por_nome

        indices_historicos: Dict[str, List[Dict[str, float]]] = {}
        for nome_indice in obter_lista_indices_disponiveis():
            try:
                registros = obter_indices_por_nome(nome_indice) or []
                agrupado: Dict[Tuple[int, int], List[float]] = {}
                for registro in registros:
                    dt_alvo = registro.get("DT_ALVO")
                    vl_pjtd = registro.get("VL_PJTD", 0.0)
                    if dt_alvo is None:
                        continue
                    try:
                        data_obj = pd.to_datetime(dt_alvo)
                        valor = float(vl_pjtd or 0.0)
                    except Exception:
                        continue
                    chave = (int(data_obj.year), int(data_obj.month))
                    agrupado.setdefault(chave, []).append(valor)

                indices_historicos[nome_indice] = [
                    {
                        "ano": ano,
                        "mes": mes,
                        "valor": float(np.mean(valores)) if valores else 0.0,
                    }
                    for (ano, mes), valores in sorted(agrupado.items())
                ]
            except Exception as e:
                _log_calc(f"[CALC] Erro ao carregar histórico do índice {nome_indice}: {e}")

        _INDICES_HIST_CACHE = indices_historicos
        return indices_historicos

    except Exception as e:
        _log_calc(f"[CALC] Erro ao carregar índices históricos: {e}")
        return {}


def _preparar_contexto_com_indices(dre_dados: Dict) -> Dict:
    """
    Prepara contexto completo com variáveis DRE + índices econômicos.
    
    Para cada índice, cria entrada no contexto com 12 valores mensais.
    
    Args:
        dre_dados: Dicionário com dados da DRE
        
    Returns:
        Dicionário estendido com {**dre_dados, IPCA: [...], TAXA_SELIC: [...], ...}
    """
    contexto = dict(dre_dados)
    ano_referencia = _obter_ano_referencia(contexto)

    for nome_indice, serie_historica in _carregar_dados_indices_historicos().items():
        # Normalizar nome do índice (remover caracteres especiais)
        chave_contexto = nome_indice.upper().replace("-", "_").replace(" ", "_")
        
        contexto[chave_contexto] = {
            "tipo": "indice_economico",
            "valores": _serie_historica_para_12_meses(serie_historica, ano_referencia),
            "nome": nome_indice,
            "serie_historica": serie_historica,
        }
        
        _log_calc(f"[CALC] Índice adicionado ao contexto: {chave_contexto}")

    contexto["__meta__"] = {
        **(contexto.get("__meta__", {}) if isinstance(contexto.get("__meta__"), dict) else {}),
        "ano_referencia": ano_referencia,
    }

    return contexto


def evaluar_funcao_em_formula(nome_funcao: str, argumentos: str, 
                             dre_dados: Dict, mes_idx: int = None,
                             incluir_indices: bool = True) -> float:
    """
    Avalia uma função nativa dentro de uma fórmula de metodologia com suporte a sazonalidade e índices.
    
    ✨ NOVO: Suporta referências a índices econômicos nos argumentos
    
    Args:
        nome_funcao: Nome da função ('SOMA', 'MEDIA', etc)
        argumentos: String com argumentos com ou sem intervalo temporal
                   Ex: 'TD71' ou 'TD71; 7' ou 'IPCA' ou 'IPCA; -7'
        dre_dados: Dicionário com dados da DRE
        mes_idx: Índice do mês (0-11) se aplicável, None para valor agregado
        incluir_indices: Se True, permite referências a índices econômicos
        
    Returns:
        float: Valor calculado
        
    Exemplos:
        evaluar_funcao_em_formula('SOMA', 'TD71', dre_dados) → soma 12 meses
        evaluar_funcao_em_formula('SOMA', 'IPCA', dre_dados, incluir_indices=True) → soma 12 meses de IPCA
        evaluar_funcao_em_formula('MEDIA', 'IPCA; -7', dre_dados, incluir_indices=True) → média últimos 7 meses
    """
    
    nome_funcao_upper = nome_funcao.upper()
    if nome_funcao_upper not in FUNCOES_NATIVAS:
        _log_calc(f"[CALC] Função desconhecida: {nome_funcao}")
        return 0.0
    
    try:
        # ✨ Preparar contexto com índices se permitido
        contexto = _preparar_contexto_com_indices(dre_dados) if incluir_indices else dre_dados
        
        percentual = None
        janela = None
        lag = 0
        ano_referencia = _obter_ano_referencia(contexto)
        if nome_funcao_upper in {"MEDIA_INTERNA", "TRIMMEAN"}:
            referencias, percentual, janela, lag = parse_argumentos_media_interna(argumentos.strip())
            codigo_str = referencias[0]
            intervalo_temporal = janela or 0
        else:
            # ===== ETAPA 1: Extrair código e intervalo temporal =====
            codigo_str, intervalo_temporal = processar_intervalo_temporal(argumentos.strip())
        
        _log_calc(f"[CALC] {nome_funcao}({argumentos})")
        _log_calc(f"[CALC]  → Código: {codigo_str}, Intervalo: {intervalo_temporal}")
        
        # ===== ETAPA 2: Obter lista de códigos a processar =====
        codigos_disponiveis = list(contexto.keys())
        
        # Detectar se é intervalo de códigos (TD71:TD90) ou apenas um código
        if ":" in codigo_str:
            # Intervalo de códigos
            codigos_a_usar = parse_range_intervalo(codigo_str, codigos_disponiveis)
        else:
            # Código único
            if codigo_str in codigos_disponiveis:
                codigos_a_usar = [codigo_str]
            else:
                _log_calc(f"[CALC] Código '{codigo_str}' não encontrado")
                return 0.0
        
        if not codigos_a_usar:
            _log_calc(f"[CALC] Nenhum código válido encontrado em: {codigo_str}")
            return 0.0
        
        # ===== ETAPA 3: Coletar valores com filtro temporal =====
        valores_para_funcao = []
        mes_base = (mes_idx + 1) if mes_idx is not None else 12
        
        for codigo in codigos_a_usar:
            if codigo in contexto:
                item_contexto = contexto[codigo]

                if mes_idx is not None and intervalo_temporal:
                    valores_filtrados = _extrair_janela_historica_por_periodo(
                        item_contexto,
                        ano_referencia,
                        mes_base,
                        janela=intervalo_temporal,
                        lag=lag,
                        ano_referencia=ano_referencia,
                    )
                    valores_para_funcao.extend(valores_filtrados)
                elif mes_idx is not None and lag:
                    ano_lag, mes_lag = _ordem_para_periodo(
                        _periodo_para_ordem(ano_referencia, mes_base) - lag
                    )
                    valores_para_funcao.append(
                        _obter_valor_historico(item_contexto, ano_lag, mes_lag, ano_referencia, mes_lag - 1)
                    )
                elif mes_idx is not None:
                    valores_para_funcao.append(
                        _obter_valor_historico(item_contexto, ano_referencia, mes_base, ano_referencia, mes_base - 1)
                    )
                else:
                    valores_para_funcao.extend(
                        [
                            _obter_valor_historico(
                                item_contexto,
                                ano_referencia,
                                mes_cursor,
                                ano_referencia,
                                mes_cursor - 1,
                            )
                            for mes_cursor in range(1, 13)
                        ]
                    )
        
        # ===== ETAPA 4: Executar a função =====
        funcao = FUNCOES_NATIVAS[nome_funcao_upper]
        if nome_funcao_upper in {"MEDIA_INTERNA", "TRIMMEAN"}:
            resultado = funcao(valores_para_funcao, percentual)
        else:
            resultado = funcao(valores_para_funcao)
        
        _log_calc(f"[CALC]  → Resultado: {resultado}")
        
        return resultado
        
    except Exception as e:
        _log_calc(f"[CALC] ❌ Erro ao avaliar {nome_funcao}({argumentos}): {e}")
        return 0.0


def evaluar_funcao_dinamica_por_mes(
    nome_funcao: str, 
    argumentos: str, 
    dre_dados: Dict,
    saz: Union[Dict, int, None] = None,
    incluir_indices: bool = True,
    linha_destino_codigo: Optional[str] = None,
) -> List[float]:
    """
    Avalia uma função de forma DINÂMICA para cada mês (com sazonalidade e índices).
    
    ✨ NOVO: Suporta referências a índices econômicos
    
    Este é o novo fluxo que calcula diferentes valores para cada mês,
    em vez de calcular uma única vez e reutilizar.
    
    Args:
        nome_funcao: Nome da função ('SOMA', 'MEDIA', etc)
        argumentos: String com argumentos (ex: 'TD71' ou 'TD71:TD90' ou 'IPCA')
                    NOTA: argumentos NÃO incluem o intervalo temporal aqui
        dre_dados: Dicionário com dados da DRE
        saz: Sazonalidade (dict novo, int legacy, ou None)
        incluir_indices: Se True, permite referências a índices econômicos
        
    Returns:
        List[float]: 12 valores, um para cada mês, calculados dinamicamente
        
    Exemplos:
        # Para cada mês, calcula a média dos últimos 7 meses daquele mês
        evaluar_funcao_dinamica_por_mes('MEDIA', 'TD71', dre_dados, 
                                        {tipo: VARIAVEL, quantidade: 7, ...})
        
        # Para cada mês, sempre usa os meses jan-jul (sazonalidade fixa)
        evaluar_funcao_dinamica_por_mes('SOMA', 'TD71', dre_dados,
                                        {tipo: FIXO, mes_inicio: 1, mes_fim: 7})
        
        # Para cada mês, calcula a média dos últimos 3 meses do IPCA
        evaluar_funcao_dinamica_por_mes('MEDIA', 'IPCA', dre_dados,
                                        {tipo: VARIAVEL, quantidade: 3, ...},
                                        incluir_indices=True)
    """
    nome_funcao_upper = nome_funcao.upper()
    if nome_funcao_upper not in FUNCOES_NATIVAS:
        _log_calc(f"[CALC] Função desconhecida: {nome_funcao}")
        return [0.0] * 12
    
    # ✨ Preparar contexto com índices se permitido
    contexto = _preparar_contexto_com_indices(dre_dados) if incluir_indices else dre_dados
    
    # Normalizar sazonalidade
    saz_normalizada = normalizar_sazonalidade(saz)
    
    _log_calc(f"[CALC] {nome_funcao}({argumentos}) - Sazonalidade: {saz_normalizada}")
    
    valores_resultado_12_meses = []
    
    percentual = None
    if nome_funcao_upper in {"MEDIA_INTERNA", "TRIMMEAN"}:
        referencias, percentual, janela, lag = parse_argumentos_media_interna(argumentos)
    else:
        referencias, janela, lag = parse_argumentos_temporais(argumentos)

    ano_referencia = _obter_ano_referencia(contexto)

    # Para cada um dos 12 meses
    for mes_idx in range(12):
        try:
            # ===== ETAPA 1: Obter lista de códigos =====
            codigos_disponiveis = list(contexto.keys())
            codigos_a_usar: List[str] = []

            for ref in referencias:
                if ":" in ref:
                    codigos_a_usar.extend(parse_range_intervalo(ref, codigos_disponiveis))
                elif ref in codigos_disponiveis:
                    codigos_a_usar.append(ref)
                else:
                    _log_calc(f"[CALC] Referência '{ref}' não encontrada (mês {mes_idx})")
            
            if not codigos_a_usar:
                _log_calc(f"[CALC] Nenhum código válido em {argumentos} (mês {mes_idx})")
                valores_resultado_12_meses.append(0.0)
                continue
            
            # Remover duplicatas preservando ordem
            codigos_a_usar = list(dict.fromkeys(codigos_a_usar))

            # ===== ETAPA 2: Aplicar sazonalidade/janela e coletar valores =====
            valores_para_funcao = []
            
            for codigo in codigos_a_usar:
                if codigo in contexto:
                    item_contexto = contexto[codigo]
                    ano_base = ano_referencia
                    mes_base = mes_idx + 1

                    if (
                        linha_destino_codigo
                        and codigo == linha_destino_codigo
                        and mes_base > 1
                        and valores_resultado_12_meses
                    ):
                        item_contexto = _aplicar_resultados_parciais_na_referencia(
                            item_contexto,
                            valores_resultado_12_meses,
                            ano_referencia=ano_referencia,
                            ate_mes_exclusivo=mes_base,
                        )

                    if (
                        linha_destino_codigo
                        and codigo == linha_destino_codigo
                        and mes_base > 1
                        and valores_resultado_12_meses
                    ):
                        item_contexto = _aplicar_resultados_parciais_na_referencia(
                            item_contexto,
                            valores_resultado_12_meses,
                            ano_referencia=ano_referencia,
                            ate_mes_exclusivo=mes_base,
                        )

                    if janela is not None:
                        valores_filtrados = _extrair_janela_historica_por_periodo(
                            item_contexto,
                            ano_base,
                            mes_base,
                            janela=janela,
                            lag=lag,
                            ano_referencia=ano_referencia,
                        )
                    elif lag:
                        ano_lag, mes_lag = _ordem_para_periodo(
                            _periodo_para_ordem(ano_base, mes_base) - lag
                        )
                        valores_filtrados = [
                            _obter_valor_historico(
                                item_contexto,
                                ano_lag,
                                mes_lag,
                                ano_referencia,
                                mes_lag - 1,
                            )
                        ]
                    elif saz_normalizada.get("tipo") != "NENHUM":
                        valores_filtrados = _extrair_sazonalidade_historica(
                            item_contexto,
                            saz,
                            ano_base,
                            mes_base,
                            ano_referencia=ano_referencia,
                        )
                    else:
                        valores_filtrados = [
                            _obter_valor_historico(
                                item_contexto,
                                ano_base,
                                mes_base,
                                ano_referencia,
                                mes_idx,
                            )
                        ]

                    valores_para_funcao.extend(valores_filtrados)
            
            # ===== ETAPA 3: Executar função =====
            funcao = FUNCOES_NATIVAS[nome_funcao_upper]
            if nome_funcao_upper in {"MEDIA_INTERNA", "TRIMMEAN"}:
                valor_mes = funcao(valores_para_funcao, percentual)
            else:
                valor_mes = funcao(valores_para_funcao)
            valores_resultado_12_meses.append(float(valor_mes))
            
            if mes_idx == 0 or mes_idx == 6 or mes_idx == 11:
                _log_calc(f"[CALC]  → Mês {mes_idx+1}: {valor_mes:.2f}")
                
        except Exception as e:
            _log_calc(f"[CALC] ❌ Erro em {nome_funcao}({argumentos}) mês {mes_idx}: {e}")
            valores_resultado_12_meses.append(0.0)
    
    _log_calc(f"[CALC]  → Resultado final (12 meses): {valores_resultado_12_meses[:3]}...")
    return valores_resultado_12_meses


# ============================================================================
# HELPERS PARA DOCUMENTAÇÃO
# ============================================================================

def obter_documentacao_funcoes() -> str:
    """
    Retorna documentação formatada de todas as funções nativas.
    
    Returns:
        str: Markdown com documentação
    """
    doc = "### 📚 Funções Nativas Disponíveis\n\n"
    
    for nome in FUNCOES_NATIVAS.keys():
        doc += f"#### **{nome}()**\n"
        doc += f"- **Descrição:** {DESCRICOES_FUNCOES.get(nome, 'N/A')}\n"
        doc += f"- **Sintaxe:** `{EXEMPLOS_FUNCOES.get(nome, 'N/A')}`\n\n"
    
    return doc
