# 🔄 GUIA DE USO - Sistema de Persistência e Base Compartilhada

## 📖 Visão Geral

Este documento explica como o novo sistema de **base compartilhada** e **curvas individuais** funciona.

---

## 👥 Dois Tipos de Usuários

### 1️⃣ **ADMINISTRADOR**
Credenciais:
- **Email**: `admin@uan.com.br`
- **Senha**: `admin123`

**Permissões**:
- ✅ Fazer upload de novos arquivos Excel
- ✅ Salvar arquivo como "Base Compartilhada"
- ✅ Visualizar dados compartilhados
- ✅ Criar suas próprias simulações

---

### 2️⃣ **USUÁRIO COMUM**
Credenciais:
- **Email**: `teste@uan.com.br`
- **Senha**: `123456`

**Permissões**:
- ❌ Fazer upload (página será bloqueada)
- ✅ Visualizar base compartilhada (feita pelo admin)
- ✅ Criar suas próprias simulações
- ✅ Editar curvas (apenas suas)

---

## 🔄 Fluxo Principal

```
PASSO 1: Admin faz Upload
├─→ Upload página → Seleciona arquivo Excel
├─→ Valida e processa dados
├─→ Clica "Salvar como Base Compartilhada"
└─→ Arquivo salvo em: backend/database/uploads/base_dados_compartilhada.xlsx

PASSO 2: Todos os usuários carregam dados
├─→ Ao fazer login e ir ao Simulador
├─→ Sistema carrega: base_dados_compartilhada.xlsx
├─→ Aplica as simulações individuais de cada um
└─→ Resultado final: Base + Curvas individuais

PASSO 3: Usuário edita sua curva
├─→ Edita valores no gráfico
├─→ Salva simulação com um nome
├─→ Curva é salva APENAS para esse usuário
├─→ Arquivo: backend/database/simulacoes/{usuario_id}_simulacoes.json
└─→ Outros usuários NÃO veem essa curva
```

---

## 🎬 Como Usar - Passo a Passo

### **CENÁRIO 1: Admin Faz Upload**

1. **Acesse a aplicação**
   ```
   streamlit run frontend/app.py
   ```

2. **Faça login como Admin**
   - Email: `admin@uan.com.br`
   - Senha: `admin123`

3. **Vá em "Upload"**
   - Na barra lateral, clique em "Upload da base de dados"

4. **Selecione um arquivo Excel**
   - Arquivo deve ter as colunas: DATA_COMPLETA, MES, ANO, CATEGORIA, PRODUTO, etc.

5. **Processe os dados**
   - Clique em "✔️ Confirmar e Carregar Dados"
   - Sistema valida e normaliza

6. **Salve como Base Compartilhada**
   - Após processar, você verá botão "💾 Salvar como Base Compartilhada"
   - Clique para salvar
   - Mensagem de sucesso: "✅ Todos os usuários do sistema verão esta base..."

✅ **Feito!** Todos os usuários agora veem este arquivo.

---

### **CENÁRIO 2: Usuário Comum Acessa Simulador**

1. **Faça login como Usuário Comum**
   - Email: `teste@uan.com.br`
   - Senha: `123456`

2. **Vá em "Simulador"**
   - Na barra lateral

3. **Dados carregam automaticamente**
   - Sistema busca o arquivo que admin fez upload
   - Mostra base compartilhada

4. **Crie uma simulação**
   - Selecione Cliente, Categoria, Produto
   - Edite a curva "Ajustada" (drag-and-drop)
   - Clique "Sincronizar"

5. **Salve a simulação**
   - Clique "Salvar Simulação"
   - Digite um nome (ex: "Cenário Otimista")
   - Clique "Salvar"

6. **Faça logout e login novamente**
   - Vá para Upload (vai ver "🔒 Acesso Restrito")
   - Volte para Simulador
   - **Suas simulações estarão lá!** 💾

✅ **Curva salva apenas para você!**

---

### **CENÁRIO 3: Usuário Comum Tenta Fazer Upload**

1. **Faça login como Usuário Comum**

2. **Vá em "Upload"**

3. **Vê mensagem**
   ```
   🔒 Acesso Restrito
   
   Apenas usuários com permissão de Administrador podem fazer upload
   
   ✓ Visualizar a base de dados compartilhada
   ✗ Fazer upload de novos dados (apenas admin)
   ✓ Criar suas próprias simulações
   ```

4. **Pode visualizar dados**
   - Clique na aba "📊 Dados Carregados"
   - Vê o que foi enviado pelo admin

❌ **Não pode fazer upload** (como esperado)

---

## 📊 Estrutura de Arquivos

