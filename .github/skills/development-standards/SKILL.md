---
name: development-standards
description: "Use esta skill para manter padrão de desenvolvimento no projeto: legibilidade, simplicidade, uso de skills existentes, atualização de README/CHANGELOG quando necessário, logs de debug equilibrados e documentação de código (comentários/docstrings) em trechos complexos."
---

# Development Standards

## Objetivo
Padronizar a evolução técnica do projeto com código limpo, consistente e sustentável.

## Regras principais
1. Manter padrão de desenvolvimento já existente no projeto.
2. Não criar arquivos .md de documentação paralela para features/tarefas.
3. Usar README.md e CHANGELOG.md como documentação oficial.
4. Consultar skills existentes antes de implementar (otimização de tempo, tokens e contexto).
5. Priorizar código simples, legível e de fácil manutenção.
6. Adicionar logs de depuração quando necessário, sem poluir terminal.
7. Incluir comentários e docstrings em funções/trechos complexos.

## Política de documentação
Permitido e esperado:
- Atualizar README.md para visão funcional consolidada
- Atualizar CHANGELOG.md para histórico de alterações

Evitar:
- Criar novos .md de feature isolada
- Espalhar documentação operacional fora dos arquivos oficiais

## Política de logs
- Logs devem ser orientados a diagnóstico real
- Preferir flags de debug para ativar/desativar verbosidade
- Evitar prints excessivos em fluxo normal
- Manter mensagens claras e acionáveis

## Política de clareza de código
- Nomes de funções/variáveis explícitos
- Funções curtas quando possível
- Trechos complexos com comentário objetivo
- Docstrings em funções não triviais
- Evitar duplicação de regra de negócio

## Uso de skills (ordem sugerida)
1. streamlit-specialist: para componentes/layout/UI/UX
2. designer-system-guardian: para aderência ao design system
3. dre-engine-context: para DRE e motor de cálculo
4. commit_updates: para padronizar commit/push

## Checklist por entrega
- Skill certa foi consultada antes de codar?
- Código está simples e legível?
- Logs de debug estão equilibrados?
- Funções complexas têm docstring/comentário útil?
- README/CHANGELOG foram atualizados quando necessário?
- Sem criação indevida de .md extra?
