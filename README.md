# 🏦 UAN Dashboard - Sistema de Projeções Financeiras

Sistema completo de análise e simulação de projeções financeiras desenvolvido para a equipe DIRCO, com **persistência de dados**, **isolamento multi-usuário**, **controle de permissões** e **DRE Gerencial profissional**.

**Versão Atual:** v2.2.1 | **Status:** ✅ Production Ready | **Última Atualização:** 23/04/2026

---

## 📌 O que foi implementado

### ✅ [v2.2.1] - Sazonalidade Dinâmica (CORRIGIDO)
- **🔧 Fix Crítico:** Janeiro agora calcula CORRETAMENTE os últimos 7 meses (com wrap-around)
- **✨ Type Safety:** Suporta múltiplos formatos (int legacy, list, dict novo)
- **✨ UI Melhorada:** Parâmetros de sazonalidade em expanders colapsáveis
- **✅ Backward Compatible:** Dados legados funcionam automaticamente
- **Testes:** 100% validados

### ✅ [v2.2.0] - Sistema de Sazonalidade
- Período FIXO (mesmo para todos os meses)
- Período VARIÁVEL (adapta cada mês - últimos N meses)
- Compatibilidade com fórmulas dinâmicas

### ✅ [v2.1.0] - DRE Gerencial Completa
- 21 variáveis financeiras pré-configuradas
- 3 abas: Editor, Metodologias, Análise
- Sistema de fórmulas personalizadas
- Gráficos interativos e exportação

---

## 🚀 Funcionalidades Principais

### 📤 **Upload de Dados** (Admin)
- Importação de arquivos Excel com projeções
- Validação automática de colunas
- Compartilhamento automático com todos os usuários

### 📊 **Dashboard Analítico**
- KPIs principais e evolução mensal
- Filtros dinâmicos por cliente/categoria/produto
- Gráficos interativos

### 🎯 **Simulador de Projeções**
- 3 curvas: Analítica, Mercado, Ajustada
- Edição interativa com período contínuo de 12 meses
- Cálculo automático de variações
- Dados isolados e persistidos por usuário

### 📈 **DRE Gerencial**

#### **Editor DRE**
- 21 variáveis financeiras (TD71, TD72, MFB, MFBE, etc.)
- Entrada manual mês-a-mês (Jan-Dez)
- Carregamento automático de TD71 do Simulador
- Cálculos automáticos de totalizadores
- Persistência por usuário

#### **Sistema de Metodologias**
- Crie fórmulas personalizadas: `=0.05*TD71`, `=TD71+TD72`
- Valide antes de salvar
- Aplique a múltiplas variáveis
- Edite/delete metodologias salvas

#### **Análise e Relatórios**
- Métricas consolidadas (Receita, Despesa, Margens)
- Gráficos: Receita vs Despesa, Margens, Composição
- Tabela detalhada com totalizadores destacados
- Exportação JSON/CSV

### 🔐 **Autenticação e Acesso**
- Login seguro com 2 perfis: Admin e Usuário
- Isolamento completo de dados entre usuários
- Base compartilhada para todos

---

## 🛠️ Stack Tecnológica

- **Frontend:** Streamlit, Bokeh, Plotly, Pandas
- **Backend:** Python 3.12+ com persistência em JSON
- **Containers:** Docker
- **UI:** HTML/CSS customizado

---

