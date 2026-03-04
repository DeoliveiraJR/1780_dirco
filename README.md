# 🏦 UAN Dashboard - Sistema de Projeções Financeiras

Sistema completo de análise e simulação de projeções financeiras desenvolvido para a equipe DIRCO, com **persistência de dados**, **isolamento multi-usuário** e **controle de permissões**.

---

## 📋 Sobre o Projeto

O **UAN Dashboard** é uma aplicação web desenvolvida em **Streamlit** que centraliza a gestão de projeções financeiras com funcionalidades avançadas:

- ✅ **Upload e validação** de arquivos Excel
- ✅ **Dashboard analítico** com KPIs e visualizações interativas
- ✅ **Simulador de projeções** com ajustes manuais em tempo real
- ✅ **Persistência durável** de simulações por usuário
- ✅ **Isolamento de dados** entre usuários
- ✅ **Autenticação** com controle de permissões (Admin + Usuário)
- ✅ **Base compartilhada** para todos os usuários
- ✅ **Sincronização automática** entre login/logout

---

## 🚀 Principais Funcionalidades

### 📤 **Upload de Dados (Admin Only)**
- Importação de arquivos Excel (.xlsx) com projeções financeiras
- Validação automática de colunas obrigatórias
- Normalização de dados (datas, meses, categorias)
- Apenas administradores podem fazer upload
- Base salva e compartilhada com todos os usuários

### 📊 **Dashboard de Análises**
- Visualização de KPIs principais (valor total, realizado, acurácia)
- Gráficos interativos de evolução mensal
- Filtros por cliente, categoria e produto
- Comparativo entre períodos

### 🎯 **Simulador de Projeções**
- Curvas de projeção: **Analítica**, **Mercado** e **Ajustada**
- Edição interativa de valores mensais (drag-and-drop)
- Período contínuo de 12 meses (cruza anos quando necessário)
- Cálculo automático de variações mensais
- **Cada usuário tem suas curvas isoladas e persistidas**

### 👤 **Autenticação e Controle de Acesso**
- Sistema de login seguro
- Dois tipos de usuários: **Admin** e **Usuário Comum**
- Perfil com simulações salvas automaticamente

### 🔒 **Isolamento Multi-Usuário**
- Cada usuário tem sua própria cópia da base ao editar
- Dados isolados completamente entre usuários
- Sincronização automática ao login/logout

---

## 🛠️ Stack Tecnológica

- **Frontend**: Streamlit, Bokeh, Plotly, Pandas, NumPy, openpyxl
- **Backend**: Python com persistência em arquivos (mock database)
- **Infraestrutura**: Docker, Python 3.11+

---

## 📦 Instalação e Execução

### Pré-requisitos
- Python 3.11+
- pip

### Instalação Local

```bash
# 1. Clonar repositório
git clone https://github.com/DeoliveiraJR/1780_dirco.git
cd 1780_dirco

# 2. Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar aplicação
streamlit run frontend/app.py --server.port=8503
```

A aplicação estará disponível em: **http://localhost:8503**

### Execução com Docker

```bash
docker build -t uan-dashboard .
docker run -p 8503:8503 uan-dashboard
```

---

## 🔐 Credenciais de Teste

### Admin (Pode fazer upload e criar simulações)
```
Email: admin@uan.com.br
Senha: admin123
```

### Usuário Comum (Pode criar simulações, não pode fazer upload)
```
Email: teste@uan.com.br
Senha: 123456
```

---

## 📂 Estrutura do Projeto

```
/workspaces/1780_dirco/
├── README.md                          # 📖 Documentação completa
├── PROGRESSO_PROJETO.md               # 📋 Histórico de implementações
├── frontend/                          # 🎨 Interface Streamlit
│   ├── app.py                         # Aplicação principal
│   ├── pages/                         # Páginas
│   ├── components/                    # Componentes visuais
│   ├── services/                      # Agregações de dados
│   └── utils_ext/                     # Utilitários
├── backend/                           # ⚙️ Backend e Persistência
│   ├── database.py                    # 🗄️ Mock Database
│   ├── database/
│   │   ├── users.json                 # Usuários cadastrados
│   │   ├── uploads/                   # Base compartilhada
│   │   ├── simulacoes/                # Simulações por usuário
│   │   └── metadata/                  # Auditoria
│   └── app/                           # Backend Flask (opcional)
├── requirements.txt                   # Dependências
├── test_isolamento.py                 # Testes de isolamento
└── test_database.py                   # Testes automatizados
```

---

## 🔄 Sistema de Persistência de Dados

### Arquitetura Implementada

O sistema utiliza um **mock database em arquivos** (pronto para migração a BD real):

**Base Compartilhada** (Todos veem)
```
backend/database/uploads/base_dados_compartilhada.xlsx
```

**Bases Personalizadas por Usuário** (Isolamento)
```
backend/database/uploads/base_usuario_{usuario_id}.xlsx
```

**Simulações Individuais** (Persiste entre logins)
```
backend/database/simulacoes/{usuario_id}_simulacoes.json
```

### Fluxo de Isolamento

```
1. Usuário faz login → carrega base_dados_compartilhada.xlsx
2. Usuário edita curva e salva → sistema cria base_usuario_XXX.xlsx
3. Próximos logins → carregam sua cópia pessoal
4. ✅ Resultado: ISOLAMENTO COMPLETO
```

---

## 🔐 Controle de Acesso

| Feature | Admin | Usuário Comum |
|---------|-------|---------------|
| Login | ✅ | ✅ |
| Fazer Upload | ✅ | ❌ |
| Acessar Simulador | ✅ | ✅ |
| Ver Próprias Simulações | ✅ | ✅ |
| Ver Simulações de Outros | ❌ | ❌ |

---

## 🧪 Testes Automatizados

```bash
# Teste de isolamento
python test_isolamento.py
# Resultado: ✅ ISOLAMENTO DE DADOS FUNCIONANDO ✅

# Teste completo
python test_database.py
# Resultado: ✅ TODOS OS TESTES PASSARAM!
```

---

## 📊 Estrutura de Dados (Excel)

| Coluna | Descrição | Exemplo |
|--------|-----------|---------|
| `DATA_COMPLETA` | Data de referência | 01/01/2026 |
| `MES` | Mês (nome ou número) | janeiro / 1 |
| `ANO` | Ano de referência | 2026 |
| `CATEGORIA` | Categoria do produto | Eletrônicos |
| `PRODUTO` | Nome do produto | Notebook X1 |
| `CURVA_REALIZADO` | Valores realizados | 1500 |
| `PROJETADO_ANALITICO` | Projeção analítica | 1600 |
| `PROJETADO_MERCADO` | Projeção de mercado | 1550 |
| `PROJETADO_AJUSTADO` | Projeção ajustada | 1700 |

---

## 🔮 Roadmap Futuro

- [ ] Integração com banco de dados PostgreSQL
- [ ] Sistema de notificações
- [ ] Exportação de relatórios em PDF/CSV
- [ ] API de integração com ERPs
- [ ] Dashboards personalizáveis
- [ ] Versionamento de simulações
- [ ] Backup automático de bases personalizadas

---

## 📚 Documentação Adicional

- **[PROGRESSO_PROJETO.md](./PROGRESSO_PROJETO.md)** - Histórico completo de implementações
- **[QUICKSTART.md](./QUICKSTART.md)** - Guia rápido para começar

---

> **Versão:** 1.2.0  
> **Status:** ✅ Produção Pronto  
> **Última atualização:** Março 2026
