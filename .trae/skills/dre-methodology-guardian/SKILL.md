---
name: "dre-methodology-guardian"
description: "Orienta metodologias e funcoes nativas da DRE. Use ao criar, revisar, depurar ou documentar formulas, sintaxe, regras temporais e comportamento de calculo."
---

# DRE Methodology Guardian

## Objetivo
Centralizar as regras das metodologias de calculo da DRE, incluindo:
- funcoes nativas suportadas
- sintaxe valida
- comportamento temporal por mes
- aliases aceitos
- checklist de implementacao e validacao

Use esta skill quando:
- o usuario pedir nova metodologia nativa
- houver ajuste em parser de formulas
- for preciso validar sintaxe de funcoes na DRE
- houver duvida sobre janela temporal, lag, sazonalidade ou referencias
- for necessario documentar o catalogo funcional das metodologias

## Arquivos principais
- `frontend/pages/dre.py`
- `frontend/utils_ext/calc_functions.py`

## Regra-base do motor
- A DRE calcula metodologias mes a mes.
- Cada formula retorna uma serie de 12 valores.
- A linha destino recebe o resultado da formula aplicada no periodo escolhido.
- Referencias da formula e linhas destino devem ser tratadas separadamente.
- Mes vazio e zero explicito NAO sao equivalentes: vazio deve ser ignorado nas funcoes nativas; zero digitado deve participar do calculo.

## Funcoes nativas atuais

### SOMA
- Objetivo: somar os valores selecionados.
- Sintaxe:
  - `=SOMA(TD71)`
  - `=SOMA(TD71; 7)`
- Regra temporal:
  - sem janela: usa o valor do mes corrente
  - com janela positiva: usa os proximos `N` meses
  - com janela negativa: usa os ultimos `N` meses
- Regra de vazio:
  - segue o comportamento do Excel: ignora vazios
  - soma `0` normalmente quando a celula foi preenchida com zero

### MEDIA
- Objetivo: calcular a media aritmetica.
- Sintaxe:
  - `=MEDIA(TD21)`
  - `=MEDIA(TD21; -6)`
- Regra temporal:
  - mesma regra de janela da `SOMA`
- Regra de vazio:
  - meses vazios devem ser ignorados, como no Excel
  - `0` so deve entrar na media quando tiver sido explicitamente preenchido

### MEDIA_INTERNA
- Objetivo: calcular a media interna no estilo Excel `TRIMMEAN`, descartando extremos.
- Sintaxe recomendada:
  - `=MEDIA_INTERNA(TD21; 0,2)`
  - `=MEDIA_INTERNA(TD21; 0,2; -6)`
  - `=MEDIA_INTERNA(TD21; 0,2; -6; 1)`
- Aliases aceitos:
  - `=MEDIA.INTERNA(...)`
  - `=MÉDIA.INTERNA(...)`
  - `=TRIMMEAN(...)`
- Regra de calculo:
  1. coleta os valores da referencia no mes corrente ou na janela temporal
  2. ignora meses vazios, preservando zeros explicitos
  3. ordena os valores
  4. calcula `total_descartado = floor(n * percentual)`
  5. ajusta para multiplo par: `total_descartado -= total_descartado % 2`
  6. remove metade do inicio e do fim
  7. calcula a media do miolo restante
- Regras de entrada:
  - percentual deve estar entre `0` e `1`
  - o uso prioritario e sobre uma linha com janela mensal
  - exemplo de negocio: `TD71 = MEDIA_INTERNA(TD21; 0,2; -6)`

### MINIMO
- Objetivo: retornar o menor valor do conjunto.
- Sintaxe:
  - `=MINIMO(TD71)`
  - `=MINIMO(TD71; -12)`
- Regra de vazio:
  - ignora meses vazios
  - considera `0` apenas quando preenchido explicitamente

### MAXIMO
- Objetivo: retornar o maior valor do conjunto.
- Sintaxe:
  - `=MAXIMO(TD71)`
  - `=MAXIMO(TD71; 7)`
- Regra de vazio:
  - ignora meses vazios
  - considera `0` apenas quando preenchido explicitamente

### DESVIO_PADRAO
- Objetivo: calcular o desvio padrao populacional.
- Sintaxe:
  - `=DESVIO_PADRAO(TD90; -5; 1)`
- Regra de vazio:
  - ignora meses vazios
  - considera `0` apenas quando preenchido explicitamente

## Regras de sintaxe
- A formula deve comecar com `=`.
- O nome das funcoes deve ser normalizado antes da classificacao de tokens.
- Decimal com virgula deve ser convertido para ponto internamente.
- A sintaxe temporal padrao e:
  - `FUNCAO(referencia)`
  - `FUNCAO(referencia; janela)`
  - `FUNCAO(referencia; janela; lag)`
- No caso de `MEDIA_INTERNA`, a sintaxe e:
  - `MEDIA_INTERNA(referencia; percentual; janela_opcional; lag_opcional)`

## Regras temporais
- Todas as janelas temporais devem usar serie historica real por `ano/mes`, nunca array circular de 12 posicoes.
- `janela > 0`: proximos `N` meses reais apos o mes base
- `janela < 0`: ultimos `N` meses reais anteriores ao mes base
- `lag`: desloca o mes base antes de extrair a janela
- sem janela: a funcao opera no valor do mes corrente
- com sazonalidade explicita: o motor usa a selecao dinamica/fixa definida na metodologia sobre a linha do tempo real
- em validacoes estilo Excel, `-6` deve ser interpretado como "seis meses anteriores", sem incluir o mes base
- meses ausentes na janela historica NAO devem virar `0` artificialmente
- a janela deve levar somente meses preenchidos; zeros explicitos permanecem validos

## Regras de preenchimento da DRE
- Linhas variaveis devem manter flags de preenchimento por mes:
  - `projetado_preenchido`
  - `valores_base_preenchidos`
  - `valores_preenchidos`
- Ao editar a grade:
  - se o usuario digitar `0`, a flag do mes deve permanecer `True`
  - se o usuario limpar a celula, a flag do mes deve virar `False`
- Ao salvar/restaurar simulacoes da DRE, essas flags devem ser persistidas junto com os valores

## Diretrizes de implementacao
- Preservar `evaluar_funcao_dinamica_por_mes()` como ponto principal do calculo mensal.
- Evitar duplicar parser ou regra temporal entre `dre.py` e `calc_functions.py`.
- O contexto da formula deve expor `serie_historica` para referencias que precisem cruzar ano.
- Funcoes com assinatura especial, como `MEDIA_INTERNA`, devem ter parse proprio no motor.
- Sempre atualizar:
  - `FUNCOES_NATIVAS`
  - `DESCRICOES_FUNCOES`
  - `EXEMPLOS_FUNCOES`
  - normalizacao de formula em `dre.py`
  - classificacao de tokens na DRE

## Checklist de validacao
- A formula normalizada continua legivel na UI?
- Tokens da formula aparecem como validos na DRE?
- O calculo retorna 12 valores?
- Mes vazio ficou fora do calculo e `0` explicito continuou contando?
- `python -m py_compile frontend/pages/dre.py frontend/utils_ext/calc_functions.py` passa?
- A metodologia funciona no fluxo real de aplicar/remover/reaplicar?
- Se houver alias estilo Excel, ele esta normalizado para o nome interno correto?

## Exemplos uteis
- `=MEDIA(TD21; -6)`
- `=MEDIA_INTERNA(TD21; 0,2; -6)`
- `=TRIMMEAN(TD21; 0,2; -6)`
- `=MAXIMO(TD71; 3)`
- `=DESVIO_PADRAO(IPCA; -5; 1)`