```
backend/database/
├── users.json                              # Usuários mockados
│   └── [admin@uan.com.br, teste@uan.com.br]
│
├── uploads/
│   └── base_dados_compartilhada.xlsx      # Arquivo compartilhado (TODOS veem)
│
├── simulacoes/
│   ├── usr_001_simulacoes.json            # Simulações do ADMIN (isoladas)
│   ├── usr_002_simulacoes.json            # Simulações do USUÁRIO COMUM (isoladas)
│   └── ...
│
└── metadata/
    └── ultimo_upload.json                 # Info sobre último upload
```

---

## 🔐 Controle de Permissões

### **Verificação de Admin**

A função `eh_usuario_admin()` verifica se:
```python
st.session_state.usuario_role == "admin"
```

Definida durante login:
```python
st.session_state.usuario_role = usuario.get("role")  # "admin" ou "usuario"
```

### **Proteção de Upload**

Na página de upload:
```python
if not eh_usuario_admin():
    st.error("🔒 Acesso Restrito")
    # Mostra dados mas não permite upload
    return
```

---

## 💾 Persistência de Dados

### **Base Compartilhada**

```
✓ Arquivo: backend/database/uploads/base_dados_compartilhada.xlsx
✓ Todos os usuários veem
✓ Apenas admin pode atualizar
✓ Persiste entre logins
```

### **Curvas Individuais**

```
✓ Arquivo: backend/database/simulacoes/{usuario_id}_simulacoes.json
✓ Apenas o usuário vê suas curvas
✓ Persiste entre logins
✓ Sincronizado automaticamente
```

---

## 🔄 Sincronização Automática

### **Ao salvar uma simulação**:
1. Curva é salva em `session_state`
2. Função `sincronizar_curva_com_arquivo()` é chamada
3. Curva também é salva em JSON:
   ```
   backend/database/simulacoes/{usuario_id}_simulacoes.json
   ```

### **Ao fazer login de novo**:
1. Sistema detecta que há arquivo de simulações para o usuário
2. Função `restaurar_curvas_de_arquivo()` carrega automaticamente
3. Curvas aparecem no simulador

---

## 🧪 Testando o Sistema

### **Teste 1: Verificar Autenticação**
```bash
cd /workspaces/1780_dirco
python test_database.py
```

Resultado esperado:
```
✓ PASSOU - Autenticação
✓ PASSOU - Usuários
✓ PASSOU - Curvas (Persistência)
✓ PASSOU - Usuários com Simulações

✅ TODOS OS TESTES PASSARAM!
```

### **Teste 2: Fluxo Completo Manual**

1. **Iniciar app**
   ```bash
   streamlit run frontend/app.py
   ```

2. **Login Admin** → Upload → Salvar Base

3. **Logout**

4. **Login Usuário Comum** → Simulador → Checar dados

5. **Criar simulação** → Salvar

6. **Logout e Login novamente** → Simulações aparecem

---

## ⚙️ Configuração Técnica

### **Variáveis de Session State**

```python
# Autenticação
st.session_state.autenticado        # bool
st.session_state.usuario_id         # str (usr_001, usr_002, etc)
st.session_state.usuario_email      # str
st.session_state.usuario_nome       # str
st.session_state.usuario_role       # str ("admin" ou "usuario")

# Dados
st.session_state.dados_upload       # DataFrame (base compartilhada)
st.session_state.curvas_ajustadas_persistentes  # {combo_key: {...}}
```

### **Arquivos Python**

| Arquivo | Função |
|---------|--------|
| `backend/database.py` | Gerencia persistência (CRUD de dados) |
| `frontend/data_manager.py` | Interface com database |
| `frontend/pages/autenticacao.py` | Login + Integração database |
| `frontend/pages/upload.py` | Upload com controle admin |
| `frontend/pages/simulador.py` | Carrega e aplica dados |

---

## 📝 Notas Importantes

1. **Senhas em JSON**: Apenas para mock. Em produção, usar hash + salt
2. **Session State**: Ainda usado para performance (cache local)
3. **Sincronização**: Arquivos são a "fonte da verdade" (persistência real)
4. **Banco Real**: Implementação pronta para migrar para PostgreSQL, MySQL, etc.

---

## 🚀 Próximas Melhorias

- [ ] Interface de admin para gerenciar usuários
- [ ] Histórico de versões de uploads
- [ ] Dashboard com métricas de uso
- [ ] Exportação de relatórios por usuário
- [ ] Autenticação via LDAP/AD

---

## 📞 Suporte

**Dúvidas sobre a implementação?**

Consulte:
- [`IMPLEMENTACAO_DATABASE.md`](./IMPLEMENTACAO_DATABASE.md) - Detalhes técnicos
- [`backend/database.py`](./backend/database.py) - Funções disponíveis
- [`test_database.py`](./test_database.py) - Exemplos de uso

---

**Última atualização**: Março 2026
**Status**: ✅ Pronto para Produção (com Mock Database)
