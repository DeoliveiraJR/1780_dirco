# 🏦 UAN Dashboard - Sistema de Projeções Financeiras

Sistema completo de análise e simulação de projeções financeiras desenvolvido para a equipe DIRCO, com **persistência de dados**, **isolamento multi-usuário**, **controle de permissões** e **DRE Gerencial profissional**.

---

## 🔄 Últimas Alterações (Março 2026)

### ✅ Implementado - Fase 2 (DRE Gerencial):
- **📈 Nova Página: DRE Gerencial** - Sistema completo de projeções financeiras
  - 21 variáveis pré-configuradas (TD71, TD72, MFB, MFBE, TD90, TD70, TD87, TD88, TD95, TD96, TD97, TD11, TD12, TD76, TD16, TD92, TD81 e mais)
  - Interface profissional com tabelas mês-a-mês (Jan-Dez)
  - Integração automática com simulador (carrega TD71 da curva ajustada)
  - 3 abas: Editor, Metodologias e Análise

- **🔧 Sistema de Metodologias** - Cálculos automáticos via fórmulas
  - Criar/editar/deletar metodologias personalizadas
  - Sintaxe simples: `=0.05*TD71` (5% de receita), `=TD71+TD72` (soma)
  - Aplicação a múltiplas variáveis simultaneamente
  - Validação de fórmulas antes de salvar

- **📊 Análise e Relatórios** - Visualizações avançadas
  - Gráficos: Receita vs Despesa, Margens (MFB/MFBE), Composição
  - Métricas consolidadas (totais anuais, médias mensais, margens %)
  - Tabela detalhada de 21 linhas com valores formatados
  - Exportação: JSON, CSV com dados estruturados

