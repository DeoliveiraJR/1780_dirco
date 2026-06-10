---
name: designer-system-guardian
description: "Use esta skill para qualquer alteração de design, layout, UX/UI, tema, tipografia, cores ou componentes visuais. Consolida o design system com base em frontend/styles.py, exige consulta prévia da skill streamlit-specialist e prioriza centralização de estilos no styles.py."
---

# Designer System Guardian

## Objetivo
Manter consistência visual, elegância e profissionalismo do projeto, com design system centralizado em frontend/styles.py.

## Fonte única de verdade de estilo
Arquivo principal:
- frontend/styles.py

Toda mudança de design deve partir deste arquivo como referência de:
- paleta de cores (variáveis e dicionário de cores)
- tipografia (Plus Jakarta Sans para headers e Inter para corpo)
- espaçamentos, raios, sombras e transições
- padrões de botões, inputs, tabelas, métricas, alerts e responsividade

## Regra obrigatória de fluxo
Antes de qualquer implementação de UI/UX:
1. Consultar a skill streamlit-specialist
2. Validar componente ideal e abordagem técnica atualizada de Streamlit
3. Aplicar a solução respeitando o design system deste projeto

Sem essa etapa, não prosseguir com implementação visual.

## Diretrizes de centralização de estilo
1. Preferir sempre estilos centralizados no frontend/styles.py.
2. Evitar CSS inline em páginas, exceto casos pontuais com justificativa técnica.
3. Quando precisar estilo local não centralizado:
- registrar no código o motivo técnico
- explicar por que não foi possível centralizar
- indicar impacto e riscos de manutenção

## Padrões visuais obrigatórios
- Manter linguagem visual elegante e profissional
- Respeitar paleta turquesa/azul já estabelecida
- Preservar contraste, legibilidade e consistência tipográfica
- Priorizar soluções responsivas (desktop e mobile)
- Evitar estética genérica e desalinhada com o padrão atual

## Checklist rápido para mudanças de design
- A mudança foi baseada no frontend/styles.py?
- A streamlit-specialist foi consultada antes?
- Cores e tipografia seguem o padrão do projeto?
- O estilo foi centralizado em styles.py?
- Se não foi centralizado, há justificativa técnica explícita?
- README/CHANGELOG precisam atualização por mudança funcional/visual relevante?

## Manutenção contínua
Sempre que houver alteração de design/layout/UX:
- revisar e atualizar frontend/styles.py quando necessário
- garantir que novos componentes não quebrem o design system
- manter consistência entre páginas
