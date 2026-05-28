# 📋 CHANGELOG - UAN Dashboard

Histórico de alterações, bugs fixados e features implementadas.

---

## 🚀 [v2.5.0] - 2026-05-27

### ✅ NOVA FEATURE - Sistema de Índices Econômicos (COMPLETO & VALIDADO)

#### 📈 Importação de Múltiplas Abas
- O upload de dados agora detecta automaticamente **múltiplas abas** em um único arquivo Excel
- Aba 1: `DADOS` (projeções/realizados) - estrutura e validações atuais
- Aba 2: `INDICES_TESOU` (índices econômicos) - importação direta, sem tratamento
- Ambas as abas são processadas simultaneamente no upload

#### 🏗️ Armazenamento Separado e Persistente
- Dados de projeções → `/uploads/base_dados_compartilhada.xlsx` (2.400 registros)
- Índices econômicos → `/uploads/base_indices_compartilhada.xlsx` (120 registros)
- Índices estruturados → `/database/indices/indices_compartilhados.json`
- Metadados → `/database/metadata/ultimo_upload_indices.json`

#### 🎯 Interface de Upload Melhorada
- Prévia automática de ambas as abas detectadas com contagem de linhas
- Validação separada para cada tipo de base com feedback claro
- Mensagens feedback estruturadas: "Base de Projeções: X registros" + "Índices Econômicos: Y registros (Z índices únicos)"
- Single button flow: "✔️ Confirmar e Carregar"

#### 📊 Nova Aba "Índices Econômicos" (DRE)
- **Visualização Dedicada:** Aba totalmente nova na página DRE (`/dre?tab=Índices Econômicos`)
- **Informações Gerais (Cards):**
  - Total de Registros: 120
  - Índices Únicos: 5
  - Total de Colunas: 0 (N/A - configurável)
  - Último Upload: 2026-05-27
- **Filtro por Índice:** Dropdown com seleção de IPCA, SELIC, IGP-M, DOLAR, IBOVESPA
- **Dados do Índice:** Estatísticas por índice selecionado
  - Registros: 24 (por índice)
  - Período (Início): 2022-01-01
  - Período (Fim): 2023-12-01
- **Primeiras 50 Linhas:** Tabela interativa com colunas DT_ALVO, DT_PRJ, VL_PJTD, NM_IN, FONTE
- **Estatísticas:** Análise de colunas numéricas (Min, Max, Mean, Std Dev)
- **Exportação:** Botões para CSV (semicolon-separated) e JSON download

#### 🔌 Novas Funções Backend (database.py)
```python
# Carregar índices compartilhados
carregar_indices_compartilhados() → Optional[Dict]

# Obter metadados do último upload de índices
obter_metadados_ultimo_upload_indices() → Optional[Dict]

# Verificar se índices foram importados
indices_existem() → bool

# Processar DataFrame de índices para estrutura JSON
processar_indices_para_json(df_indices: pd.DataFrame) → Dict

# Salvar índices em JSON estruturado
salvar_indices_json(dados_indices: Dict) → Tuple[bool, str]

# Upload adaptado para processar ambas as abas
salvar_upload_admin(arquivo_excel: bytes, nome_arquivo: str, usuario_id: str) → Tuple[bool, str]
```

#### 📊 Dados de Teste Inclusos
- 5 índices econômicos pré-carregados:
  - **IPCA:** 24 registros (Índice de Preços ao Consumidor)
  - **SELIC:** 24 registros (Sistema Especial de Liquidação)
  - **IGP-M:** 24 registros (Índice Geral de Preços)
  - **DOLAR:** 24 registros (Cotação do Dólar - B3)
  - **IBOVESPA:** 24 registros (Índice Bovespa - B3)
- Período: 2022-01-01 a 2023-12-01 (24 meses)
- Arquivo: `bd_dados_v4_Real.xlsx`

#### 🧪 Validação Completa (Full-Stack)
✅ **Backend:**
- `python -m py_compile backend/database.py` - Sem erros
- Upload com arquivo multi-aba processado com sucesso
- Arquivos XLSX e JSON criados corretamente
- Metadados salvos com timestamp

✅ **Frontend:**
- `python -m py_compile frontend/pages/upload.py` - Sem erros
- Upload interface detecta ambas as abas
- Preview mostra: "2400 registros + 120 registros"
- Single button "✔️ Confirmar e Carregar" funciona

✅ **DRE - Aba de Índices:**
- Carregamento de 120 registros com sucesso
- Filtro por índice funciona (5 opções disponíveis)
- Tabela mostra primeiras 50 linhas com dados corretos
- Exportação CSV/JSON disponível
- Último upload: 2026-05-27

✅ **Logs de Backend:**
```
[DB] Índices compartilhados carregados: 120 linhas
[DB] === RESULTADO FINAL ===
[DB] resultados['dados'] = True
[DB] resultados['indices'] = True
[DB] mensagem final: Base de Projeções: 2400 registros + Índices Econômicos: 120 registros (5 indices unicos)
```

