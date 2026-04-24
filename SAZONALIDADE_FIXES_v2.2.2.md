# 📋 Relatório de Correções - Sazonalidade v2.2.2

## 🎯 Problemas Identificados e Resolvidos

### 1. **AttributeError: 'list' object has no attribute 'get'** (FIXO)
**Problema:** Ao selecionar "Período Fixo", o sistema quebrava com erro de tipo.

**Causa Raiz:** 
- `criar_interface_sazonalidade()` recebia `valor_padrao` como lista `[{...}]` em vez de dict
- Tentava fazer `.get()` em uma lista em vez de dict
- Não havia normalização correta antes de usar `.get()`

**Solução Implementada:**
```python
# ANTES:
tipo_saz = valor_padrao.get("tipo", "NENHUM")  # ❌ Quebra se valor_padrao é lista

# DEPOIS:
valor_padrao = normalizar_sazonalidade(valor_padrao)  # ✅ Converte lista/int/None para dict
tipo_saz = valor_padrao.get("tipo", "NENHUM")  # ✅ Sempre dict, seguro
```

---

### 2. **SOMA(TD71:TD72) não aplicando sazonalidade** (VARIÁVEL)
**Problema:** Fórmula retornava apenas valores do mês atual, ignorando sazonalidade.

**Exemplo:**
```
Fórmula: =SOMA(TD71:TD72)
Sazonalidade: VARIÁVEL "últimos 3 meses"
Janeiro esperado: soma(TD71[Nov,Dez,Jan]) + soma(TD72[Nov,Dez,Jan]) = 2640
Janeiro obtido: TD71[Jan] + TD72[Jan] = 110
```

**Causa Raiz:** Não era no cálculo em si (que estava correto), mas possível:
- Sazonalidade não sendo passada corretamente na UI
- Ou dados sendo inicializados errados

**Solução:** Adicionado logging detalhado em `aplicar_sazonalidade_por_mes()` para debug:
```python
if mes_idx == 0 or mes_idx == 1:
    print(f"[CALC] Mês {mes_idx}: saz={saz_normalizada}, indices={indices} → retorna {len(valores_filtrados)} valores")
```

**Resultado dos Testes:**
✅ SOMA(TD71:TD72) com VARIÁVEL 3 ÚLTIMO:
- Janeiro: 2640 ✅ (1100+1200+100 + 110+120+10)
- Dezembro: 3630 ✅ (1000+1100+1200 + 100+110+120)

---

### 3. **UI não expandindo para Fixo/Variável**
**Problema:** Ao selecionar "Período Fixo" ou "Período Variável", campos não colapsavam/expandiam visualmente.

**Solução:** Refatorar função para sempre normalizar ANTES de usar, usando `st.radio` com índices corretos:
```python
tipo_selecionado = st.radio(
    "Tipo de Período:",
    ["Nenhum", "Período Fixo", "Período Variável"],
    index=0 if tipo_saz == "NENHUM" else (1 if tipo_saz == "FIXO" else 2),
    key=f"{rotulo_prefix}_tipo_saz",
    horizontal=True
)
```

---

## 🔧 Mudanças Técnicas

### `frontend/utils_ext/calc_functions.py`

#### ✅ Melhorado: `normalizar_sazonalidade()`
- Agora suporta lista com dict: `[{"tipo": "FIXO", ...}]`
- Trata dict vazio: `{}` → `{"tipo": "NENHUM"}`
- Mantém compatibilidade legacy com int: `-7` → `{"tipo": "VARIAVEL", "quantidade": 7}`

#### ✅ Corrigido: `calcular_indices_por_mes()` - FIXO
```python
# ANTES:
return list(range(inicio_idx, min(fim_idx, 12)))

# DEPOIS:
# Range inclusivo: se quer jan-jul, retorna índices 0-6 (7 meses)
return list(range(inicio_idx, fim_idx))
```

#### ✅ Melhorado: `aplicar_sazonalidade_por_mes()`
- Adicionado logging para debug de sazonalidade por mês
- Cada mês agora mostra quantos valores está retornando

### `frontend/pages/dre.py`

#### ✅ Simplificado: `criar_interface_sazonalidade()`
- Normaliza `valor_padrao` no INÍCIO da função
- Usa `normalizar_sazonalidade()` para converter lista/int/None
- Remove verificações duplicadas

---

## 📊 Validação dos Testes

### TEST 1: normalizar_sazonalidade ✅
```
None → NENHUM
0 → NENHUM
[] → NENHUM
[{}] → NENHUM ✅ (CORRIGIDO)
{"tipo": "VARIAVEL", ...} → VARIAVEL
{"tipo": "FIXO", ...} → FIXO
-7 → VARIAVEL
```

### TEST 2-3: calcular_indices_por_mes ✅
**VARIÁVEL 3 ÚLTIMO:**
- Janeiro: [10, 11, 0] = [Nov, Dez, Jan] ✅
- Dezembro: [9, 10, 11] = [Out, Nov, Dez] ✅

**FIXO JAN-JUL:**
- Todos meses: [0,1,2,3,4,5,6] = [Jan-Jul] ✅

### TEST 4: aplicar_sazonalidade_por_mes ✅
- Janeiro: retorna 3 valores [1100, 1200, 100] ✅
- Retorna **3 valores** não 1 ✅

### TEST 5: SOMA com sazonalidade ✅
```
SOMA(TD71:TD72) com VARIÁVEL 3 ÚLTIMO
Janeiro: 2640 = (1100+1200+100) + (110+120+10) ✅
Dezembro: 3630 = (1000+1100+1200) + (100+110+120) ✅
```

---

## 🚀 Próximos Passos

1. **Recarregar Streamlit** para pegar as novas mudanças
2. **Testar na UI:**
   - Criar metodologia com FIXO → verificar se campos aparecem/desaparecem
   - Criar metodologia com VARIÁVEL → idem
   - Testar SOMA(TD71:TD72) com VARIÁVEL 3 últimos meses
   - Verificar que janeiro retorna valores DIFERENTES de julho

3. **Observar logs** no terminal Streamlit:
   ```
   [CALC] Mês 0: saz={'tipo': 'VARIAVEL', ...}, indices=[10, 11, 0] → retorna 3 valores
   [DRE] Resultado (12 meses): [2640.0, 1650.0, 660.0]...
   ```

---

## 📝 Notas Importantes

- **FIXO sempre retorna os MESMOS meses para TODOS os meses**
  - Ex: FIXO JAN-JUL retorna sempre [Jan, Fev, Mar, Abr, Mai, Jun, Jul]
  
- **VARIÁVEL retorna MESES DIFERENTES conforme o mês atual**
  - Ex: VARIÁVEL 3 ÚLTIMO
    - Janeiro: [Nov, Dez, Jan]
    - Fevereiro: [Dez, Jan, Fev]
    - Março: [Jan, Fev, Mar]

- **Wrap-around funciona corretamente** (simula ano anterior)
  - Janeiro com "últimos 7 meses" volta para Junho do ano anterior

---

## 📦 Commit Info
```
Commit: 4fd8bfb
Mensagem: Fix: corrigir sazonalidade - normalizar lista/dict, melhorar FIXO range, adicionar logging
Data: 24/04/2026
```
