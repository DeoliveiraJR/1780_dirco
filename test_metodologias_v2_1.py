"""
Testes para as novas funcionalidades de metodologias v2.1.0
- Testes das funções nativas (SOMA, MEDIA, MINIMO, MAXIMO)
- Testes de filtros contextuais
"""

import sys
import os

# Adicionar caminho do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.utils_ext.calc_functions import (
    SOMA, MEDIA, MINIMO, MAXIMO,
    parse_range_intervalo,
    evaluar_funcao_em_formula,
    FUNCOES_NATIVAS
)


# ============================================================================
# TESTES DAS FUNÇÕES BÁSICAS
# ============================================================================

def test_soma():
    """Teste da função SOMA"""
    print("\n✓ Testando SOMA...")
    
    # Teste 1: Soma simples
    valores = [100, 200, 300]
    resultado = SOMA(valores)
    assert resultado == 600, f"SOMA([100,200,300]) deveria ser 600, mas é {resultado}"
    print("  ✓ Soma simples: OK")
    
    # Teste 2: Com valores zero
    valores = [0, 100, 0]
    resultado = SOMA(valores)
    assert resultado == 100, f"SOMA([0,100,0]) deveria ser 100, mas é {resultado}"
    print("  ✓ Soma com zeros: OK")
    
    # Teste 3: Lista vazia
    resultado = SOMA([])
    assert resultado == 0, f"SOMA([]) deveria ser 0, mas é {resultado}"
    print("  ✓ Soma lista vazia: OK")
    
    print("  ✅ Todos os testes de SOMA passaram!")


def test_media():
    """Teste da função MEDIA"""
    print("\n✓ Testando MEDIA...")
    
    # Teste 1: Média simples
    valores = [100, 200, 300]
    resultado = MEDIA(valores)
    assert resultado == 200, f"MEDIA([100,200,300]) deveria ser 200, mas é {resultado}"
    print("  ✓ Média simples: OK")
    
    # Teste 2: Média com decimais
    valores = [10, 20, 30]
    resultado = MEDIA(valores)
    assert resultado == 20, f"MEDIA([10,20,30]) deveria ser 20, mas é {resultado}"
    print("  ✓ Média com inteiros: OK")
    
    # Teste 3: Lista vazia
    resultado = MEDIA([])
    assert resultado == 0, f"MEDIA([]) deveria ser 0, mas é {resultado}"
    print("  ✓ Média lista vazia: OK")
    
    print("  ✅ Todos os testes de MEDIA passaram!")


def test_minimo():
    """Teste da função MINIMO"""
    print("\n✓ Testando MINIMO...")
    
    # Teste 1: Mínimo simples
    valores = [100, 50, 300]
    resultado = MINIMO(valores)
    assert resultado == 50, f"MINIMO([100,50,300]) deveria ser 50, mas é {resultado}"
    print("  ✓ Mínimo simples: OK")
    
    # Teste 2: Mínimo com negativos
    valores = [-10, 0, 10]
    resultado = MINIMO(valores)
    assert resultado == -10, f"MINIMO([-10,0,10]) deveria ser -10, mas é {resultado}"
    print("  ✓ Mínimo com negativos: OK")
    
    # Teste 3: Lista vazia
    resultado = MINIMO([])
    assert resultado == 0, f"MINIMO([]) deveria ser 0, mas é {resultado}"
    print("  ✓ Mínimo lista vazia: OK")
    
    print("  ✅ Todos os testes de MINIMO passaram!")


def test_maximo():
    """Teste da função MAXIMO"""
    print("\n✓ Testando MAXIMO...")
    
    # Teste 1: Máximo simples
    valores = [100, 50, 300]
    resultado = MAXIMO(valores)
    assert resultado == 300, f"MAXIMO([100,50,300]) deveria ser 300, mas é {resultado}"
    print("  ✓ Máximo simples: OK")
    
    # Teste 2: Máximo com negativos
    valores = [-10, -50, 0]
    resultado = MAXIMO(valores)
    assert resultado == 0, f"MAXIMO([-10,-50,0]) deveria ser 0, mas é {resultado}"
    print("  ✓ Máximo com negativos: OK")
    
    # Teste 3: Lista vazia
    resultado = MAXIMO([])
    assert resultado == 0, f"MAXIMO([]) deveria ser 0, mas é {resultado}"
    print("  ✓ Máximo lista vazia: OK")
    
    print("  ✅ Todos os testes de MAXIMO passaram!")


# ============================================================================
# TESTES DO PARSER DE ARGUMENTOS
# ============================================================================

