# 🧪 Guia de Teste - Backend Database Schema Sincronização

## 📌 O que foi corrigido?

**Problema:** TD71 ficava vazio porque dados não sincronizavam entre Simulador e DRE.

**Root Cause:** A página de Upload não passava `usuario_id` para a função `salvar_upload_admin()`, causando exceção silenciosa.

**Solução:** Adicionado parametro `usuario_id` + logging detalhado para diagnosticar problemas.

---

## 🚀 Passo a Passo para Testar

### Pré-requisitos
- ✅ Estar logado como Admin (email: `admin@uan.com.br`, senha: `admin123`)
- ✅ Ter um arquivo Excel com dados de projeção

---

### 1️⃣ **UPLOAD DE DADOS** (Upload page)

1. Acesso: `Menu → Upload`
2. Clique em `Escolha um arquivo Excel`
3. Selecione seu arquivo com dados de projeção
4. Verifique a prévia (dados brutos)
5. Clique em `✔️ Confirmar e Carregar Dados`
6. Verifique a prévia dos dados limpos
7. **IMPORTANTE**: Clique em `💾 Salvar como Base Compartilhada`

**Output esperado:**
```
✅ Arquivo 'seu_arquivo.xlsx' importado com sucesso!
✅ Estrutura de dados atualizada para 2 usuários
📢 Todos os usuários do sistema verão esta base de dados no próximo acesso.
```

**O que deveria acontecer nos bastidores:**
- ✅ Arquivo salvo em: `backend/database/uploads/base_dados_compartilhada.xlsx`
- ✅ JSON criado em: `backend/database/dados/usr_001_dados.json`
- ✅ JSON criado em: `backend/database/dados/usr_002_dados.json`

---

### 2️⃣ **SIMULADOR** (Simulador page)

1. Acesso: `Menu → Simulador`
2. Selecione: `Cliente` → `Categoria` → `Produto`
3. Ajuste a curva conforme desejado (usando sliders ou editando valores)
4. Clique em `💾 Salvar`

**Output esperado:**
```
✅ Simulação 'Simulação 2026' salva com sucesso!
✅ Simulação salva! ID: uma_id_qualquer...
```

**O que deveria acontecer nos bastidores:**
- ✅ Função `adicionar_simulacao()` salvou simulação
- ✅ Função `sincronizar_curva_para_backend()` foi chamada
- ✅ JSON em `backend/database/dados/usr_001_dados.json` foi atualizado com nova curva

---

### 3️⃣ **DRE GERENCIAL** (DRE page)

1. Acesso: `Menu → DRE`
2. Selecione: `Cliente` → `Categoria` → `Produto` **IGUAL ao que você simulou**
3. Vá para a aba `📝 Editor DRE`

**Output esperado:**
```
✅ TD71 (Receita Financeira) deve estar PREENCHIDO com suas valores!
```

**Resultado:**
- Se tudo funcionar: TD71 terá os valores que você ajustou no Simulador
- Se não funcionar: TD71 ainda estará zerado

---

## 🔍 Debugar se não funcionar

### Opção 1: Verificar arquivos criados

```bash
# Terminal - na pasta backend/
python debug_schema.py

# Deve mostrar:
# ✅ 2 arquivo(s) encontrado(s):
#    - usr_001_dados.json
#    - usr_002_dados.json
```

### Opção 2: Verificar dados de um usuário

```bash
python debug_schema.py usuario usr_001

# Deve mostrar:
# ✅ METADATA
# ✅ PRODUTOS: N encontrados
```

### Opção 3: Verificar curva específica

```bash
python debug_schema.py curva usr_001 "CLIENTE" "CATEGORIA" "PRODUTO" 2026

# Deve mostrar:
# ✅ CURVA ENCONTRADA:
#    Valores: [v1, v2, v3, ...]
#    Populated: True
```

---

## 🐛 Possíveis Problemas e Soluções

### ❌ Problema: "Erro: usuario_id não definido"

**Causa:** Não está logado ou sessão expirou

**Solução:**
1. Faça logout (`Menu → Perfil → Logout`)
2. Faça login novamente
3. Repita o processo de upload

---

### ❌ Problema: Upload "salva" mas sem files JSON criados

**Causa:** Usuário logado não é admin

**Solução:**
1. Verifique qual email está usando
2. Deve ser: `admin@uan.com.br`
3. Se não for, faça login com admin account

---

### ❌ Problema: Arquivos JSON criados mas TD71 ainda vazio

**Causa:** DRE está procurando cliente/categoria/produto errado

**Solução:**
1. Verifique exatamente qual produto você simulou
2. Na DRE, selecione **EXATAMENTE** o mesmo:
   - Cliente (maiúsculas/minúsculas importam)
   - Categoria (deve ser exato)
   - Produto (deve ser exato)

---

### ❌ Problema: Arquivo JSON existe mas está vazio

**Causa:** Estrutura do Excel não esperada ou falta de dados

**Solução:**
1. Verifique se Excel tem as colunas esperadas:
   - `TIPO_CLIENTE`
   - `CATEGORIA`
   - `PRODUTO`
   - `MES` ou `MES_NUM`
   - `ANO`
   - `PROJETADO_ANALITICO`
   - `PROJETADO_MERCADO`
   - `PROJETADO_AJUSTADO`

---

## 📊 Checklist de Sucesso

- [ ] Upload realizado e "Salvar como Base Compartilhada" clicado
- [ ] `backend/database/dados/usr_001_dados.json` criado
- [ ] Simulador: simulação salva com sucesso
- [ ] Logs mostram "Curva sincronizada para backend"
- [ ] DRE: TD71 está preenchido quando abre a página
- [ ] TD71 tem os mesmos valores que ajustou no Simulador

---

## 📝 Logs Esperados ao Executar

Ao fazer upload, você deveria ver logs como:

```
[DB] Iniciando parse XLSX → JSON...
[DB] 2 usuários encontrados para sincronizar
[DB] Parseando para usuário: usr_001
[DB]   ✅ Schema criado: 15 produtos
[DB]   ✅ Dados salvos com sucesso
[DB] Parseando para usuário: usr_002
[DB]   ✅ Schema criado: 15 produtos
[DB]   ✅ Dados salvos com sucesso
[DB] Upload salvo e parseado: backend/database/uploads/base_dados_compartilhada.xlsx
```

---

## ✅ Se Tudo Funcionar

Parabéns! Você tem:

1. **Upload → Backend**: Dados persistidos em JSON
2. **Simulador → Backend**: Curvas sincronizadas
3. **DRE ← Backend**: TD71 sempre preenchido
4. **Persistência**: Dados sobrevivem reconexão/reload

---

## 🆘 Ainda com Problemas?

Execute o teste automatizado:

```bash
cd /workspaces/1780_dirco/backend
python test_fluxo.py
```

Este teste simula o fluxo completo e mostra exatamente onde falhar.
