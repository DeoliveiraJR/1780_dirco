# 🏦 UAN Dashboard - Sistema de Projeções Financeiras

Sistema de análise e simulação de projeções financeiras desenvolvido para equipe da DIRCO. A aplicação permite visualizar, validar e ajustar projeções de resultados financeiros de forma interativa.

---

## 📋 Sobre o Projeto

O **UAN Dashboard** é uma aplicação web desenvolvida em **Streamlit** que centraliza a gestão de projeções financeiras. O sistema foi projetado para atender analistas de controladoria, oferecendo:

- **Upload e validação** de dados financeiros via Excel
- **Dashboard analítico** com KPIs e visualizações interativas
- **Simulador de projeções** com ajustes manuais em tempo real
- **Persistência de simulações** individuais por usuário
- **Autenticação** para controle de acesso

### Arquitetura

O projeto segue uma arquitetura modular separando frontend e backend:

```
├── frontend/          # Aplicação Streamlit (UI/UX)
│   ├── pages/         # Páginas da aplicação
│   ├── components/    # Componentes visuais (gráficos)
│   ├── services/      # Lógica de agregações e cálculos
│   └── utils_ext/     # Utilitários e constantes
├── backend/           # API Flask (serviços de dados)
│   ├── routes/        # Endpoints da API
│   └── services/      # Serviços de processamento
└── data/              # Dados mockados para desenvolvimento
```

---

## 🚀 Principais Funcionalidades

### 📤 Upload de Dados
- Importação de arquivos Excel (.xlsx) com projeções financeiras
- Validação automática de colunas obrigatórias
- Normalização de dados (datas, meses, categorias)
- Suporte a múltiplos formatos de nomenclatura

### 📊 Dashboard de Análises
- Visualização de KPIs principais (valor total, realizado, acurácia)
- Gráficos interativos de evolução mensal
- Filtros por cliente, categoria e produto
- Comparativo entre períodos

### 🎯 Simulador de Projeções
- Curvas de projeção: **Analítica**, **Mercado** e **Ajustada**
- Edição interativa de valores mensais
- Comparativo visual entre anos realizados e projeções
- Cálculo automático de variações mensais
- Suporte a ajustes por categoria/produto

### 👤 Perfil e Autenticação
- Sistema de login para controle de acesso
- Perfil de usuário com simulações salvas
- Histórico de alterações

---

## 🛠️ Stack Tecnológica

### Frontend
| Tecnologia | Descrição |
|------------|-----------|
| **Streamlit** | Framework principal para aplicação web interativa |
| **Bokeh** | Gráficos interativos e editáveis (simulador) |
| **Plotly** | Visualizações do dashboard |
| **Pandas** | Manipulação e análise de dados |
| **NumPy** | Cálculos numéricos |
| **Pillow** | Processamento de imagens |

### Backend
| Tecnologia | Descrição |
|------------|-----------|
| **Flask** | API REST para serviços de dados |
| **Flask-CORS** | Suporte a requisições cross-origin |
| **OpenPyXL** | Leitura de arquivos Excel |

### Infraestrutura
| Tecnologia | Descrição |
|------------|-----------|
| **Docker** | Containerização da aplicação |
| **Python 3.11** | Runtime |

---

## 📦 Instalação e Execução

### Pré-requisitos
- Python 3.11+
- Docker (opcional)

### Instalação Local

```bash
# Clonar repositório
git clone https://github.com/DeoliveiraJR/1780_dirco.git
cd 1780_dirco

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
streamlit run frontend/app.py --server.port=8503
```

### Execução com Docker

```bash
# Construir imagem
docker build -t uan-dashboard .

# Executar container
docker run -p 8503:8503 uan-dashboard
```

A aplicação estará disponível em: `http://localhost:8503`

---

## 📂 Estrutura de Dados

O sistema espera arquivos Excel com as seguintes colunas:

| Coluna | Descrição |
|--------|-----------|
| `DATA_COMPLETA` | Data de referência |
| `MES` | Mês (nome ou número) |
| `ANO` | Ano de referência |
| `CATEGORIA` | Categoria do produto |
| `PRODUTO` | Nome do produto |
| `CURVA_REALIZADO` | Valores realizados |
| `PROJETADO_ANALITICO` | Projeção analítica |
| `PROJETADO_MERCADO` | Projeção de mercado |
| `PROJETADO_AJUSTADO` | Projeção ajustada |
| `TIPO_CLIENTE` | Tipo de cliente (opcional) |

---

## 🔮 Roadmap

- [ ] Integração com banco de dados PostgreSQL
- [ ] Persistência de simulações no backend
- [ ] Exportação de relatórios em PDF
- [ ] Sistema de notificações
- [ ] API de integração com ERPs
- [ ] Dashboards personalizáveis por usuário

---

## 👥 Equipe

Desenvolvido para a equipe de **DIRCO** - Sistema de análise e simulação de projeções financeiras.

---

## 📄 Licença

Este projeto é de uso interno e proprietário.

---

> **Versão:** 1.0.0-dev  
> **Última atualização:** Fevereiro 2026
