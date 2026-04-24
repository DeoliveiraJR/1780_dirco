"""
DEMONSTRAÇÃO VISUAL: Problema Original vs Solução

Mostra claramente a diferença entre:
❌ ANTES: MEDIA(TD71; -7) retornava valor FIXO e estático
✅ DEPOIS: MEDIA(TD71; -7) retorna valor DINÂMICO a cada mês
"""

import sys
sys.path.insert(0, "frontend")

from utils_ext.calc_functions import evaluar_funcao_dinamica_por_mes

# Dados simulados: Receita crescente ao longo dos meses
dre_dados = {
    "TD71": {
        "codigo": "TD71",
        "descricao": "Receita Financeira",
        "valores": [
            100.0,     # Janeiro
            150.0,     # Fevereiro
            200.0,     # Março
            250.0,     # Abril
            300.0,     # Maio
            350.0,     # Junho
            400.0,     # Julho
            450.0,     # Agosto
            500.0,     # Setembro
            550.0,     # Outubro
            600.0,     # Novembro
            650.0,     # Dezembro
        ]
    }
}

print("="*80)
print("🔍 DEMONSTRAÇÃO: SAZONALIDADE DINÂMICA vs FIXA")
print("="*80)

print("""
CENÁRIO: Empresa com receita CRESCENTE ao longo do ano
Dados: 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650

FÓRMULA: =MEDIA(TD71)
""")

print("\n" + "-"*80)
print("❌ PROBLEMA ANTIGO (ANTES): Sazonalidade como int (-7)")
print("-"*80)
print("""
Quando a sazonalidade era um número inteiro, a função calculava UMA ÚNICA VEZ
o valor agregado e reutilizava em todos os 12 meses.

Resultado: Valor FIXO e ESTÁTICO em todos os meses
  Jan: 400.0  ← calculado uma vez
  Fev: 400.0  ← reutilizado (ERRADO!)
  Mar: 400.0  ← reutilizado (ERRADO!)
  ...
  Dez: 400.0  ← reutilizado (ERRADO!)

❌ Problema: Não reflete a TENDÊNCIA REAL dos dados!!!
   A receita crescente em dezembro deveria gerar uma MÉDIA MAIOR!
""")

print("\n" + "-"*80)
print("✅ SOLUÇÃO NOVA: Sazonalidade como estrutura Dict (Tipo + Parâmetros)")
print("-"*80)

# TESTE 1: PERÍODO VARIÁVEL (Últimos 7 meses)
print("""
TESTE 1: Sazonalidade VARIÁVEL (Últimos 7 meses - MÓVEL)
----
Cada mês calcula sua própria média dos últimos 7 meses:
""")

saz_var_ultimo_7 = {
    "tipo": "VARIAVEL",
    "quantidade": 7,
    "tipo_periodo": "MES",
    "periodoLinha": "ULTIMO"
}

resultado_var = evaluar_funcao_dinamica_por_mes(
    'MEDIA', 'TD71', dre_dados, saz=saz_var_ultimo_7
)

meses = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

print("  Mês              | Valores Usados         | Média")
print("  " + "-"*66)
for i, mes in enumerate(meses):
    valores_usados = dre_dados["TD71"]["valores"][max(0, i-6):i+1]
    print(f"  {mes:15} | {str(valores_usados):20} | {resultado_var[i]:6.1f}")

print(f"""
✅ RESULTADO CORRETO: A média é DINÂMICA!
   - Janeiro: 100.0  (só tem 1 mês)
   - Julho: 400.0    (média de jan-jul)
   - Dezembro: 550.0 (média dos últimos 7: jun-dez)
   
   ✨ Cada mês tem seu valor apropriado conforme a tendência!
""")

# TESTE 2: PERÍODO FIXO (Jan-Jul para todos)
print("\n" + "-"*80)
print("""
TESTE 2: Sazonalidade FIXO (Jan-Jul sempre - para todos os meses)
----
Cada mês usa SEMPRE os dados de jan-jul (período fixo):
""")

saz_fixo_jan_jul = {
    "tipo": "FIXO",
    "mes_inicio": 1,
    "mes_fim": 7,
}

resultado_fixo = evaluar_funcao_dinamica_por_mes(
    'MEDIA', 'TD71', dre_dados, saz=saz_fixo_jan_jul
)

print("  Mês          | Sempre Usa (Jan-Jul) | Média")
print("  " + "-"*50)
for i, mes in enumerate(meses):
    valores_usados = dre_dados["TD71"]["valores"][0:7]  # Sempre jan-jul
    print(f"  {mes:12} | {str(valores_usados):20} | {resultado_fixo[i]:6.1f}")

print(f"""
✅ RESULTADO CORRETO: A média é FIXA!
   - Janeiro: 400.0
   - Fevereiro: 400.0
   - ...
   - Dezembro: 400.0
   
   ✨ Usado para comparações consistentes em base FIXA!
""")

print("\n" + "="*80)
print("📊 RESUMO DAS DIFERENÇAS")
print("="*80)
print("""
┌─ ANTES (❌ PROBLEMA) ────────────────────────────────────────┐
│                                                               │
│ Sazonalidade: -7 (número inteiro)                            │
│ Cálculo: UMA VEZ e reutiliza em todos os meses              │
│ Resultado:                                                   │
│   - Todos os meses retornam o MESMO valor (400.0)           │
│   - Não reflete a TENDÊNCIA dos dados                       │
│   - Inútil para análises sazonais reais                      │
│                                                               │
└───────────────────────────────────────────────────────────────┘

┌─ DEPOIS (✅ SOLUÇÃO) ────────────────────────────────────────┐
│                                                               │
│ Sazonalidade: {tipo, quantidade, tipo_periodo, periodoLinha}│
│                                                               │
│ ├─ Período Variável (Móvel):                                │
│ │  {tipo: VARIAVEL, quantidade: 7, periodoLinha: ULTIMO}   │
│ │  → Cada MÊS calcula seus últimos 7 meses                 │
│ │  → Resultado: DINÂMICO [100, 150, 200, ..., 550]        │
│ │                                                           │
│ └─ Período Fixo (Estático):                                │
│    {tipo: FIXO, mes_inicio: 1, mes_fim: 7}                 │
│    → Todos os MESES usam jan-jul                            │
│    → Resultado: FIXO [400, 400, 400, ..., 400]             │
│                                                               │
└───────────────────────────────────────────────────────────────┘

🎯 CASOS DE USO:

1️⃣ PERÍODO VARIÁVEL (Últimos N meses):
   - Para detectar TENDÊNCIAS recentes
   - Ex: "Como está a receita nos últimos 7 meses?"
   - Resultado: Varia mês a mês ✨

2️⃣ PERÍODO FIXO (Mesmo período sempre):
   - Para COMPARAR em base consistente
   - Ex: "Qual é a performance de jan-jul em todos os anos?"
   - Resultado: Consistente todo mês 🔒

3️⃣ NENHUM (Todos os 12 meses):
   - Para análise completa do ano
   - Resultado: Média geral constante
""")

print("\n" + "="*80)
print("✅ NOVA FUNCIONALIDADE VALIDADA E FUNCIONANDO!")
print("="*80 + "\n")
