"""
Módulo de Funções de Cálculo Nativas para DRE Gerencial

Implementa funções de cálculo semelhantes ao Excel para uso em fórmulas de metodologias:
- SOMA: Soma todos os valores
- MEDIA: Calcula a média aritmética
- MINIMO: Encontra o valor mínimo
- MAXIMO: Encontra o valor máximo

Sintaxe:
    SOMA(TD71)              # Soma os 12 meses de TD71
    MEDIA(TD71;TD72)        # Média dos valores de TD71 e TD72 combinados
    MINIMO(TD71:TD90)       # Valor mínimo entre TD71 e TD90 (intervalo)
    MAXIMO(TD71;TD72;TD87)  # Valor máximo dos códigos especificados
"""

import numpy as np
from typing import Dict, List, Union


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
# MAPEAMENTO DE FUNÇÕES DISPONÍVEIS
# ============================================================================

FUNCOES_NATIVAS = {
    "SOMA": SOMA,
    "MEDIA": MEDIA,
    "MINIMO": MINIMO,
    "MAXIMO": MAXIMO,
}

DESCRICOES_FUNCOES = {
    "SOMA": "Soma todos os valores de uma variável ou intervalo",
    "MEDIA": "Calcula a média aritmética dos valores",
    "MINIMO": "Encontra o valor mínimo entre os valores",
    "MAXIMO": "Encontra o valor máximo entre os valores",
}

EXEMPLOS_FUNCOES = {
    "SOMA": "SOMA(TD71)     # Soma os 12 meses de TD71",
    "MEDIA": "MEDIA(TD71;TD72)    # Média de TD71 e TD72",
    "MINIMO": "MINIMO(TD71:TD90)   # Mínimo entre TD71 e TD90",
    "MAXIMO": "MAXIMO(TD71;TD72;TD87)   # Máximo entre essas variáveis",
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
    Avalia uma função nativa dentro de uma fórmula de metodologia.
    Pode retornar um valor único ou uma lista de 12 valores.
    
    Args:
        nome_funcao: Nome da função ('SOMA', 'MEDIA', etc)
        argumentos: String com argumentos ('TD71' ou 'TD71;TD72' ou 'TD71:TD90')
        dre_dados: Dicionário com dados da DRE
        mes_idx: Índice do mês (0-11) se aplicável, None para valor agregado
        
    Returns:
        float: Valor calculado
        
    Exemplo:
        evaluar_funcao_em_formula('SOMA', 'TD71', dre_dados)
        → Retorna a soma dos 12 meses de TD71
    """
    
    if nome_funcao.upper() not in FUNCOES_NATIVAS:
        print(f"[CALC] Função desconhecida: {nome_funcao}")
        return 0.0
    
    try:
        # Obter lista de códigos a processar
        codigos_disponiveis = list(dre_dados.keys())
        codigos_a_usar = parse_range_intervalo(argumentos.strip(), codigos_disponiveis)
        
        if not codigos_a_usar:
            print(f"[CALC] Nenhum código válido encontrado em: {argumentos}")
            return 0.0
        
        # Coletar valores
        valores_para_funcao = []
        
        for codigo in codigos_a_usar:
            if codigo in dre_dados:
                valores_var = dre_dados[codigo].get("valores", [0.0] * 12)
                
                if mes_idx is not None and mes_idx < len(valores_var):
                    # Se especificou mês, usar valor daquele mês
                    valores_para_funcao.append(valores_var[mes_idx])
                else:
                    # Senão, agregar todos os 12 meses
                    valores_para_funcao.extend(valores_var)
        
        # Executar a função
        funcao = FUNCOES_NATIVAS[nome_funcao.upper()]
        resultado = funcao(valores_para_funcao)
        
        print(f"[CALC] {nome_funcao}({argumentos}) = {resultado}")
        
        return resultado
        
    except Exception as e:
        print(f"[CALC] Erro ao avaliar {nome_funcao}({argumentos}): {e}")
        return 0.0


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