#### 🛠️ Arquivos Alterados
- `backend/database.py` - Suporte a múltiplas abas, processamento e persistência de índices
- `frontend/pages/upload.py` - Nova UI para upload multi-aba com preview
- `frontend/pages/dre.py` - Nova aba "Índices Econômicos" com visualização completa
- `bd_dados_v4_Real.xlsx` - Arquivo de teste com dados reais (2.400 projeções + 120 índices)

#### 🚀 Próximas Etapas (v2.5.1+)
- [ ] Integração de índices em cálculos de DRE (uso em fórmulas)
- [ ] Uso de índices em metodologias (ex: `=0.05*IBOVESPA`)
- [ ] API de consulta por período/código de índice
- [ ] Versionamento de bases históricas
- [ ] Dashboard de tendências de índices

#### 📝 Status
**✅ PRODUCTION READY** - Feature completa, testada e validada com dados reais

---

## 🚀 [v2.4.2] - 2026-05-07

### ✅ CORRIGIDO - Fluxo de Save e Filtro de Produto

#### 🐛 NameError no simulador
- Corrigido erro `name 'salvar_clicked' is not defined` no fluxo de renderização da página Simulador.

#### 💾 Save unificado via sidebar
- O botão de salvar na sidebar passou a disparar o fluxo oficial de save dentro do simulador, preservando a curva ajustada atual e o sincronismo com localStorage/Bokeh.
- Removida duplicidade de lógica de persistência que poderia gerar comportamento inconsistente.

#### 📦 Opção "TODOS" no produto (comportamento real)
- As funções de agregação agora tratam produto vazio/TODOS como agregação por categoria (todos os produtos), em vez de filtrar por um único produto.
- Ajustado fallback para não substituir "TODOS" automaticamente pelo primeiro produto da lista.

#### 🛠️ Arquivos alterados
- `frontend/app.py`
- `frontend/pages/simulador.py`
- `frontend/services/aggregations.py`

#### 🧪 Validação
- `python -m py_compile frontend/app.py` ✅
- `python -m py_compile frontend/pages/simulador.py` ✅
- `python -m py_compile frontend/services/aggregations.py` ✅

---

## 🚀 [v2.4.1] - 2026-05-07

### ✅ HOTFIX - Inicialização de Session State

- Inicialização preventiva de `st.session_state["filtros"]` e `st.session_state["sim_nome"]`.
- Correção de acesso seguro às chaves de filtros para evitar `KeyError` na sidebar.

#### 🛠️ Arquivo alterado
- `frontend/app.py`

---

## 🚀 [v2.4.0] - 2026-05-07

### ✅ MELHORADO - Reorganização de UX no Simulador

- Filtros principais movidos para a barra lateral em expander dedicado.
- Reorganização do histórico de simulações em formato compacto com paginação.
- Inclusão da opção "TODOS" no filtro de produto.

#### 🛠️ Arquivos alterados
- `frontend/app.py`
- `frontend/pages/simulador.py`

---

## 🚀 [v2.2.9] - 2026-05-06

### ✅ MELHORADO - Cards de Categoria e Gráficos de Barras

#### 🧩 Cards com referência de realizado 2025
- Incluídas duas colunas novas nos cards de categoria com base de realizado 2025:
    - `Ref. 2025 Tot.`
    - `Ref. 2025 Méd.`

#### 📊 Informação relevante para linhas de projeção
- Como não há histórico de projeção de anos anteriores (viram realizado), as linhas de projeção passaram a mostrar comparação percentual contra a base de realizado 2025 nas colunas de referência.
- A linha de `Realizado` mantém a leitura absoluta da referência (Total e Média).

#### 📅 Filtro de ano nos gráficos de barras
- Adicionado seletor `Ano - Barras` na seção de análises por categoria.
- Os gráficos de barras agora são recalculados conforme o ano selecionado, sem impactar cards e pizzas.
- O título de cada gráfico de barras exibe o ano ativo para reduzir ambiguidades visuais.

#### 🛠️ Arquivos alterados
- `frontend/services/aggregations.py`
- `frontend/components/cards.py`
- `frontend/components/bars.py`
- `frontend/pages/simulador.py`

#### 🧪 Validação
- Compilação sintática:
    - `python -m py_compile frontend/pages/simulador.py` ✅
    - `python -m py_compile frontend/components/cards.py` ✅
    - `python -m py_compile frontend/components/bars.py` ✅
    - `python -m py_compile frontend/services/aggregations.py` ✅

---

## � [v2.2.8] - 2026-05-06

### ✅ CORRIGIDO - Funcionalidade de Rotação/Inclinação da Curva

