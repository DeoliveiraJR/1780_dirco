# 🔄 IMPLEMENTAÇÃO: Sistema de Update e Persistência de Dados

## 📋 Resumo Executivo

Foi implementado um sistema completo de **mock database** que permite:

1. **Upload Controlado**: Apenas administradores podem fazer upload de arquivos
2. **Base Compartilhada**: Todos os usuários veem a mesma base de dados (controlada por admin)
3. **Curvas Individuais**: Cada usuário tem suas simulações/curvas ajustadas isoladas
4. **Persistência em Arquivos**: Dados armazenados em pasta `backend/database/` (simula banco de dados)

---

## 🏗️ Arquitetura Implementada

### 1️⃣ Estrutura de Pastas

```
backend/
├── database.py                    # Gerenciador de persistência
└── database/
    ├── users.json               # Usuários mockados
    ├── uploads/
    │   └── base_dados_compartilhada.xlsx  # Arquivo base (todos veem)
    ├── simulacoes/
    │   ├── usr_001_simulacoes.json       # Curvas do admin
    │   ├── usr_002_simulacoes.json       # Curvas do usuário comum
    │   └── ...
    └── metadata/
        └── ultimo_upload.json            # Info do último upload
```

### 2️⃣ Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────┐
│                     NOVO FLUXO DE DADOS                         │
└─────────────────────────────────────────────────────────────────┘

ADMIN FOCA UPLOAD
    │
    ├─→ Valida arquivo Excel
    ├─→ Verifica permissão (role = "admin")
    ├─→ Salva em: backend/database/uploads/base_dados_compartilhada.xlsx
    ├─→ Salva metadata em: backend/database/metadata/ultimo_upload.json
    ├─→ TODOS os usuários veem a mesmo arquivo ✓
    └─→ Curvas ajustadas de CADA usuário permanecem isoladas ✓

USUÁRIO COMUM/ADMIN ABRE SIMULADOR
    │
    ├─→ Carrega dados do database compartilhado
    │   (arquivo base_dados_compartilhada.xlsx)
    │
    ├─→ Aplica suas PRÓPRIAS curvas ajustadas
    │   (carregadas de backend/database/simulacoes/{usuario_id}_simulacoes.json)
    │
    └─→ Cada usuário vê: base + suas curvas

USUÁRIO SALVA SIMULAÇÃO
    │
    ├─→ Curva é salva APENAS para esse usuário
    ├─→ Arquivo: backend/database/simulacoes/{usuario_id}_simulacoes.json
    ├─→ Outros usuários NÃO veem essa curva
    └─→ Próxima vez que logar, suas curvas são restauradas
```

---

## 👥 Usuários Mockados

### Admin
- **Email**: `admin@uan.com.br`
- **Senha**: `admin123`
- **Role**: `admin`
- **Permissões**: ✓ Upload de arquivos, ✓ Visualizam base compartilhada

### Usuário Comum
- **Email**: `teste@uan.com.br`
- **Senha**: `123456`
- **Role**: `usuario`
- **Permissões**: ✗ Upload, ✓ Visualizam base compartilhada, ✓ Criar simulações

---

## 📁 Módulos Implementados

### `backend/database.py`

Gerenciador central de persistência com funções para:

#### **Gerenciamento de Usuários**
```python
validar_login(email, senha) → (bool, usuario_dict)
obter_usuario_por_email(email) → usuario_dict
eh_admin(usuario) → bool
```

#### **Base de Dados Compartilhada**
```python
salvar_upload_admin(arquivo_bytes, nome_arquivo, usuario_id) 
  → (bool, mensagem)
  
carregar_base_dados_compartilhada() → DataFrame
obter_metadados_ultimo_upload() → dict
```

#### **Curvas por Usuário**
```python
salvar_curva_usuario(usuario_id, cliente, categoria, produto, curva)
  → (bool, mensagem)
  
carregar_curvas_usuario(usuario_id) → List[Dict]
obter_curva_usuario(usuario_id, cliente, categoria, produto) → List[float]
deletar_curva_usuario(usuario_id, combo_key) → (bool, mensagem)
```

### `frontend/data_manager.py` (Extensões)

Novas funções para integração com o database mockado:

```python
carregar_base_dados_compartilhada() → DataFrame
salvar_upload_admin(arquivo_bytes, nome_arquivo) → (bool, mensagem)
eh_usuario_admin() → bool
sincronizar_curva_com_arquivo(cliente, categoria, produto, curva) → bool
carregar_curvas_usuario_do_arquivo() → Dict
restaurar_curvas_de_arquivo() → int
```

---

## 🔐 Controle de Permissões

### Página de Upload (`frontend/pages/upload.py`)

✓ **Novo**: Verificação de admin no início da página

```python
if not eh_usuario_admin():
    # Mostra mensagem de acesso restrito
    # Permite apenas visualizar dados (não fazer upload)
    # Redireciona para aba de dados carregados
```

✓ **Novo**: Botão "Salvar como Base Compartilhada"

Após processar arquivo, admin vê botão para salvar como base compartilhada que todos veerão.

---

## 🔄 Fluxo de Autenticação

### `frontend/pages/autenticacao.py` (Atualizado)

```python
# Novo: Integração com database mockado
autenticado, usuario = validar_login(email, senha)

if autenticado:
    st.session_state.usuario_id = usuario['id']
    st.session_state.usuario_nome = usuario['nome']
    st.session_state.usuario_role = usuario['role']     # 'admin' ou 'usuario'
    st.session_state.usuario_email = email
