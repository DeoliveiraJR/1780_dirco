---
name: dre-engine-context
description: "Use esta skill quando precisar entender, depurar, evoluir ou validar a página DRE (frontend/pages/dre.py) e o motor de cálculo (frontend/utils_ext/calc_functions.py), incluindo metodologias, aplicação por linha/período, contexto com índices econômicos, totalizadores e regras de sessão/persistência."
---

# DRE Engine Context

## Objetivo
Esta skill consolida o contexto técnico da DRE para reduzir retrabalho em diagnósticos e evoluções.

Escopo principal:
- Página DRE e fluxos de UI: frontend/pages/dre.py
- Motor de funções e temporalidade: frontend/utils_ext/calc_functions.py

## Arquitetura de alto nível

### 1) Fonte de dados e estados
- Estado principal da DRE: st.session_state["dre_dados"]
- Metodologias: st.session_state["dre_metodologias"]
- Filtros de escopo DRE: st.session_state["dre_filtros"]
- Persistência da grade DRE (atual): sessão atual (session_state), sem restore em arquivo após restart

### 2) Contexto de fórmula
Funções centrais:
- _obter_contexto_formula(dre_dados)
- _preparar_contexto_com_indices(contexto)

Regras:
- O contexto inclui linhas DRE e volumes (TD21, TD62)
- Índices econômicos entram no contexto expandido
- A fórmula pode referenciar variáveis DRE e índices, com validação de tokens

### 3) Pipeline de avaliação
Funções centrais:
- _normalizar_formula_usuario
- _classificar_tokens_formula
- _avaliar_formula
- evaluar_funcao_dinamica_por_mes

Fluxo resumido:
1. Normaliza fórmula do usuário (ex.: decimal com vírgula)
2. Valida tokens (funções, DRE, índices, inválidos)
3. Identifica funções nativas e substitui por placeholders
4. Avalia mês a mês com contexto do mês
5. Retorna série de 12 valores

## Aplicação de metodologias

### Contrato funcional
Função:
- _aplicar_metodologia_em_linha(dre_dados, codigo, met_nome, met_dados, modo_periodo, mes_inicio, mes_fim)

Comportamento esperado:
- Aplica fórmula calculada na linha destino
- Período pode ser Todos ou Intervalo
- Registra metadado de metodologia na linha
- Armazena snapshot de `valores_anteriores` para permitir remoção com restauração
- Retorna (ok, mensagem, alterou)

Função de apoio:
- _remover_metodologia_da_linha(dre_dados, codigo, restaurar_valores=True)

Função de remoção específica:
- _remover_metodologia_especifica_da_linha(dre_dados, codigo, met_nome)

Comportamento esperado da remoção:
- Remove vínculo da metodologia da linha
- Quando houver snapshot, restaura os valores anteriores da linha
- Na remoção específica, limpar `metodologia` (campo legado) antes de recalcular para evitar reentrada da metodologia removida

### Regra crítica de UX
Separar claramente:
- Linhas destino: onde o resultado será escrito
- Referências da fórmula: variáveis/índices lidos durante o cálculo

Essa separação evita erro de interpretação como:
- Usuário quer TD71+TD72 mas fórmula salva contém TD21+TD72

## Motor de cálculo e temporalidade

### Funções nativas suportadas
- SOMA
- MEDIA
- MINIMO
- MAXIMO
- DESVIO_PADRAO

### Parse temporal
Funções:
- parse_argumentos_temporais
- extrair_janela_por_mes
- aplicar_sazonalidade_por_mes

Regras atuais:
- Sem janela e sem sazonalidade explícita: função opera no valor do mês corrente
- Com lag: desloca o mês base
- Com janela: aplica janela temporal por mês
- Com sazonalidade explícita: aplica seleção dinâmica/fixa de meses

## Renderização da grade DRE

### Modo visual (somente leitura)
- Tabela HTML com responsividade via wrapper horizontal
- Formatação compacta de números grandes (mi/bi)
- Badge de metodologia na coluna Metodologia (visual, sem link)
- Remoção por linha disponível em painel nativo **"Remover metodologia aplicada"** com confirmação em `st.dialog`

### Modo edição
- st.data_editor para edição de valores mensais
- Totalizadores não são editáveis
- Aplicação por célula/faixa é feita por painel auxiliar (limitação de eventos de célula no data_editor)

## Encadeamento de metodologias

### Conceito
Uma fórmula pode referenciar o resultado de outra metodologia já aplicada como variável.

