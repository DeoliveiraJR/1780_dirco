#!/usr/bin/env python3
"""
Script de teste para validar sazonalidade com SOMA(TD71:TD72)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend'))

from utils_ext.calc_functions import (
    normalizar_sazonalidade, 
    calcular_indices_por_mes,
    aplicar_sazonalidade_por_mes,
    evaluar_funcao_dinamica_por_mes
)

# ===== TESTE 1: normalizar_sazonalidade =====
print("=" * 70)
print("TEST 1: normalizar_sazonalidade")
print("=" * 70)

test_cases = [
    None,
    0,
    [],
    [{}],
    {"tipo": "VARIAVEL", "quantidade": 3, "tipo_periodo": "MES", "periodoLinha": "ULTIMO"},
    {"tipo": "FIXO", "mes_inicio": 1, "mes_fim": 7},
    -7,  # Legacy
]

for test in test_cases:
    result = normalizar_sazonalidade(test)
    print(f"  Input: {str(test)[:50]:50} -> Type: {result.get('tipo')}")

# ===== TESTE 2: calcular_indices_por_mes para VARIÁVEL 3 ÚLTIMO =====
print("\n" + "=" * 70)
print("TEST 2: calcular_indices_por_mes - VARIÁVEL 3 ÚLTIMO")
print("=" * 70)

saz = normalizar_sazonalidade({"tipo": "VARIAVEL", "quantidade": 3, "tipo_periodo": "MES", "periodoLinha": "ULTIMO"})
print(f"Sazonalidade: {saz}\n")

for mes_idx in range(12):
    indices = calcular_indices_por_mes(saz, mes_idx)
    mes_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    mes_atual = mes_nomes[mes_idx]
    meses_usados = [mes_nomes[i] for i in indices]
    print(f"  Mês {mes_idx:2d} ({mes_atual}): indices={indices} → {meses_usados}")

# ===== TESTE 3: calcular_indices_por_mes para FIXO JAN-JUL =====
print("\n" + "=" * 70)
print("TEST 3: calcular_indices_por_mes - FIXO JAN-JUL")
print("=" * 70)

saz_fixo = normalizar_sazonalidade({"tipo": "FIXO", "mes_inicio": 1, "mes_fim": 7})
print(f"Sazonalidade: {saz_fixo}\n")

for mes_idx in [0, 1, 5, 11]:  # Jan, Fev, Jun, Dez
    indices = calcular_indices_por_mes(saz_fixo, mes_idx)
    mes_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    mes_atual = mes_nomes[mes_idx]
    meses_usados = [mes_nomes[i] for i in indices]
    print(f"  Mês {mes_idx:2d} ({mes_atual}): indices={indices} → {meses_usados}")

# ===== TESTE 4: aplicar_sazonalidade_por_mes =====
print("\n" + "=" * 70)
print("TEST 4: aplicar_sazonalidade_por_mes - VARIÁVEL 3 ÚLTIMO")
print("=" * 70)

valores_exemplo = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200]
print(f"Valores de exemplo: {valores_exemplo}\n")

saz = normalizar_sazonalidade({"tipo": "VARIAVEL", "quantidade": 3, "tipo_periodo": "MES", "periodoLinha": "ULTIMO"})

for mes_idx in [0, 1, 11]:  # Jan, Fev, Dez
    valores = aplicar_sazonalidade_por_mes(valores_exemplo, saz, mes_idx)
    mes_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    mes_atual = mes_nomes[mes_idx]
    print(f"  Mês {mes_idx} ({mes_atual}): {len(valores)} valores → {valores}")

# ===== TESTE 5: evaluar_funcao_dinamica_por_mes com SOMA =====
print("\n" + "=" * 70)
print("TEST 5: evaluar_funcao_dinamica_por_mes - SOMA com sazonalidade")
print("=" * 70)

# Criar dados de teste
dre_teste = {
    "TD71": {"valores": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200]},
    "TD72": {"valores": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]},
}

saz = {"tipo": "VARIAVEL", "quantidade": 3, "tipo_periodo": "MES", "periodoLinha": "ULTIMO"}
print(f"Fórmula: SOMA(TD71:TD72)")
print(f"Sazonalidade: {saz}\n")

resultado = evaluar_funcao_dinamica_por_mes("SOMA", "TD71:TD72", dre_teste, saz)
print(f"\nResultado (12 meses): {resultado}")
print(f"  Jan (3 últimos): {resultado[0]} (esperado: {100+1100+1200 + 10+110+120} = {100+1100+1200+10+110+120})")
print(f"  Fev (3 últimos): {resultado[1]}")
print(f"  Dez (3 últimos): {resultado[11]} (esperado: {1000+1100+1200 + 100+110+120} = {1000+1100+1200+100+110+120})")

print("\n" + "=" * 70)
print("TESTES COMPLETADOS")
print("=" * 70)