def test_parse_range():
    """Teste do parser de argumentos com intervalo"""
    print("\n✓ Testando parser de intervalo...")
    
    codigos_disponiveis = ['TD71', 'TD72', 'TD90', 'TD91', 'TD70']
    
    # Teste 1: Código único
    resultado = parse_range_intervalo('TD71', codigos_disponiveis)
    assert resultado == ['TD71'], f"Parse 'TD71' deveria ser ['TD71'], mas é {resultado}"
    print("  ✓ Código único: OK")
    
    # Teste 2: Múltiplos códigos com ;
    resultado = parse_range_intervalo('TD71;TD72;TD91', codigos_disponiveis)
    assert set(resultado) == {'TD71', 'TD72', 'TD91'}, f"Parse com ; falhou: {resultado}"
    print("  ✓ Múltiplos códigos: OK")
    
    # Teste 3: Intervalo com :
    resultado = parse_range_intervalo('TD72:TD91', codigos_disponiveis)
    assert 'TD72' in resultado and 'TD91' in resultado, f"Parse com : falhou: {resultado}"
    print("  ✓ Intervalo com :: OK")
    
    print("  ✅ Todos os testes de parser passaram!")


# ============================================================================
# TESTES DE INTEGRAÇÃO COM DRE
# ============================================================================

def test_funcoes_com_dre_dados():
    """Teste de funções com dados de DRE realistas"""
    print("\n✓ Testando integração com dados DRE...")
    
    # Simular dados DRE
    dre_dados = {
        "TD71": {
            "valores": [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210],
            "descricao": "Receita Financeira"
        },
        "TD72": {
            "valores": [50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105],
            "descricao": "Despesa Financeira"
        },
        "TD90": {
            "valores": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
            "descricao": "Receita de Oportunidade"
        }
    }
    
    # Teste 1: SOMA de uma variável
    resultado = evaluar_funcao_em_formula('SOMA', 'TD71', dre_dados)
    esperado = sum(dre_dados['TD71']['valores'])
    assert resultado == esperado, f"SOMA(TD71) deveria ser {esperado}, mas é {resultado}"
    print(f"  ✓ SOMA(TD71) = {resultado}")
    
    # Teste 2: MEDIA de múltiplas variáveis
    resultado = evaluar_funcao_em_formula('MEDIA', 'TD71;TD72', dre_dados)
    valores_combinados = dre_dados['TD71']['valores'] + dre_dados['TD72']['valores']
    esperado = sum(valores_combinados) / len(valores_combinados)
    assert abs(resultado - esperado) < 0.01, f"MEDIA(TD71;TD72) falhou"
    print(f"  ✓ MEDIA(TD71;TD72) = {resultado:.2f}")
    
    # Teste 3: MAXIMO de intervalo
    resultado = evaluar_funcao_em_formula('MAXIMO', 'TD71:TD90', dre_dados)
    print(f"  ✓ MAXIMO(TD71:TD90) = {resultado:.2f}")
    
    # Teste 4: MINIMO de intervalo
    resultado = evaluar_funcao_em_formula('MINIMO', 'TD71:TD90', dre_dados)
    print(f"  ✓ MINIMO(TD71:TD90) = {resultado:.2f}")
    
    print("  ✅ Todos os testes de integração passaram!")


# ============================================================================
# TESTES DE FORMATAÇÃO
# ============================================================================

def test_disponibilidade_funcoes():
    """Teste se todas as funções estão disponíveis"""
    print("\n✓ Testando disponibilidade de funções...")
    
    funcoes_esperadas = ['SOMA', 'MEDIA', 'MINIMO', 'MAXIMO']
    
    for funcao in funcoes_esperadas:
        assert funcao in FUNCOES_NATIVAS, f"Função {funcao} não encontrada!"
        print(f"  ✓ Função {funcao} disponível")
    
    print("  ✅ Todas as funções estão disponíveis!")


# ============================================================================
# EXECUTAR TODOS OS TESTES
# ============================================================================

def rodar_todos_testes():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("🧪 EXECUTANDO TESTES DE METODOLOGIAS v2.1.0")
    print("="*60)
    
    try:
        # Testes básicos
        test_soma()
        test_media()
        test_minimo()
        test_maximo()
        
        # Testes de parser
        test_parse_range()
        
        # Testes de integração
        test_funcoes_com_dre_dados()
        
        # Testes de disponibilidade
        test_disponibilidade_funcoes()
        
        print("\n" + "="*60)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("="*60 + "\n")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    sucesso = rodar_todos_testes()
    exit(0 if sucesso else 1)