## 📦 Instalação

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
.venv\Scripts\activate      # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar
streamlit run frontend/app.py --server.port=8503
```

Acesso: **http://localhost:8503**

### Com Docker
```bash
docker build -t uan-dashboard .
docker run -p 8503:8503 uan-dashboard
```

---

## 🔐 Credenciais de Teste

| Tipo | Email | Senha |
|------|-------|-------|
| Admin | `admin@uan.com.br` | `admin123` |
| Usuário | `usuario@uan.com.br` | `user123` |

---

## 📁 Estrutura do Projeto

```
1780_dirco/
├── frontend/
│   ├── app.py                          # App principal Streamlit
│   ├── pages/
│   │   ├── autenticacao.py            # Login/logout
│   │   ├── dashboard.py               # KPIs e análises
│   │   ├── simulador.py               # Editor de curvas
│   │   ├── dre.py                     # DRE Gerencial (v2.1+)
│   │   ├── upload.py                  # Upload Admin
│   │   └── perfil.py                  # Perfil do usuário
│   ├── utils_ext/
│   │   ├── calc_functions.py          # Funções nativas (SOMA, MEDIA, etc.)
│   │   ├── constants.py               # Constantes e cores
│   │   ├── callbacks.py               # Event handlers
│   │   └── formatters.py              # Formatação de dados
│   ├── components/
│   │   ├── cards.py                   # KPI cards
│   │   ├── lines.py, bars.py, donut.py # Gráficos
│   │   └── bokeh_editable/            # Editor interativo
│   └── services/
│       └── aggregations.py            # Agregações de dados
│
├── backend/
│   ├── app/
│   │   ├── models/                    # Estruturas de dados
│   │   ├── routes/                    # Endpoints
│   │   └── services/                  # Lógica de negócio
│   ├── database.py                    # Gerenciador de BD (JSON)
│   ├── database_schema.py             # Schema de dados
│   ├── database/
│   │   ├── users.json                 # Usuários
│   │   ├── dados/                     # DREs por usuário
│   │   ├── simulacoes/                # Simulações por usuário
│   │   └── uploads/                   # Arquivos enviados
│   └── run.py                         # Server backend
│
├── README.md                           # Este arquivo (documentação oficial)
├── CHANGELOG.md                        # Histórico de alterações e versões
├── requirements.txt                    # Dependências Python
└── Dockerfile                          # Container config
```

---

## 🧪 Como Testar

### Teste de Sazonalidade (v2.2.1)

1. **Criar Metodologia com Sazonalidade:**
   - Página: `DRE → Metodologias → + Nova`
   - Nome: "Média 7M"
   - Fórmula: `MEDIA(TD071; -7)`
   - Parâmetros: 
     - Tipo: VARIÁVEL
     - Quantidade: 7
     - Período: MES
     - Posição: ULTIMO
   - Aplicar a: TD071
   - Clique: "Criar"

2. **Verificar Resultado:**
   - ✅ Janeiro deve retornar valor DIFERENTE de Julho
   - ✅ Cada mês deve ter valor único (não estático)
   - ✅ Janeiro deve incluir últimos 7 períodos (Jul-Jan com wrap-around)

### Teste Completo de Fluxo

1. **Upload (Admin):** 
   - `Menu → Upload → Escolher Arquivo.xlsx → Salvar`
2. **Simulador:** 
   - `Menu → Simulador → Ajustar curva → Salvar`
3. **DRE:** 
   - `Menu → DRE → Editor → Verificar TD71 preenchido`

---

## 📝 Documentação

### Arquivos Oficiais
- **README.md** - Este arquivo (documentação principal e única)
- **CHANGELOG.md** - Histórico completo de alterações, bugs e features

### Como Usar a Documentação

Para entender mudanças de versão:
1. Abra [CHANGELOG.md](CHANGELOG.md)
2. Encontre a versão desejada (v2.2.1, v2.2.0, etc.)
3. Leia o resumo de mudanças e bugs corrigidos

Para questões técnicas:
1. Consulte a estrutura em "📁 Estrutura do Projeto"
2. Verifique os passos em "🧪 Como Testar"
3. Se necessário, explore o [CHANGELOG.md](CHANGELOG.md) para contexto

---

## 🚀 Próximas Tarefas (Roadmap)

- [ ] Testes de carga (100k+ registros)
- [ ] Suporte multi-ano (períodos > 12 meses)
- [ ] Dashboard comparativo entre períodos
- [ ] API REST para sazonalidade

---

## 🤝 Contribuindo

1. Crie uma branch: `git checkout -b feature/sua-feature`
2. Commit: `git commit -am 'FEAT: Descrição'`
3. Push: `git push origin feature/sua-feature`
4. Abra um PR com detalhes das mudanças

**Convenções de Commit:**
- `✅ FEAT:` Nova feature
- `🐛 FIX:` Correção de bug
- `📝 DOCS:` Documentação
- `♻️ REFACTOR:` Refatoração
- `⚡ PERF:` Performance

---

## 📄 Licença

Desenvolvido para DIRCO - UAN. Todos os direitos reservados.

---

## 📞 Suporte

Para questões ou problemas:

1. **Histórico de Alterações:** Consulte [CHANGELOG.md](CHANGELOG.md)
2. **Estrutura do Projeto:** Veja "📁 Estrutura do Projeto"
3. **Como Testar:** Siga passos em "🧪 Como Testar"
4. **Erro ao Executar:** Verifique [CHANGELOG.md](CHANGELOG.md) para bugs conhecidos

---

**Última atualização:** 23/04/2026 | **Versão:** v2.2.1 | **Status:** ✅ Production Ready

Mantém este README como documentação única e oficial. Para histórico detalhado, consulte [CHANGELOG.md](CHANGELOG.md).