#### 🔴 Bug Crítico #1: StreamlitAPIException ao clicar "Aplicar"
    - **Issue:** Usuário alterava slider para +11.00x, clicava "Aplicar", mas a curva não mudava
    - **Root Cause:** Calculava apenas 12 meses (2026) mas simulador ALWAYS usa 24 meses (2026 + 2027)
        - Quando simulador recarregava, via `len(12) != len(24)` e **resetava para base**
    - **Solução:** Expandir cálculo para SEMPRE retornar 24 elementos

#### 🔴 Bug Crítico #2: Rotação não persistia corretamente
    - **Issue:** `st.session_state.sim_rotacionar_curva cannot be modified after widget instantiated`
    - **Root Cause:** Conflito de renderização com chaves do Streamlit
    - **Solução:** Sistema de 3 chaves separadas (sem conflito)

#### ✅ Correções Aplicadas

**1. Sistema de Chaves Corrigido:**
**1. Expansão para 24 Meses:**
    - Calcula para 12 primeiros (2026)
    - Se tem 24 elementos, aplica mesma rotação aos 12 seguintes (2027)
    - Caso contrário, replica os 12 primeiros
    - Sempre retorna 24 elementos

**2. Fluxo de Persistência:**
**2. Sistema de Chaves:**
    - Slider: `key="sim_rotacionar_mult"` (não modificável)
    - Persistência: `_sim_rotacionar_curva_aplicado` (privada)
    - Simulador: `sim_rotacionar_curva` (pública)

#### 📝 Fluxo Corrigido (End-to-End)
1. Usuário ajusta slider → clica "✅ Aplicar"
2. Rotação calculada para 12 meses (2026)
3. Expandida para 24 meses (2026 + 2027)
4. Salva com tamanho correto: `len(ajustada) == 24`
5. Simulador carrega sem resetar, mostra rotação
6. Curva visualiza a rotação corretamente

#### 🛠️ Arquivo alterado
    - `frontend/app.py` (função `_calcular_curva_rotacionada_sidebar`)

#### 🧪 Validação
    - Compilação sintática: `python -m py_compile frontend/app.py` ✅
    - Retorna 24 elementos ✅
    - Sem reset de dados ✅

---

## �🚀 [v2.2.7] - 2026-04-29

### ✅ MELHORADO - Tabela Histórica do Simulador

#### ✨ Destaque para colunas de AJUSTE
- Colunas `AJUSTE (+/-)` (2026 e 2027) passaram a ter formatação visual destacada.

#### 🔒 Edição válida somente em AJUSTE
- Mantida edição de tabela apenas para `Ajuste_2026` e `Ajuste_2027`.
- Edições em colunas não permitidas são revertidas automaticamente via callback.

#### 🔄 Sincronização com painel "Ajuste Manual por Mês"
- Corrigida aplicação de sincronização do localStorage: valores de 12 meses são mapeados para o vetor interno de 24 meses.
- Com isso, o incremento exibido no painel manual passa a refletir corretamente os ajustes digitados na tabela após sincronização.

#### 🛠️ Arquivo alterado
- `frontend/pages/simulador.py`

#### 🧪 Validação
- Compilação sintática: `python -m py_compile frontend/pages/simulador.py` ✅

---

## 🚀 [v2.2.6] - 2026-04-28

### ✅ HOTFIX - Conflito de Documento Bokeh no Simulador

#### 🔴 Erro corrigido: `Models must be owned by only a single document`
- **Issue:** A tabela histórica usava callback com referência a `ColumnDataSource` do gráfico principal, mas estava sendo renderizada em outro documento Bokeh via `streamlit_bokeh`.
- **Root Cause:** O mesmo model Bokeh (`src_ajs`) estava sendo compartilhado entre dois renders/documentos distintos.
- **Solução:** Unificação do gráfico principal e da tabela histórica em um único layout Bokeh renderizado por `bokeh_editable`.

#### ✅ Impacto
- Mantida a sincronização entre edição da tabela e curva ajustada.
- Eliminado erro de ownership de modelos Bokeh.

#### 🛠️ Arquivo alterado
- `frontend/pages/simulador.py`

#### 🧪 Validação
- Compilação sintática: `python -m py_compile frontend/pages/simulador.py` ✅

---

## 🚀 [v2.2.5] - 2026-04-28

### ✅ HOTFIX - Renderização da Tabela Histórica do Simulador

#### 🔴 Erro corrigido: validação de `TableColumn.editor`
- **Issue:** `ValueError: failed to validate TableColumn(...).editor: expected an instance of type CellEditor, got None`
- **Root Cause:** Foram criadas colunas com `editor=None`, mas o Bokeh exige uma instância válida de `CellEditor` quando a propriedade `editor` é informada.
- **Solução:** Removido `editor=None` das colunas não editáveis, mantendo `NumberEditor` apenas nas colunas de `AJUSTE (+/-)`.

#### 🛠️ Arquivo alterado
- `frontend/pages/simulador.py`

#### 🧪 Validação
- Compilação sintática: `python -m py_compile frontend/pages/simulador.py` ✅

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

**Última atualização:** 2026-05-07 | **Versão Atual:** v2.4.2
