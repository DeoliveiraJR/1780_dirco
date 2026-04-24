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

Sintaxe com Sazonalidade (Intervalo Temporal):
    SOMA(TD71; 7)           # Soma dos PRÓXIMOS 7 meses de TD71 (a partir de agora)
    MEDIA(TD72; -7)         # Média dos ÚLTIMOS 7 meses de TD72 (meses passados)
    MINIMO(TD71; -12)       # Valor mínimo dos últimos 12 meses (ano anterior)

Novo Sistema de Sazonalidade (Fixo vs Variável):
    FIXO: Mesmo período para todos os meses
        {tipo: FIXO, mes_inicio: 1, mes_fim: 7}  → Always Jan-Jul
    VARIÁVEL: Período móvel por mês
        {tipo: VARIAVEL, quantidade: 7, tipo_periodo: MES, periodoLinha: ULTIMO}
        → Cada mês calcula seus últimos 7 meses
"""

import numpy as np
from typing import Dict, List, Union, Tuple, Optional


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
        return float(sum(v for v in valores if isinstance(v, (int, float))))
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
        valores_validos = [v for v in valores if isinstance(v, (int, float))]
        if not valores_validos:
            return 0.0
        return float(sum(valores_validos) / len(valores_validos))
    except Exception as e:
        print(f"[CALC] Erro em MEDIA: {e}")
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
        valores_validos = [v for v in valores if isinstance(v, (int, float))]
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
        valores_validos = [v for v in valores if isinstance(v, (int, float))]
        if not valores_validos:
            return 0.0
        return float(max(valores_validos))
    except Exception as e:
        print(f"[CALC] Erro em MAXIMO: {e}")
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
                print(f"[CALC] ⚠️ Intervalo temporal inválido: {partes[1]}")
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
        print(f"[CALC] Mês {mes_idx}: saz={saz_normalizada}, indices={indices} → retorna {len(valores_filtrados)} valores")
    
    return valores_filtrados


# ============================================================================
# MAPEAMENTO DE FUNÇÕES DISPONÍVEIS
# ============================================================================

FUNCOES_NATIVAS = {
    "SOMA": SOMA,
    "MEDIA": MEDIA,
    "MINIMO": MINIMO,
    "MAXIMO": MAXIMO,
}

DESCRICOES_FUNCOES = {
    "SOMA": "Soma todos os valores (com suporte a intervalo temporal)",
    "MEDIA": "Calcula a média aritmética dos valores (com suporte a intervalo temporal)",
    "MINIMO": "Encontra o valor mínimo entre os valores (com suporte a intervalo temporal)",
    "MAXIMO": "Encontra o valor máximo entre os valores (com suporte a intervalo temporal)",
}

EXEMPLOS_FUNCOES = {
    "SOMA": "SOMA(TD71) ou SOMA(TD71; 7)     # Soma dos 12 meses ou próximos 7",
    "MEDIA": "MEDIA(TD71; -7)     # Média dos últimos 7 meses",
    "MINIMO": "MINIMO(TD71; -12)   # Mínimo dos últimos 12 meses (ano anterior)",
    "MAXIMO": "MAXIMO(TD71; 7)     # Máximo dos próximos 7 meses",
}


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
            print(f"[CALC] Códigos {cod_inicio}:{cod_fim} não encontrados")
            return []
    
    else:
        # Códigos separados por ponto-e-vírgula: TD71;TD72;TD87
        codigos = [c.strip().upper() for c in intervalo.split(";")]
        return [c for c in codigos if c in codigos_disponiveis]


# ============================================================================
# AVALIADOR DE FUNÇÕES (Integração com fórmulas)
# ============================================================================

def evaluar_funcao_em_formula(nome_funcao: str, argumentos: str, 
                             dre_dados: Dict, mes_idx: int = None) -> float:
    """
    Avalia uma função nativa dentro de uma fórmula de metodologia com suporte a sazonalidade.
    
    Args:
        nome_funcao: Nome da função ('SOMA', 'MEDIA', etc)
        argumentos: String com argumentos com ou sem intervalo temporal
                   Ex: 'TD71' ou 'TD71; 7' ou 'TD71; -7'
        dre_dados: Dicionário com dados da DRE
        mes_idx: Índice do mês (0-11) se aplicável, None para valor agregado
        
    Returns:
        float: Valor calculado
        
    Exemplos:
        evaluar_funcao_em_formula('SOMA', 'TD71', dre_dados) → soma 12 meses
        evaluar_funcao_em_formula('SOMA', 'TD71; 7', dre_dados) → soma próximos 7 meses
        evaluar_funcao_em_formula('MEDIA', 'TD72; -7', dre_dados) → média dos últimos 7 meses
    """
    
    if nome_funcao.upper() not in FUNCOES_NATIVAS:
        print(f"[CALC] Função desconhecida: {nome_funcao}")
        return 0.0
    
    try:
        # ===== ETAPA 1: Extrair código e intervalo temporal =====
        codigo_str, intervalo_temporal = processar_intervalo_temporal(argumentos.strip())
        
        print(f"[CALC] {nome_funcao}({argumentos})")
        print(f"[CALC]  → Código: {codigo_str}, Intervalo: {intervalo_temporal}")
        
        # ===== ETAPA 2: Obter lista de códigos a processar =====
        codigos_disponiveis = list(dre_dados.keys())
        
        # Detectar se é intervalo de códigos (TD71:TD90) ou apenas um código
        if ":" in codigo_str:
            # Intervalo de códigos
            codigos_a_usar = parse_range_intervalo(codigo_str, codigos_disponiveis)
        else:
            # Código único
            if codigo_str in codigos_disponiveis:
                codigos_a_usar = [codigo_str]
            else:
                print(f"[CALC] Código '{codigo_str}' não encontrado")
                return 0.0
        
        if not codigos_a_usar:
            print(f"[CALC] Nenhum código válido encontrado em: {codigo_str}")
            return 0.0
        
        # ===== ETAPA 3: Coletar valores com filtro temporal =====
        valores_para_funcao = []
        
        for codigo in codigos_a_usar:
            if codigo in dre_dados:
                valores_var = dre_dados[codigo].get("valores", [0.0] * 12)
                
                # Aplicar filtro temporal
                valores_filtrados = aplicar_intervalo_temporal(valores_var, intervalo_temporal)
                
                if mes_idx is not None and mes_idx < len(valores_filtrados):
                    # Se especificou mês, usar valor daquele mês
                    valores_para_funcao.append(valores_filtrados[mes_idx])
                else:
                    # Senão, agregar todos os valores filtrados
                    valores_para_funcao.extend(valores_filtrados)
        
        # ===== ETAPA 4: Executar a função =====
        funcao = FUNCOES_NATIVAS[nome_funcao.upper()]
        resultado = funcao(valores_para_funcao)
        
        print(f"[CALC]  → Resultado: {resultado}")
        
        return resultado
        
    except Exception as e:
        print(f"[CALC] ❌ Erro ao avaliar {nome_funcao}({argumentos}): {e}")
        import traceback
        traceback.print_exc()
        return 0.0


def evaluar_funcao_dinamica_por_mes(
    nome_funcao: str, 
    argumentos: str, 
    dre_dados: Dict,
    saz: Union[Dict, int, None] = None
) -> List[float]:
    """
    Avalia uma função de forma DINÂMICA para cada mês (com sazonalidade).
    
    Este é o novo fluxo que calcula diferentes valores para cada mês,
    em vez de calcular uma única vez e reutilizar.
    
    Args:
        nome_funcao: Nome da função ('SOMA', 'MEDIA', etc)
        argumentos: String com argumentos (ex: 'TD71' ou 'TD71:TD90')
                    NOTA: argumentos NÃO incluem o intervalo temporal aqui
        dre_dados: Dicionário com dados da DRE
        saz: Sazonalidade (dict novo, int legacy, ou None)
        
    Returns:
        List[float]: 12 valores, um para cada mês, calculados dinamicamente
        
    Exemplos:
        # Para cada mês, calcula a média dos últimos 7 meses daquele mês
        evaluar_funcao_dinamica_por_mes('MEDIA', 'TD71', dre_dados, 
                                        {tipo: VARIAVEL, quantidade: 7, ...})
        
        # Para cada mês, sempre usa os meses jan-jul (sazonalidade fixa)
        evaluar_funcao_dinamica_por_mes('SOMA', 'TD71', dre_dados,
                                        {tipo: FIXO, mes_inicio: 1, mes_fim: 7})
    """
    if nome_funcao.upper() not in FUNCOES_NATIVAS:
        print(f"[CALC] Função desconhecida: {nome_funcao}")
        return [0.0] * 12
    
    # Normalizar sazonalidade
    saz_normalizada = normalizar_sazonalidade(saz)
    
    print(f"[CALC] {nome_funcao}({argumentos}) - Sazonalidade: {saz_normalizada}")
    
    valores_resultado_12_meses = []
    
    # Para cada um dos 12 meses
    for mes_idx in range(12):
        try:
            # ===== ETAPA 1: Extrair código =====
            codigo_str = argumentos.strip()
            
            # ===== ETAPA 2: Obter lista de códigos =====
            codigos_disponiveis = list(dre_dados.keys())
            
            if ":" in codigo_str:
                codigos_a_usar = parse_range_intervalo(codigo_str, codigos_disponiveis)
            else:
                if codigo_str in codigos_disponiveis:
                    codigos_a_usar = [codigo_str]
                else:
                    print(f"[CALC] Código '{codigo_str}' não encontrado (mês {mes_idx})")
                    valores_resultado_12_meses.append(0.0)
                    continue
            
            if not codigos_a_usar:
                print(f"[CALC] Nenhum código válido em {codigo_str} (mês {mes_idx})")
                valores_resultado_12_meses.append(0.0)
                continue
            
            # ===== ETAPA 3: Aplicar sazonalidade e coletar valores =====
            valores_para_funcao = []
            
            for codigo in codigos_a_usar:
                if codigo in dre_dados:
                    valores_var = dre_dados[codigo].get("valores", [0.0] * 12)
                    
                    # 🔑 NOVO: Aplicar sazonalidade dinamicamente por mês
                    valores_filtrados = aplicar_sazonalidade_por_mes(
                        valores_var, 
                        saz, 
                        mes_idx
                    )
                    
                    valores_para_funcao.extend(valores_filtrados)
            
            # ===== ETAPA 4: Executar função =====
            funcao = FUNCOES_NATIVAS[nome_funcao.upper()]
            valor_mes = funcao(valores_para_funcao)
            valores_resultado_12_meses.append(float(valor_mes))
            
            if mes_idx == 0 or mes_idx == 6 or mes_idx == 11:
                print(f"[CALC]  → Mês {mes_idx+1}: {valor_mes:.2f}")
                
        except Exception as e:
            print(f"[CALC] ❌ Erro em {nome_funcao}({argumentos}) mês {mes_idx}: {e}")
            valores_resultado_12_meses.append(0.0)
    
    print(f"[CALC]  → Resultado final (12 meses): {valores_resultado_12_meses[:3]}...")
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
