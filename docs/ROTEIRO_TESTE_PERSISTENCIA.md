# 🧪 Roteiro de Testes - Persistência de Simulações

Este documento descreve os passos para testar a funcionalidade de persistência de curvas e simulações no Simulador.

---

## 📋 Pré-requisitos

1. Aplicação rodando (`streamlit run frontend/app.py`)
2. Dados importados via página de Upload (arquivo Excel)
3. Console do navegador aberto (F12) para visualizar logs

---

## 🔬 Cenário 1: Salvar Simulação e Persistir Curva

### Passos:
1. **Acessar Simulador**: Navegue para a página do Simulador
2. **Selecionar Filtros**:
   - Cliente: `PJ` (ou qualquer disponível)
   - Categoria: `CAPTAÇÕES`
   - Produto: Selecione um produto disponível
3. **Ajustar Curva**:
   - Arraste os pontos da curva "Ajustada" (verde) no gráfico
   - Observe os valores mudarem
4. **Salvar Simulação**:
   - Preencha o nome: "Teste Persistência 1"
   - Clique no botão "💾 Salvar"

### ✅ Resultado Esperado:
- Toast verde: "✅ Simulação salva com sucesso!"
- No console (F12): 
  ```
  [PERSIST] Curva salva: PJ::CAPTAÇÕES::PRODUTO = [...]
  [PERSIST] DataFrame atualizado: CAPTAÇÕES/PRODUTO com 12 meses
  ```

---

## 🔬 Cenário 2: Mudar Filtros e Verificar Persistência

### Passos:
1. **Mudar para outro produto**:
   - Selecione um produto diferente na mesma categoria
   - Observe que a curva ajustada muda
2. **Voltar ao produto original**:
   - Selecione novamente o produto do Cenário 1

### ✅ Resultado Esperado:
- Toast azul: "📂 Carregada simulação salva para [PRODUTO]"
- A curva ajustada deve exibir os valores salvos anteriormente
- No console:
  ```
  [PERSIST] Curva carregada do banco: PJ::CAPTAÇÕES::PRODUTO
  ```

---

## 🔬 Cenário 3: Verificar Totais por Categoria

### Passos:
1. Com uma ou mais curvas salvas, role a página até a seção **"🗂️ Análises por Categoria"**
2. Observe os cards de cada categoria
3. Compare o valor "Proj. Ajustada" com os valores esperados

### ✅ Resultado Esperado:
- Os totais nos cards devem refletir os ajustes salvos
- Os gráficos de barras devem mostrar a curva "Ajustada" com valores diferentes da "Analítica"

---

## 🔬 Cenário 4: Histórico de Simulações

### Passos:
1. Salve múltiplas simulações para diferentes produtos
2. Expanda o painel **"📂 Simulações Salvas"**
3. Clique em "🔄" para restaurar uma simulação

### ✅ Resultado Esperado:
- Lista mostra todas as simulações salvas com nome, categoria e produto
- Ao restaurar, os filtros mudam automaticamente e a curva é carregada
- No console:
  ```
  [PERSIST] Simulação restaurada: [ID]
  ```

---

## 🔬 Cenário 5: Reload da Página

### Passos:
1. Salve uma simulação
2. Pressione F5 para recarregar a página
3. Selecione os mesmos filtros (cliente/categoria/produto)

### ✅ Resultado Esperado:
- A curva salva deve ser carregada automaticamente
- ⚠️ **Nota**: Dados em `session_state` são perdidos no reload. Para persistência real, seria necessário backend/banco de dados.

---

## 📊 Logs Esperados no Console

### Quando salva:
```
[PERSIST] Curva salva: Cliente::Categoria::Produto = [valor1, valor2, ...]
[PERSIST] DataFrame atualizado: Categoria/Produto com 12 meses
```

### Quando carrega:
```
[PERSIST] Curva carregada do banco: Cliente::Categoria::Produto
```

### Quando aplica todas as curvas (início da sessão):
```
[PERSIST] Aplicadas X curvas salvas no DataFrame
```

---

## 🐛 Problemas Conhecidos

1. **Dados não persistem entre sessões**: O `session_state` do Streamlit é efêmero. Para persistência real, integrar com banco de dados.

2. **Muitas simulações podem sobrecarregar**: O histórico cresce indefinidamente na sessão.

---

## 📝 Checklist de Validação

- [ ] Curva ajustada não reseta ao mudar filtros
- [ ] Toast aparece ao carregar curva salva
- [ ] Botão "Salvar" grava corretamente
- [ ] Lista de simulações mostra histórico
- [ ] Botão "Restaurar" funciona
- [ ] Totais por categoria refletem ajustes
- [ ] Console mostra logs [PERSIST]

---

## 🛠️ Comandos Úteis para Debug

```python
# Ver curvas salvas no session_state
import streamlit as st
print(st.session_state.curvas_ajustadas_persistentes)

# Ver histórico de simulações
print(st.session_state.historico_simulacoes)

# Ver simulações do usuário
print(st.session_state.simulacoes)
```
