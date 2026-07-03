---
name: commit_updates
description: "Use esta skill quando o usuário pedir para commitar/pushar alterações. Padroniza mensagens de commit em português com tipo (feat, fix, docs, refactor, chore, test), emoji por tipo, título curto focado na principal entrega e confirmação obrigatória do usuário antes de executar commit."
---

# Commit Updates

## Objetivo
Padronizar commits deste projeto com mensagens curtas, claras e consistentes.

## Regras obrigatórias
1. Sempre usar tipo no título: feat, fix, docs, refactor, chore, test.
2. Sempre escrever em português.
3. Sempre manter o título curto, focado na principal tarefa entregue.
4. Sempre perguntar antes de commitar: confirmar se a tarefa foi finalizada e se pode prosseguir.
5. Só executar commit após confirmação explícita do usuário.
6. Sempre usar emoji antes do tipo.

## Formato padrão da mensagem
`<emoji> <tipo>: <título curto em português>`

Exemplo:
`⚙️ feat: implementa a lógica das metodologias da DRE`

## Mapa emoji por tipo
- feat: ⚙️
- fix: 🐛
- docs: 📝
- refactor: ♻️
- chore: 🔧
- test: ✅

## Fluxo recomendado
1. Revisar mudanças no git status.
2. Definir o conjunto de arquivos do commit (evitar mudanças não relacionadas).
3. Propor mensagem de commit no padrão.
4. Perguntar ao usuário se pode prosseguir com commit.
5. Após confirmação, executar commit.
6. Executar push para a branch atual.

## Checklist rápido
- Tarefa principal está concluída?
- Mensagem está curta e em português?
- Tipo e emoji estão corretos?
- Usuário confirmou autorização para commitar?
