# 🚀 QUICK START - Teste Rápido em 5 Minutos

## 📋 Passos Rápidos para Validar a Implementação

### ⏱️ Tempo Total: ~5 minutos

---

## 1️⃣ Inicializar o Sistema (1 min)

### A. Rodar Testes de Database
```bash
cd /workspaces/1780_dirco
python test_database.py
```

**Resultado esperado**:
```
✓ PASSOU - Autenticação
✓ PASSOU - Usuários  
✓ PASSOU - Curvas (Persistência)
✓ PASSOU - Usuários com Simulações

✅ TODOS OS TESTES PASSARAM!
```

✅ Isso confirma que toda a persistência está funcionando!

---

## 2️⃣ Rodar a Aplicação Streamlit (1 min)

### B. Iniciare app.py
```bash
streamlit run frontend/app.py
```

Será aberta em: http://localhost:8501

---

## 3️⃣ Testar Fluxo Admin (2 min)

### C. Login Como Admin
- Email: `admin@uan.com.br`
- Senha: `admin123`

Você verá:
```
✓ Login realizado! Bem-vindo, Admin DIRCO (Administrador)
```

### D. Ir em Upload
- Clique em "📤 Upload da base de dados"
- Você verá interface de upload (não está bloqueada)

### E. Simular Arquivo (Opcional)
Se tiver um arquivo Excel, faça upload:
```
1. Selecione arquivo
2. Clique "✔️ Confirmar e Carregar Dados"
3. Veja o botão "💾 Salvar como Base Compartilhada"
4. Clique para salvar
```

Arquivo será salvo em: `backend/database/uploads/base_dados_compartilhada.xlsx`

---

## 4️⃣ Testar Fluxo Usuário Comum (1 min)

### F. Fazer Logout
- Clique no canto superior direito ou volte à página de login
- Logout automático

### G. Login Como Usuário Comum
- Email: `teste@uan.com.br`
- Senha: `123456`

Você verá:
```
✓ Login realizado! Bem-vindo, Analista Teste (Usuário)
```

### H. Ir em Upload
- Clique em "📤 Upload da base de dados"
- **Você verá**: 🔒 Acesso Restrito
- Pode visualizar dados na aba "Dados Carregados"
- **Não pode** fazer upload

✅ Controle de permissão funcionando!

---

## ✅ O Que Validar

### ✓ Autenticação
- [x] Admin login funciona
- [x] Usuário comum login funciona
- [x] Login errado é rejeitado
- [x] Roles são diferenciados

### ✓ Permissões
- [x] Admin vê upload normal
- [x] Usuário comum vê bloqueio
- [x] Upload está controlado

### ✓ Persistência
- [x] Database inicializa correto
- [x] Arquivos JSON são criados
- [x] Curvas são salvas

### ✓ Fluxo Visual
- [x] Mensagens são claras
- [x] Interface é intuitiva
- [x] Sem erros no console

---

## 📂 Estrutura Criada Após Testes

```
backend/database/
├── users.json                             (criado inicialmente)
├── uploads/
│   └── base_dados_compartilhada.xlsx      (criado se fazer upload)
├── simulacoes/
│   ├── usr_001_simulacoes.json            (se admin criar)
│   └── usr_002_simulacoes.json            (se usuário criar)
└── metadata/
    └── ultimo_upload.json                 (se fazer upload)
```

---

## 🎯 Checklist Final

- [ ] Executou `python test_database.py` → Passou
- [ ] Rodou `streamlit run frontend/app.py` → Abriu
- [ ] Login admin funcionou
- [ ] Login usuário funcionou
- [ ] Bloqueio de upload funciona
- [ ] Mensagens são claras
- [ ] Sem erros no console

Se todos ✓, **A IMPLEMENTAÇÃO ESTÁ FUNCIONAL!** 🎉

---

## 🆘 Se Algo Deu Errado

### Erro: "ModuleNotFoundError"
```bash
# Solução: Certifique-se que está na pasta certa
cd /workspaces/1780_dirco
```

### Erro: "Database não criado"
```bash
# Solução: Rode o test para inicializar
python test_database.py
```

### Erro: "Arquivo não encontrado"
```bash
# Solução: Verifique se backend/database/ foi criada
ls -la backend/database/
```

### Erro: Streamlit não inicia
```bash
# Solução: Instale dependências
pip install streamlit pandas numpy
```

---

## 📚 Leitura Complementar

Após validar, leia em ordem:

1. **RÁPIDO** (2 min):
   - [`GUIA_USO_PERSISTENCIA.md`](./GUIA_USO_PERSISTENCIA.md)

2. **DETALHADO** (10 min):
   - [`IMPLEMENTACAO_DATABASE.md`](./IMPLEMENTACAO_DATABASE.md)

3. **TÉCNICO** (15+ min):
   - [`backend/database.py`](./backend/database.py) - Código fonte

---

## 🎓 O Que Você Testou

```
┌─────────────────────────────────┐
│       Autenticação              │
│  admin + usuario comum          │
│  Roles diferenciadas            │
└────────┬────────────────────────┘
         │
┌────────▼────────────────────────┐
│     Controle de Acesso          │
│  Admin: upload liberado         │
│  Usuário: bloqueado             │
└────────┬────────────────────────┘
         │
┌────────▼────────────────────────┐
│    Persistência de Dados        │
│  Database.py funcionando        │
│  JSON sendo criado/salvo        │
│  Isolamento entre usuários      │
└─────────────────────────────────┘
```

---

## 🎉 Próximos Passos

Depois de validar, você pode:

1. **Adicionar mais usuários**
   - Edit: `backend/database/users.json`
   - Add novo usuário com id, email, role

2. **Testar com dados reais**
   - Coloque arquivo Excel
   - Faça upload como admin
   - Veja em outro usuário

3. **Explore o código**
   - Veja como database.py funciona
   - Entenda sincronização em data_manager.py
   - Modifique conforme necessário

4. **Configure para produção**
   - Mude senhas
   - Adicione mais usuários
   - Configure permissões específicas

---

**🏁 Pronto para começar!** 

Execute: 
```bash
cd /workspaces/1780_dirco
python test_database.py
streamlit run frontend/app.py
```

Qualquer dúvida, consulte os arquivos de documentação! 📚
