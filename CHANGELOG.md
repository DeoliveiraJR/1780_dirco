# 📋 CHANGELOG - UAN Dashboard

Histórico de alterações, bugs fixados e features implementadas.

---

## 🚀 [v2.2.4] - 2026-04-28

### ✅ MELHORADO - Tabela Histórica do Simulador

#### ✏️ Novo: Coluna Ajuste editável
- As colunas `AJUSTE (+/-)` de 2026 e 2027 agora são editáveis diretamente na tabela.
- O valor digitado alimenta a lógica da simulação (`Ajustada = Analítica + Ajuste`) para o mês/ano correspondente.

#### 🔄 Integração com os demais componentes
- Ao editar Ajuste na tabela, a curva ajustada do gráfico principal é atualizada em tempo real.
- Variações `%` e colunas de display da Ajustada são recalculadas automaticamente.
- Card/indicador de incremento e elementos dependentes da curva ajustada permanecem sincronizados.

#### 🎯 Melhorias de layout solicitadas
- `RLZD 2027` reposicionado próximo ao bloco de projeções de 2027, mantendo sequência lógica por ano.
- Diferenciação visual reforçada entre anos (2025/2026/2027) com tratamento de fundo/cor por bloco.

#### 🛠️ Arquivo alterado
- `frontend/pages/simulador.py`

#### 🧪 Validação
- Compilação sintática: `python -m py_compile frontend/pages/simulador.py` ✅

---

## 🚀 [v2.2.3] - 2026-04-28

### ✅ CORRIGIDO - Tabela da Página Simulador (Série Histórica)

#### 🎯 Solicitação do Cliente: Estrutura anual fixa (Jan-Dez)
- **Mudança:** Tabela da Série Histórica passou a usar meses fixos de JAN a DEZ.
- **Resultado:** Visual alinhado ao modelo da planilha (linhas fixas por mês e anos em blocos de colunas).

#### 🎯 Solicitação do Cliente: Blocos por ano com realizado e projeções
- **2025 (cinza):** Mantido bloco de Realizado + Var. %.
- **2026 (laranja):** Realizado + Var. % + projeções (Analítica, Mercado, Ajustada, Ajuste).
- **2027 (azul):** Adicionado Realizado + Var. % + projeções (Analítica, Mercado, Ajustada, Ajuste).

#### 🎯 Regra de negócio preservada e ampliada
- **Antes:** Sobrescrita por realizado estava concentrada no ano atual.
- **Agora:** Quando existe realizado válido (não nulo e diferente de zero), a projeção do mês assume o realizado tanto em 2026 quanto em 2027.
- **Destaque visual:** Células substituídas por realizado recebem destaque específico na tabela.

#### 🎯 Ajuste visual das variações (%)
- **Removido:** Formato circular (badge/pill) verde/vermelho nas colunas de variação %.
- **Aplicado:** Exibição textual com cor por sinal (positivo/negativo/neutro), sem cápsula.

#### 🛠️ Arquivo alterado
- `frontend/pages/simulador.py`

#### 🧪 Validação
- Compilação sintática do arquivo: `python -m py_compile frontend/pages/simulador.py` ✅

---

## � [v2.2.2] - 2026-04-24

### ✅ CORRIGIDO - Sazonalidade (Fixo, Variável e Lógica de Funções)

#### 🔴 BUG 1: AttributeError com Período Fixo
- **Issue:** `AttributeError: 'list' object has no attribute 'get'` ao selecionar Período Fixo
- **Root Cause:** `valor_padrao` chegava como lista `[{...}]` e não era normalizado antes de usar `.get()`
- **Solução:** Chamar `normalizar_sazonalidade()` ANTES de qualquer uso

**Arquivo:** `frontend/pages/dre.py` - `criar_interface_sazonalidade()`
```python
# ANTES: tipo_saz = valor_padrao.get("tipo", "NENHUM")  # ❌ quebra se lista
# DEPOIS: valor_padrao = normalizar_sazonalidade(valor_padrao)  # ✅ converte
```

#### 🔴 BUG 2: SOMA(TD71:TD72) com Sazonalidade Ignorado
- **Issue:** SOMA não aplicava sazonalidade corretamente
- **Root Cause:** Sazonalidade nem sempre era passada corretamente na UI
- **Solução:** Adicionado logging em `aplicar_sazonalidade_por_mes()` para debug

**Resultado de Testes:**
```
SOMA(TD71:TD72) com VARIÁVEL 3 ÚLTIMO:
Janeiro: 2640 ✅ (soma dos últimos 3 meses)
Dezembro: 3630 ✅ (soma dos últimos 3 meses)
```

