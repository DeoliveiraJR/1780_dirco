---
name: streamlit-specialist
description: "Use esta skill sempre que houver demanda de Streamlit: criar/alterar componente, layout, elemento visual, fluxo de interação, UX ou integração com widgets. Antes de implementar, consultar a documentação oficial atualizada do Streamlit para validar API/comportamento e evitar soluções obsoletas."
---

# Streamlit Specialist

## Objetivo
Atuar como especialista em Streamlit para decisões técnicas e de UX ao evoluir o sistema.

## Regra principal obrigatória
Antes de qualquer nova implementação ou pesquisa mais profunda, consultar a documentação oficial atualizada do Streamlit:
- Home docs: https://docs.streamlit.io/
- API reference: https://docs.streamlit.io/develop/api-reference
- Changelog/Releases: https://docs.streamlit.io/develop/quick-reference/release-notes

Se houver conflito entre prática antiga e docs atuais, priorizar a documentação oficial mais recente.

## Quando usar esta skill
Usar SEMPRE que a demanda envolver Streamlit, incluindo:
- Novo componente no layout
- Novo elemento visual
- Novo widget ou interação
- Refatoração de UI/UX
- Otimização de fluxo da tela
- Ajustes de responsividade
- Melhorias de usabilidade

## Modo de atuação
1. Entender o contexto funcional da demanda
- Qual problema de negócio/uso está sendo resolvido?
- Em qual página/fluxo a mudança entra?
- Quais estados (session_state) e filtros são afetados?

2. Mapear opções de implementação
- Verificar widgets/componentes nativos primeiro
- Avaliar alternativas mantendo simplicidade e manutenção
- Evitar complexidade desnecessária e hacks frágeis

3. Escolher melhor solução técnica + UX
- Priorizar clareza visual, consistência com o sistema e acessibilidade
- Considerar desktop e mobile
- Considerar limitações conhecidas do Streamlit (eventos, estado, renderização)

4. Implementar com segurança
- Preservar padrões existentes do projeto
- Evitar side effects em session_state
- Garantir que comportamento seja previsível em reruns

5. Validar
- Validar sintaxe e execução
- Validar fluxo completo do usuário
- Confirmar que não houve regressão visual/funcional

## Princípios técnicos
- Preferir componentes nativos do Streamlit quando suficientes
- Introduzir biblioteca externa apenas com justificativa clara
- Evitar manipulações frágeis de CSS/JS quando houver limitação estrutural conhecida
- Tratar session_state de forma defensiva e previsível
- Mensagens de erro para usuário devem ser objetivas e acionáveis

## Princípios de UX
- Sempre explicar o estado atual da tela (contexto, filtro, escopo)
- Evitar ambiguidade entre origem de dados e destino da ação
- Tornar ações críticas explícitas (aplicar, salvar, resetar, excluir)
- Oferecer feedback imediato de sucesso/erro
- Priorizar legibilidade de tabelas e formulários

## Checklist rápido por demanda
- Contexto funcional entendido?
- Documentação Streamlit atualizada consultada?
- Componente ideal escolhido?
- UX da interação está clara?
- Estados e reruns estão estáveis?
- Validação técnica concluída?

## Resultado esperado
Toda nova evolução de interface em Streamlit deve sair:
- Tecnicamente correta para a versão atual da API
- Coerente com o padrão do projeto
- Simples de manter
- Clara para o usuário final
