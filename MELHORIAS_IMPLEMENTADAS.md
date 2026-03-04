# Melhorias Implementadas - Estrutura de Projeções 12 Meses

## 📋 Resumo das Mudanças

Foram implementadas melhorias significativas na forma como o sistema apresenta projeções de curvas que cruzam de um ano para outro, respondendo à necessidade de trabalhar com um período contínuo de 12 meses mesmo quando isso implica transição entre anos (ex: Março 2026 → Março 2027).

---

## 🔧 Mudanças Técnicas

### 1. **Novas Funções em `frontend/services/aggregations.py`**

#### `_carregar_curvas_por_ano()`
- **Propósito**: Carrega projeções (Analítica, Mercado, Ajustada) para um ano específico
- **Parâmetros**: `cliente`, `categoria`, `produto`, `ano_proj`
- **Retorno**: Tupla `(ana[12], mer[12], ajs[12])`

#### `_carregar_proximos_12_meses()`
- **Propósito**: Monta um período contínuo de 12 meses começando do mês atual, integrando dados de ambos os anos quando necessário
- **Parâmetros**: 
  - `cliente`, `categoria`, `produto`
  - `mes_atual`, `ano_atual` (da data atual)
  - `mascarar_zeros_finais` (bool)
- **Retorno**: Dicionário com estrutura:
  ```python
  {
      "meses": ["Mar 2026", "Abr 2026", ..., "Fev 2027", "Mar 2027"],
      "meses_num": [3, 4, ..., 2, 3],
      "anos": [2026, 2026, ..., 2027, 2027],
      "rlzd": [valor, ...],      # Realizado (se houver)
      "ana": [valor, ...],       # Projeção Analítica
      "mer": [valor, ...],       # Projeção Mercado
      "ajs": [valor, ...]        # Projeção Ajustada
  }
  ```

### 2. **Refatoração da Tabela em `frontend/pages/simulador.py`**

#### Estrutura Anterior (Problemática)
- Mostrava 12 meses fixos do ano atual
- Duplicava colunas para "2026" mesmo quando dados deveriam vir de 2027
- Não deixava claro quando havia transição de anos
- Colunas: `RLZD 2026`, `VAR% 2026`, `Prj_Ana_2026`, ..., `Prj_Ana_2026` (repetida)

#### Estrutura Nova (Melhorada)
- Mostra **período contínuo de 12 meses** (ex: Mar 2026 → Mar 2027)
- Cabeçalho de coluna "Período" mostra mês e ano: `"Mar 2026"`, `"Abr 2026"`, etc.
- **Colunas consolidadas**: 
  - `Período` (ex: "Abr 2026")
  - `Realizado` (se já passou e há dados)
  - `Var. % Rlzd`
  - `Analítica` (dados de 2026 ou 2027 conforme necessário)
  - `Var. % Analítica`
  - `Mercado`
  - `Var. % Mercado`
  - `Ajustada` (editável, pode ser manipulada)
  - `Var. % Ajustada`
  - `Ajuste (Δ)` (diferença Ajustada - Analítica)

#### Lógica de Substituição
- **Meses já passados com realizado**: Valor vem do realizado
- **Meses futuros**: Valor vem da projeção (Analítica, Mercado ou Ajustada)
- **Transição entre anos**: Dados carregados automaticamente do ano correto

### 3. **Atualização dos Gráficos**

#### Eixo X do Gráfico Bokeh
- **Anterior**: Mostrava apenas nomes de mês (Jan, Fev, ..., Dez)
- **Novo**: Mostra período completo com ano (`"Mar 2026"`, `"Abr 2026"`, ..., `"Mar 2027"`)

#### Divisor Visual
- Linha vertical tracejada marca a transição entre anos
- Anotação mostra claramente: `"2026→2027"`
- Facilita visualização da estrutura do período

#### Dados dos Gráficos
- Utiliza os mesmos 12 meses contínuos da tabela
- Sincronizado com edições do gráfico drag-and-drop
- Mantém a cor diferenciada para Ajustada (editável)

---

## 📊 Comportamento Esperado

### Cenário: Março de 2026 (mesActual = 3)

**Período de 12 meses será:**
- `Mar 2026` → `Dez 2026` (10 meses do ano 2026)
- `Jan 2027` → `Mar 2027` (3 meses do ano 2027)

**Dados utilizados:**
- Mar → Dez 2026: Dados vêm da tabela de **2026**
- Jan → Mar 2027: Dados vêm da tabela de **2027**

**Valores:**
- Meses já passados (Mar): Realizado (se houver)
- Meses futuros (Abr → Mar 2027): Projeção

---

## ✅ Benefícios

1. **Clareza**: Fica imediatamente óbvio qual é o período coberto (por exemplo, "Mar 2026 → Mar 2027")
2. **Precisão**: Projeções corretas de 2027 são usadas para meses de 2027, não valores repetidos de 2026
3. **Simplicidade**: Única tabela ao invés de múltiplas colunas redundantes
4. **Sincronização**: Tabela e gráfico trabalham com os mesmos dados
5. **Manutenção**: Mais fácil de entender e modificar no futuro

---

## 🐛 Notas para Testes

- Verificar que projeções de **2027 estão sendo carregadas corretamente**
- Confirmar que **meses passados mostram realizado**, não projeção
- Validar que a **linha divisória entre anos aparece no gráfico**
- Testar edição de valores: arrastar pontos no gráfico deve atualizar a tabela
- Verificar sincronização: cllocar "Sincronizar" deve aplicar edições

---

## 📁 Arquivos Modificados

1. **`frontend/services/aggregations.py`**
   - Adicionado: `_carregar_curvas_por_ano()`
   - Adicionado: `_carregar_proximos_12_meses()`

2. **`frontend/pages/simulador.py`**
   - Refatorado: Construção de dados da tabela
   - Refatorado: Definição de colunas da tabela
   - Refatorado: Gráfico Bokeh para usar período de 12 meses
   - Atualizado: ImportError de `_carregar_proximos_12_meses`

---

## 🎯 Próximos Passos (Sugestões)

1. Considerar adicionar um **seletor de período** para deixar o usuário escolher começar em outro mês
2. Adicionar **indicadores de célula** para distinguir visualmente realizado vs projetado
3. Considerar **exportar tabela** com layout aprimorado incluindo a estrutura de anos