- **🎨 Design Profissional** - Layout melhorado
  - Tabelas HTML customizadas com CSS moderno
  - Cores institucionais (#0c3a66, #06b6d4, #f9a8d4)
  - Hover effects e visual hierarchy
  - Responsividade para diferentes tamanhos de tela

- **🔐 Filtros Avançados** - Cascata Cliente/Categoria/Produto
  - Sincronismo com Simulador
  - Carregamento dinâmico de opções
  - Persistência de filtros na sessão

### ✅ Implementado - Fase 1:
- **Tabela Expandida** - Height de 1800px → 2100px para visibilidade completa
- **Gráfico Dinâmico** - Período contínuo de próximos 12 meses
- **Validações Gracioso** - Mensagens user-friendly para dados incompletos

**Detalhes completos:** Veja [ULTIMAS_ALTERACOES.md](ULTIMAS_ALTERACOES.md)

---

## 📋 Sobre o Projeto

O **UAN Dashboard** é uma aplicação web desenvolvida em **Streamlit** que centraliza a gestão de projeções financeiras com funcionalidades avançadas:

- ✅ **Upload e validação** de arquivos Excel
- ✅ **Dashboard analítico** com KPIs e visualizações interativas
- ✅ **Simulador de projeções** com ajustes manuais em tempo real
- ✅ **DRE Gerencial** com 21 variáveis e sistema de metodologias
- ✅ **Persistência durável** de simulações e DRE por usuário
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

### 🎯 **Simulador de Projeções (TD21)**
- Curvas de projeção: **Analítica**, **Mercado** e **Ajustada**
- Edição interativa de valores mensais (drag-and-drop)
- Período contínuo de 12 meses (cruza anos quando necessário)
- Cálculo automático de variações mensais
- **Cada usuário tem suas curvas isoladas e persistidas**
- Botão de cópia automática de curva analítica para ajustada

### 📈 **DRE Gerencial - NOVO!**
Uma página dedicada para projeções financeiras profissionais com:

#### **Editor de DRE**
- 21 variáveis financeiras organizadas hierarquicamente
- Entrada manual de valores mês-a-mês
- Cálculos automáticos de totalizadores (MFB, MFBE)
- Carregamento automático de TD71 a partir do Simulador
- Persistência de dados por usuário
- Interface limpa e responsiva

#### **Metodologias**
- Criar fórmulas personalizadas de cálculo automático
- Exemplos: `=0.05*TD71` (Receita 5%), `=TD71+TD72` (Spread)
- Aplicar a múltiplas variáveis em um clique
- Validação antes de salvar
- Editar/deletar metodologias salvas
- Histórico com data de criação

#### **Análise e Relatórios**
- Métricas consolidadas (Receita, Despesa, Margens, Período)
- Gráficos interativos:
  - Receita x Despesa (mês a mês)
  - Evolução de Margens (MFB e MFBE)
  - Composição de Receita
- Tabela detalhada formatada com totalizadores destacados
- Exportação em JSON e CSV

### 👤 **Autenticação e Controle de Acesso**
- Sistema de login seguro
- Dois tipos de usuários: **Admin** e **Usuário Comum**
- Perfil com simulações e dados DRE salvos automaticamente

### 🔒 **Isolamento Multi-Usuário**
- Cada usuário tem sua própria cópia da base ao editar
- Dados isolados completamente entre usuários
- Sincronização automática ao login/logout
- DRE separada por usuário com persistência

---

## 🛠️ Stack Tecnológica

- **Frontend**: Streamlit, Bokeh, Plotly, Pandas, NumPy, openpyxl
- **Backend**: Python com persistência em arquivos (mock database)
- **Linguagens**: Python 3.12+
- **Infraestrutura**: Docker, Python 3.12+

---

## 📦 Instalação e Execução

### Pré-requisitos
- Python 3.12+
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

### Admin (Pode fazer upload e criar simulações/DRE)
```
Email: admin@uan.com.br
Senha: admin123
```

### Usuário Comum (Pode criar simulações e DRE, não pode fazer upload)
```
Email: teste@uan.com.br
Senha: 123456
```

---

## 📂 Estrutura do Projeto

```
/workspaces/1780_dirco/
├── README.md                          # 📖 Documentação completa
├── ULTIMAS_ALTERACOES.md              # 📋 Histórico de implementações
├── requirements.txt                   # Dependências Python
│
├── frontend/                          # 🎨 Interface Streamlit
│   ├── app.py                         # Aplicação principal e router
│   ├── data_manager.py                # Gerencimento de dados compartilhados
│   ├── styles.py                      # Estilos CSS globais
│   ├── utils.py                       # Funções utilitárias gerais
│   │
│   ├── pages/                         # 📄 Páginas da aplicação
│   │   ├── __init__.py
│   │   ├── autenticacao.py            # Sistema de login/autenticação
│   │   ├── dashboard.py               # Dashboard de análises
│   │   ├── simulador.py               # Simulador TD21 (3 curvas)
│   │   ├── dre.py                     # 🆕 DRE Gerencial (21 variáveis)
│   │   ├── perfil.py                  # Perfil do usuário
│   │   └── upload.py                  # Upload de dados (Admin)
│   │
│   ├── components/                    # 🧩 Componentes visuais reutilizáveis
│   │   ├── __init__.py
│   │   ├── bars.py                    # Gráficos de barras
│   │   ├── cards.py                   # Cards de métricas
│   │   ├── donut.py                   # Gráficos de pizza/donut
│   │   ├── lines.py                   # Gráficos de linhas
│   │   └── bokeh_editable/            # Componentes editáveis Bokeh
│   │
│   ├── services/                      # ⚙️ Serviços de agregação de dados
│   │   ├── __init__.py
│   │   ├── aggregations.py            # Funções de agregação por categoria/produto
│   │   └── data_service.py            # Acesso a dados do backend
│   │
│   ├── utils_ext/                     # 🔧 Utilitários especializados
│   │   ├── __init__.py
│   │   ├── callbacks.py               # Callbacks de eventos Streamlit
│   │   ├── constants.py               # Constantes (MESES_ABR_LIST, CORES, etc)
│   │   ├── css.py                     # Injeção de CSS customizado
│   │   ├── display.py                 # Funções de exibição formatada
│   │   ├── formatters.py              # Formatação de números (fmt_br)
│   │   └── series.py                  # Operações com séries de dados
│   │
│   ├── themes/                        # 🎨 Temas CSS
│   │   └── uan_light.css              # Tema light com cores UAN
│   │
│   └── images/                        # 📸 Assets visuais
│
├── backend/                           # ⚙️ Backend e Persistência
│   ├── run.py                         # Script para rodar backend Flask (opcional)
│   ├── database.py                    # 🗄️ Mock Database com isolamento
│   │
│   ├── app/                           # Flask app (opcional)
│   │   ├── __init__.py
│   │   ├── models/                    # Modelos ORM
│   │   ├── routes/                    # Rotas API
│   │   └── services/                  # Serviços de negócio
│   │
│   └── database/                      # 💾 Armazenamento persistente
│       ├── users.json                 # Usuários cadastrados
│       ├── metadata/                  # Auditoria e metadados
│       ├── uploads/                   # Base compartilhada e personalizadas
│       │   ├── base_dados_compartilhada.xlsx
│       │   └── base_usuario_{id}.xlsx
│       └── simulacoes/                # Simulações e DRE por usuário
│           ├── usr_001_simulacoes.json   # TD21
│           └── usr_001_dre.json          # 🆕 DRE Gerencial
│
├── data/                              # 📊 Dados brutos (dev)
│   └── raw/
│       ├── generate_mock_data.py      # Gerador de dados de teste
│       └── scores_mape.csv            # MAPE de acurácia
│
└── tests/                             # 🧪 Testes automatizados
    ├── test_isolamento.py             # Teste de isolamento de dados
    └── test_dre.py                    # 🆕 Testes para DRE Gerencial
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

**Simulações Individuais** (TD21 - Persiste entre logins)
```
backend/database/simulacoes/{usuario_id}_simulacoes.json
```

**DRE Gerencial Individual** (🆕 Persiste entre logins)
```
backend/database/simulacoes/{usuario_id}_dre.json
```

### Fluxo de Isolamento

```
1. Usuário faz login → carrega base_dados_compartilhada.xlsx
2. Usuário edita curva e salva → sistema cria base_usuario_XXX.xlsx
3. Usuário cria/edita DRE → salvo em {usuario_id}_dre.json
4. Próximos logins → carregam sua cópia pessoal (simulações + DRE)
5. ✅ Resultado: ISOLAMENTO COMPLETO
```

---

## 🔐 Controle de Acesso

| Feature | Admin | Usuário Comum |
|---------|-------|---------------|
| Login | ✅ | ✅ |
| Fazer Upload | ✅ | ❌ |
| Acessar Dashboard | ✅ | ✅ |
| Acessar Simulador | ✅ | ✅ |
| Acessar DRE Gerencial | ✅ | ✅ |
| Ver Próprias Simulações | ✅ | ✅ |
| Ver Própria DRE | ✅ | ✅ |
| Ver Dados de Outros | ❌ | ❌ |

---

## 📊 Estrutura de Dados

### Excel (Upload)

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

### DRE (Estrutura Interna)

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `codigo` | str | Identificador único | TD71 |
| `descricao` | str | Nome da variável | Receita Financeira |
| `tipo` | str | variavel \| totalizador | variavel |
| `valores` | list[float] | 12 meses | [1000, 1050, 1100, ...] |
| `formula` | str \| null | Para cálculos | =0.05*TD71 |
| `eh_negrito` | bool | Destaque visual | true |
| `metodologia` | str \| null | Metodologia aplicada | Receita 5% |

---

## 🧪 Testes Automatizados

```bash
# Teste de isolamento
python test_isolamento.py
# Resultado: ✅ ISOLAMENTO DE DADOS FUNCIONANDO ✅

# Teste completo
python test_database.py
# Resultado: ✅ TODOS OS TESTES PASSARAM!

# Teste DRE (futuro)
python tests/test_dre.py
# Resultado: ✅ DRE Funcionalidades OK!
```

---

## 📚 Guias de Uso

### Dashboard
1. Fazer login com credenciais
2. Selecionar cliente, categoria e produto nos filtros
3. Visualizar KPIs e gráficos automáticos

### Simulador (TD21)
1. Ir para "🎯 Simulador" no menu
2. Selecionar cliente, categoria, produto
3. Editar 3 curvas: Analítica, Mercado, Ajustada
4. Sistema mostra automaticamente próximos 12 meses
5. Salvar alterações (persistem por usuário)

### DRE Gerencial
1. Ir para "📈 DRE" no menu
2. Selecionar cliente, categoria, produto
3. **Abas disponíveis:**
   - **Editor**: Preencher 21 variáveis mês-a-mês
   - **Metodologias**: Criar fórmulas de cálculo automático
   - **Análise**: Visualizar gráficos, métricas e exportar dados

#### Exemplo de Metodologia
```
Nome: "Receita 5% da Financeira"
Fórmula: =0.05*TD71
Aplicável a: TD90
Resultado: TD90 = 5% * valores de TD71
```

---

## 🔮 Roadmap Futuro

- [ ] Integração com banco de dados PostgreSQL
- [ ] Sistema de versionamento de DRE (histórico)
- [ ] Exportação de DRE em PDF profissional
- [ ] Comparativo entre cenários DRE
- [ ] API de integração com ERPs
- [ ] Dashboards personalizáveis
- [ ] Versionamento e rollback de simulações
- [ ] Backup automático de bases personalizadas
- [ ] Alertas para anomalias nas projeções

---

## 📚 Documentação Adicional

- **[ULTIMAS_ALTERACOES.md](./ULTIMAS_ALTERACOES.md)** - Histórico completo de implementações
- **Docs DRE:** Veja comentários em [frontend/pages/dre.py](./frontend/pages/dre.py)

---

## 🤝 Contribuindo

Para adicionar novas funcionalidades:

1. Create uma branch: `git checkout -b feature/nova-funcionalidade`
2. Make changes and test locally
3. Commit: `git commit -am 'Add nova-funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

---

## 📞 Suporte e Dúvidas

Para dúvidas sobre a aplicação:
- Consulte os comentários no código (bem documentado)
- Veja exemplos em [ULTIMAS_ALTERACOES.md](./ULTIMAS_ALTERACOES.md)
- Abra uma issue no repositório

---

> **Versão:** 2.0.0  
> **Status:** ✅ Produção Pronto  
> **Última atualização:** 12 de Março de 2026  
> **Mudança Principal:** Adição do módulo DRE Gerencial com sistema de metodologias