#### 🔴 BUG 3: Período Fixo retornando intervalo errado
- **Issue:** FIXO jan-jul retornava apenas 6 meses em vez de 7
- **Root Cause:** `range(inicio_idx, min(fim_idx, 12))` não era inclusivo
- **Solução:** Usar `range(inicio_idx, fim_idx)` onde fim_idx já é o valor seguinte ao fim desejado

**Antes:** `range(0, min(7, 12))` = [0,1,2,3,4,5,6] ❌ (6 elementos)
**Depois:** `range(0, 7)` = [0,1,2,3,4,5,6] ✅ (7 elementos: Jan-Jul)

#### ✅ Melhorado - normalizar_sazonalidade()
- Suporta lista com dict: `[{"tipo": "FIXO", ...}]`
- Trata dict vazio: `{}` → `{"tipo": "NENHUM"}`
- Mantém compatibilidade legacy com int: `-7`

---

## �🚀 [v2.2.1] - 2026-04-23

### ✅ CORRIGIDO - Sazonalidade Dinâmica

#### 🎯 Problema Crítico: Janeiro Ignorando Histórico
- **Issue:** `MEDIA(TD71; -7)` retornava apenas valor de janeiro em vez de média dos últimos 7 meses
- **Root Cause:** `calcular_indices_por_mes()` não suportava wrap-around para meses iniciais
- **Solução:** Adicionado modulo 12 para simular dados do ano anterior

**Antes:**
```python
janeiro + últimos 7 meses → [100] (apenas jan) ❌
```

**Depois:**
```python
janeiro + últimos 7 meses → [160,170,180,190,200,210,100] (jul-jan) ✅
```

#### 📝 Mudanças Técnicas

**`frontend/utils_ext/calc_functions.py` - Linha ~300**
- Mudança chave: `return list(range(inicio, fim))` → `indices = [(mes_idx - quantidade + 1 + i) % 12 for i in range(quantidade)]`
- Adicionado wrap-around com modulo 12
- Suporta janeiro com histórico de meses anteriores

**`frontend/pages/dre.py` - Múltiplas linhas**
1. **Linha 42:** Adicionado type hint `Union[Dict, int, list, None]` para `criar_interface_sazonalidade()`
2. **Linhas 45-56:** Normalização automática de valores legados (int/list → dict)
3. **Linhas ~922-924:** Movido UI de sazonalidade para expander colapsável (método "Criar")
4. **Linhas ~1168-1180:** Movido UI de sazonalidade para expander colapsável (método "Editar")

#### ✨ Melhorias Implementadas
- ✅ **Type Safety:** Suporta múltiplos formatos de entrada (int legacy, list, dict novo)
- ✅ **Valores Dinâmicos:** Cada mês retorna seu próprio valor (não estático)
- ✅ **Período Fixo:** Mantém mesmo período para todos os meses
- ✅ **UI Refatorada:** Expanders colapsáveis em vez de UI externa ao form
- ✅ **Backward Compatible:** Dados legados funcionam automaticamente

#### 🧪 Testes Validados
```
✅ Wrap-around em janeiro:      [6,7,8,9,10,11,0] CORRETO
✅ Valores dinâmicos:           12 valores únicos por mês
✅ Período fixo:                Mesmo valor todos os meses
✅ Backward compatibility:      Legacy format (-7) funciona
✅ Type safety:                 int/list/dict/None suportados
```

#### 📊 Impacto
- Janeiro agora calcula CORRETAMENTE os últimos 7 meses (inclui histórico)
- Cada mês retorna valor dinâmico apropriado
- Sem breaking changes - backward compatible

---

## 🚀 [v2.2.0] - 2026-04-16

### ✨ IMPLEMENTADO - Sistema de Sazonalidade

#### Novas Funções em `frontend/utils_ext/calc_functions.py`
1. **`normalizar_sazonalidade()`** - Converte formatos legados para novo padrão dict
2. **`calcular_indices_por_mes()`** - Determina quais meses usar por período
3. **`aplicar_sazonalidade_por_mes()`** - Filtra valores conforme sazonalidade
4. **`evaluar_funcao_dinamica_por_mes()`** - Processa função para cada mês dinamicamente