Exemplo de sintaxe:
```
METODOLOGIA_BASE = SOMA(TD71;TD72)   → apply first
=MEDIA(0.05 * METODOLOGIA_BASE)      → reference in next formula
```

### Mecanismo
1. Ao aplicar uma metodologia, a série de 12 valores é gravada em `serie_computada` no objeto da metodologia (`dre_metodologias[met_nome]["serie_computada"]`).
2. `_resolver_series_metodologias()` retorna essas séries como contexto adicional.
3. `_obter_contexto_formula()` injeta essas séries no contexto de cálculo.
4. O nome é normalizado via `_normalizar_nome_metodologia_var()` (ex: `Minha Met` → `MINHA_MET`).
5. `_classificar_tokens_formula()` detecta tokens de metodologias na nova categoria `met`.

### Regra anti-recursividade
- `_resolver_series_metodologias()` só retorna dados de metodologias com `serie_computada` já gravada (não recomputa).
- Ciclos são impossíveis porque uma das partes da cadeia ainda não teria série gravada.

### Tags visuais de fórmula (categorias)
- `fn:` funções nativas (azul)
- `dre:` variáveis DRE/volumes (verde)
- `idx:` índices econômicos (ciano)
- `met:` referência a metodologia encadeada (âmbar)
- `inv:` referência inválida (vermelho)

## Design: múltiplas metodologias por linha (implementado)

### Situação atual
- A linha mantém `metodologias_aplicadas` (lista ordenada) e `valores_base`.
- Aplicar uma metodologia nova na mesma linha acumula no final da ordem.
- Reaplicar a mesma metodologia atualiza sua configuração preservando posição.

### Regra de cálculo
- O recálculo da linha roda em ordem de `metodologias_aplicadas`.
- O efeito é somatório sobre `valores_base` (acúmulo de efeitos por metodologia).
- O campo visual `metodologia.nome` vira um resumo concatenado (`MET_A + MET_B + ...`).

### Edição e sincronização
- Ao editar metodologia:
  - linhas removidas de `aplicavel_a` removem apenas essa metodologia da pilha da linha;
  - renomeação troca apenas a entrada correspondente na pilha;
  - a linha é recalculada em seguida.

## Limitações conhecidas e decisões
- st.data_editor não expõe evento robusto de duplo clique por célula
- Para fluxo por célula, usar painel auxiliar com TD/mês base e aplicação por faixa
- Evitar mutação de chave de widget já instanciado no mesmo ciclo do Streamlit
- `href=` em HTML injetado causa reload de página no Streamlit multi-page
- Para manter previsibilidade de UX, evitar ações críticas dentro da célula HTML da tabela
- Para ações críticas (ex.: exclusão), preferir widgets nativos + `session_state` + `st.dialog` (sem navegação de URL)

## Troubleshooting rápido

### Sintoma: valor aplicado não confere
Checklist:
1. Verificar fórmula salva na metodologia
2. Verificar Referências da fórmula no card
3. Confirmar linha destino aplicada
4. Confirmar período (Todos vs Intervalo)
5. Reaplicar e conferir coluna Metodologia na linha destino

### Sintoma: aplicação sem efeito
Checklist:
1. Conferir tokens inválidos
2. Conferir se fórmula começa com =
3. Conferir se resultado calculado difere do valor anterior
4. Conferir se a linha destino está em aplicavel_a
5. Conferir diagnóstico de referências zeradas no escopo atual

### Sintoma: edição da metodologia mantém efeitos antigos
Checklist:
1. Ao salvar edição, sincronizar linhas já afetadas pela metodologia
2. Se linha deixar de ser aplicável, remover metodologia da linha com restauração
3. Se a metodologia for renomeada, atualizar nome no metadado das linhas ainda aplicáveis

### Sintoma: regressão de estado UI
Checklist:
1. Procurar writes diretos em st.session_state de widgets já montados
2. Usar chaves auxiliares pending/remount quando necessário

## Boas práticas para mudanças futuras
- Preservar o helper central de aplicação (_aplicar_metodologia_em_linha)
- Não duplicar lógica de cálculo em múltiplos botões/painéis
- Atualizar README e CHANGELOG quando comportamento funcional mudar
- Validar sempre com:
  - python -m py_compile frontend/pages/dre.py frontend/utils_ext/calc_functions.py

## Arquivos de referência
- frontend/pages/dre.py
- frontend/utils_ext/calc_functions.py
- README.md
- CHANGELOG.md
