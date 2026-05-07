# 🏦 UAN Dashboard - Sistema de Projeções Financeiras

Sistema completo de análise e simulação de projeções financeiras desenvolvido para a equipe DIRCO, com **persistência de dados**, **isolamento multi-usuário**, **controle de permissões** e **DRE Gerencial profissional**.

**Versão Atual:** v2.4.2 | **Status:** ✅ Production Ready | **Última Atualização:** 07/05/2026

---

## 📌 O que foi implementado

### ✅ [v2.4.2] - Correções de Save + Filtro Produto TODOS
- **🐛 NameError Corrigido:** removida dependência de variável órfã (`salvar_clicked`) no simulador.
- **💾 Save Unificado:** botão de salvar na sidebar agora dispara o fluxo oficial do simulador (captura da curva ajustada atual e persistência correta).
- **🔄 Sincronização de Estado:** nome da simulação e feedback de save passaram a ser sincronizados em `session_state` de forma consistente.
- **📦 Produto "TODOS" funcional:** serviços de agregação agora tratam produto vazio/TODOS como agregação de todos os produtos da categoria.
- **🧩 UX estável:** evita erros em cascata no ciclo sidebar → simulador → histórico.

### ✅ [v2.4.1] - Hotfix de Inicialização de Session State
- Inicialização defensiva de `st.session_state["filtros"]` e `st.session_state["sim_nome"]`.
- Correção de acesso seguro para evitar `KeyError` na montagem dos filtros da sidebar.

### ✅ [v2.4.0] - Releitura de UX no Simulador
- Filtros principais migrados para sidebar em expander dedicado.
- Inclusão do campo de histórico em layout compacto (paginação) para evitar crescimento vertical excessivo.
- Inclusão da opção "TODOS" no filtro de produto.

### ✅ [v2.2.9] - Cards de Categoria e Filtro de Ano nas Barras
- **🧩 Cards Enriquecidos:** Incluídas duas colunas de referência com realizado de 2025 (Total e Média) dentro dos cards de categoria
- **📐 Relevância para Projeções:** Nas linhas de projeção, as colunas de referência agora exibem variação percentual vs base de realizado 2025 (em vez de comparação com histórico de projeção inexistente)
- **📅 Filtro de Ano (Barras):** Adicionado seletor de ano dedicado para os gráficos de barras por categoria
- **🏷️ Contexto Visual:** Título dos gráficos de barras passou a exibir o ano selecionado
- **🔒 Sem quebra de fluxo:** Cards, barras e pizzas seguem preservando estrutura e sincronismo do simulador

### ✅ [v2.2.8] - Rotação de Curva (Bug Fix)
- **🔧 Correção Crítica:** Funcionalidade de "Rotacionar Curva" na barra lateral estava quebrada
- **🔀 Sincronização de Estado:** Chave `sim_rotacionar_mult` unificada com `sim_rotacionar_curva`
- **💾 Persistência Corrigida:** Rotação agora é salva corretamente ao clicar "Aplicar"
- **✅ Impacto:** Ajustes de inclinação agora funcionam end-to-end (sidebar → simulador → persistência)
- **✨ Destaque Visual:** Colunas de `AJUSTE (+/-)` com estilo diferenciado para facilitar leitura
- **🔒 Edição Validada:** Apenas colunas de ajuste aceitam edição válida; alterações em outras colunas são revertidas automaticamente
- **🔄 Sincronização Completa:** Ajustes digitados na tabela agora alimentam corretamente o estado de 24 meses e refletem no incremento da seção "Ajuste Manual por Mês"

### ✅ [v2.2.6] - Hotfix de Documento Bokeh no Simulador
- **🩹 Correção Estrutural:** Gráfico principal e tabela histórica passaram a ser renderizados no mesmo documento Bokeh
- **🔗 Compatibilidade de Modelos:** Eliminado conflito de `ColumnDataSource already in a doc` ao sincronizar edição da tabela com os gráficos

### ✅ [v2.2.5] - Hotfix Bokeh na Tabela do Simulador
- **🩹 Correção de Renderização:** Removido uso inválido de `editor=None` em `TableColumn`, que causava erro de validação no Bokeh
- **✅ Estabilidade:** Mantida a edição de Ajuste sem quebrar a renderização da tabela histórica

### ✅ [v2.2.4] - Simulador (Ajuste Editável na Tabela)
- **✏️ Ajuste Editável:** Colunas de Ajuste (+/-) em 2026 e 2027 agora aceitam input manual na tabela histórica
- **🔄 Sincronização Integrada:** Alterar Ajuste na tabela atualiza automaticamente Ajustada, variações e curva do gráfico principal
- **🧭 Ordem de Colunas:** RLZD 2027 reposicionado junto ao bloco de projeções 2027
- **🎨 Diferenciação Visual:** Blocos de 2026 e 2027 com identidade visual mais clara para leitura por ano

### ✅ [v2.2.3] - Tabela do Simulador (Layout Anual)
- **📅 Meses Fixos:** Tabela da Série Histórica padronizada em JAN-DEZ
- **🧩 Estrutura por Ano:** Colunas separadas para 2025 (RLZD/VAR), 2026 (RLZD + projeções) e 2027 (RLZD + projeções)
- **🔁 Regra de Realizado:** Quando existir realizado em 2026/2027, as projeções do mês passam a assumir o valor realizado
- **🎨 Visual de Variação:** Removido estilo circular nas colunas de variação %, mantendo destaque apenas por cor do valor

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

**Última atualização:** 07/05/2026 | **Versão:** v2.4.2 | **Status:** ✅ Production Ready

Mantém este README como documentação única e oficial. Para histórico detalhado, consulte [CHANGELOG.md](CHANGELOG.md).