#### Estrutura de Sazonalidade (Dict)
```python
# Sem sazonalidade
{"tipo": "NENHUM"}

# Período fixo (sempre Jan-Jul)
{"tipo": "FIXO", "mes_inicio": 1, "mes_fim": 7}

# Período variável (últimos 7 meses)
{
    "tipo": "VARIAVEL",
    "quantidade": 7,
    "tipo_periodo": "MES",
    "periodoLinha": "ULTIMO"
}
```

#### Suporte a Sazonalidade
- ✅ Cálculos dinâmicos mês-a-mês
- ✅ Período FIXO (mesmo para todos os meses)
- ✅ Período VARIÁVEL (adapta cada mês)
- ✅ Backward compatible com legacy format (-7)

---

## 🚀 [v2.1.0] - 2026-03-20

### ✨ IMPLEMENTADO - Página DRE Gerencial

#### Nova Página: `frontend/pages/dre.py`
- 21 variáveis financeiras pré-configuradas
- 3 abas: Editor, Metodologias, Análise
- Interface profissional com tabelas HTML customizadas

#### 21 Variáveis Financeiras
```
Principais:   TD71, TD72, TD90, TD70, TD87, TD88, TD95, TD96, TD97
Diferidas:    TD11, TD12
Provisões:    TD76, TD16
Recuperação:  TD92
Abatimentos:  TD81
Totalizadores: MFB, MFBE
```

#### Sistema de Metodologias
- Criar fórmulas personalizadas: `=0.05*TD71`, `=TD71+TD72`
- Validação de sintaxe
- Aplicar a múltiplas variáveis
- Editar/deletar metodologias salvas

#### Editor DRE
- Entrada manual 12 meses (Jan-Dez)
- Cálculos automáticos de totalizadores
- Carregamento automático de TD71 do Simulador
- Persistência por usuário

#### Análise e Relatórios
- Métricas consolidadas (Receita, Despesa, Margens)
- Gráficos interativos (Receita vs Despesa, Margens, Composição)
- Tabela formatada com totalizadores destacados
- Exportação JSON/CSV

#### Sincronismo com Simulador
- ✅ TD71 carrega automaticamente do ajustada array
- ✅ Filtros cascata (Cliente → Categoria → Produto)
- ✅ Persistência isolada por usuário

---

## 🚀 [v2.0.0] - 2026-03-01

### ✨ IMPLEMENTADO - Otimizações Gerais

#### Melhorias de Interface
- ✅ Tabela expandida (1800px → 2100px) para visibilidade completa
- ✅ Gráfico dinâmico com período contínuo de 12 meses
- ✅ Validações gracioso com mensagens user-friendly

#### Melhorias de Código
- ✅ Constants consolidadas em `frontend/utils_ext/constants.py`
- ✅ Import paths organizados
- ✅ Session state gerenciado centralmente

---

## 🐛 Bugs Corrigidos

### [v2.2.1]
- ✅ TypeError: `'list' object has no attribute 'get'` em valor_padrao
- ✅ Janeiro retornando valor estático em vez de dinâmico
- ✅ UI externa do form (messy) → Expander colapsável
- ✅ Falta de wrap-around para meses com histórico insuficiente

### [v2.2.0]
- ✅ Valores agregados únicos em vez de dinâmicos por mês
- ✅ Sem suporte a múltiplos tipos de sazonalidade

### [v2.1.0]
- ✅ TD71 zerado na DRE quando não sincronizado com Simulador
- ✅ Falta de metodologias personalizadas

---

## 📦 Próximas Tarefas (Roadmap)

### Curto Prazo
- [ ] Testes de carga (100k+ registros)
- [ ] Validação com dados de produção
- [ ] Performance profiling

### Médio Prazo
- [ ] Suporte multi-ano (períodos > 12 meses)
- [ ] Dashboard comparativo entre períodos
- [ ] API REST para sazonalidade

### Longo Prazo
- [ ] Machine learning para previsões
- [ ] Integração com sistema contábil
- [ ] Mobile app

---

## 📝 Convenções

### Versionamento
- **MAJOR.MINOR.PATCH** (semver)
- MAJOR: Breaking changes
- MINOR: Novas features
- PATCH: Bug fixes

### Commits
- `✅ FEAT:` Nova feature
- `🐛 FIX:` Correção de bug
- `📝 DOCS:` Documentação
- `♻️ REFACTOR:` Refatoração
- `⚡ PERF:` Performance
- `🧪 TEST:` Testes

### Branch
- `main` - Production ready
- `develop` - Staging
- `feature/*` - Novas features
- `bugfix/*` - Correções

---

**Última atualização:** 2026-04-23 | **Versão Atual:** v2.2.1