```

---

## 📊 Comportamento Esperado

### Cenário 1: Admin faz Upload

1. **Login**: admin@uan.com.br / admin123
2. **Vai para Upload**
3. **Seleciona arquivo** Excel
4. **Processa dados**
5. **Clica "Salvar como Base Compartilhada"**
   - ✅ Arquivo salvo em: `backend/database/uploads/base_dados_compartilhada.xlsx`
   - ✅ Metadata salvo em: `backend/database/metadata/ultimo_upload.json`
6. **Todos os usuários** veem a nova base no próximo acesso

### Cenário 2: Usuário Comum acessa Simulador

1. **Login**: teste@uan.com.br / 123456
2. **Vai para Simulador**
3. **Carrega dados** → Busca em `backend/database/uploads/base_dados_compartilhada.xlsx`
4. **Aplica suas curvas** → Carregadas de `backend/database/simulacoes/usr_002_simulacoes.json`
5. **Edita e salva simulação**
   - ✅ Curva salva APENAS no arquivo do usuário
   - ✅ Outros usuários NÃO veem essa curva
6. **Próximo login** → Suas curvas são restauradas automaticamente

### Cenário 3: Usuário Comum tenta fazer Upload

1. **Login**: teste@uan.com.br / 123456
2. **Vai para Upload**
3. **Vê aviso**: "🔒 Acesso Restrito - Apenas Administradores"
4. **Pode**: Visualizar dados da base compartilhada
5. **Não pode**: Fazer upload de novos arquivos

---

## 🔄 Sincronização de Dados

### Na Página de Simulador

As curvas ajustadas são sincronizadas em **dois pontos**:

1. **Ao salvar uma simulação**: 
   - Curva é salva em `st.session_state.curvas_ajustadas_persistentes`
   - Chamada `sincronizar_curva_com_arquivo(...)` para persistir em arquivo
   
2. **Ao fazer login**:
   - Função `restaurar_curvas_de_arquivo()` carrega todas as curvas do usuário
   - Restaura no `st.session_state`

---

## ✅ Benefícios Implementados

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Base Compartilhada** | ❌ Cada usuário tinha seus dados | ✅ Todos veem a mesma base |
| **Controle de Upload** | ❌ Sem verificação | ✅ Apenas admin pode fazer upload |
| **Curvas Individuais** | ✓ Funcionava | ✓ Agora persistem em arquivo |
| **Persistência** | ⚠️ Apenas session_state (volatilidade) | ✅ Arquivos (durável) |
| **Isolamento de Dados** | ❌ Tudo misturado | ✅ Cada usuário tem seu arquivo |
| **Auditoria** | ❌ Sem registro | ✅ Metadata de uploads registrada |

---

## 🧪 Como Testar

### Teste 1: Autenticação
```
1. Tente fazer login com credenciais inválidas
   → Deve rejeitar
2. Tente login como admin@uan.com.br / admin123
   → Deve aceitar e indicar "Administrador"
3. Tente login como teste@uan.com.br / 123456
   → Deve aceitar e indicar "Usuário"
```

### Teste 2: Controle de Upload
```
1. Login como admin
2. Vá em Upload
   → Deve mostrar interface de upload e botão de salvar
3. Logout e faça login como usuário comum
4. Vá em Upload
   → Deve mostrar "Acesso Restrito"
   → Deve permitir visualizar dados (tab "Dados Carregados")
```

### Teste 3: Base Compartilhada
```
1. Admin faz upload de um arquivo
2. Salva como "Base Compartilhada"
3. Logout
4. Login como usuário comum
5. Vá para Simulador
   → Deve carregar os dados do arquivo que admin fez upload
```

### Teste 4: Curvas Individuais
```
1. Login como admin
2. Vá para Simulador
3. Edite uma curva e salve como "Simulação Admin"
4. Logout
5. Login como usuário comum
6. Vá para Simulador
   → NÃO deve ver a simulação do admin
7. Crie sua própria simulação
8. Logout e login novamente
   → Suas simulações devem estar lá (restauradas)
```

---

## 📝 Arquivos Modificados

### Criados
- ✅ `backend/database.py` - Gerenciador mock database
- ✅ `backend/database/users.json` - Usuários mockados
- ✅ `backend/database/uploads/` - Pasta para arquivos compartilhados
- ✅ `backend/database/simulacoes/` - Pasta para curvas por usuário
- ✅ `backend/database/metadata/` - Pasta para metadados

### Atualizados
- ✅ `frontend/pages/autenticacao.py` - Integração com database
- ✅ `frontend/pages/upload.py` - Controle de admin e salvar compartilhado
- ✅ `frontend/data_manager.py` - Novas funções de integração

---

## 🚀 Próximos Passos (Sugestões)

1. **Adicionar interface de admin** para:
   - Listar usuários conectados
   - Ver histórico de uploads
   - Gerenciar permissões

2. **Exportação de simulações**:
   - Permitir usuários exportarem suas simulações em Excel
   - Permitir admin exportar relatório consolidado

3. **Versionamento de uploads**:
   - Manter histórico de arquivos anteriores
   - Permitir voltar para versão anterior se necessário

4. **Dashboard de admin**:
   - Visualizar métricas da base compartilhada
   - Ver quantos usuários estão usando o sistema
   - Monitorar últimas alterações

---

## 📌 Notas Importantes

1. **Compatibilidade Mantida**: Todas as funcionalidades existentes continuam funcionando
2. **Session State**: Ainda usado para performance (cache), mas sincronizado com arquivos
3. **Mock Database**: Em produção, seria substituído por um banco de dados real (PostgreSQL, etc.)
4. **Segurança**: Senhas armazenadas em JSON (apenas para mock). Em produção, usar hash + salt.

---

**Status**: ✅ **IMPLEMENTADO E PRONTO PARA TESTES**

Data de Implementação: Março 2026
Desenvolvedor: GitHub Copilot
