# Instruções de Setup do Projeto UAN Dashboard

## 1. Pré-requisitos

- Python 3.8+
- Git
- Pip (gerenciador de pacotes Python)

## 2. Setup Inicial

### 2.1 Clonar o Repositório

```bash
git clone <repository-url>
cd UAN
```

### 2.2 Criar Ambiente Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2.3 Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2.4 Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env conforme necessário (opcional para MVP)
```

## 3. Executar o Projeto

### 3.1 Gerar Dados Mockados (Primeira execução)

```bash
cd data/raw
python generate_mock_data.py
cd ../..
```

### 3.2 Iniciar Backend

```bash
# Terminal 1
python backend/run.py
```

Servidor disponível em: `http://localhost:5000`

### 3.3 Iniciar Frontend

```bash
# Terminal 2
streamlit run frontend/app.py
```

Interface disponível em: `http://localhost:8501`

## 4. Testando a Aplicação

### 4.1 Dashboard
1. Acesse `http://localhost:8501`
2. Navegue para "Dashboard"
3. Visualize gráficos e tabelas com dados mockados

### 4.2 Simulador
1. Acesse a aba "Simulador"
2. Crie uma nova simulação preenchendo os parâmetros
3. Visualize a prévia da simulação

### 4.3 Perfil
1. Acesse "Perfil"
2. Veja dados pessoais, segurança e histórico

## 5. Estrutura do Projeto

```
UAN/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── services/
│   │   ├── routes/
│   │   └── __init__.py
│   └── run.py
├── frontend/
│   ├── pages/
│   ├── app.py
│   └── utils.py
├── data/
│   └── raw/
│       └── generate_mock_data.py
├── requirements.txt
├── .env.example
└── README.md
```

## 6. Git Setup

```bash
# Inicializar repositório (se necessário)
git init

# Adicionar todos os arquivos
git add .

# Primeiro commit
git commit -m "Initial commit: MVP structure and setup"

# Adicionar remote (se necessário)
git remote add origin <repository-url>

# Push para main branch
git push -u origin main
```

## 7. Dicas de Desenvolvimento

### Estrutura de Arquivos
- Manter módulos separados por responsabilidade
- Usar nomes descritivos para funções e classes
- Adicionar docstrings a todas as funções públicas

### Código
- Seguir PEP 8 para Python
- Usar type hints quando possível
- Adicionar comentários para lógica complexa

### Commits
- Mensagens claras e descritivas
- Um feature/fix por commit quando possível
- Usar prefixos: `feat:`, `fix:`, `refactor:`, `docs:`

## 8. Troubleshooting

### Problema: Streamlit não inicia
**Solução:**
```bash
streamlit cache clear
streamlit run frontend/app.py
```

### Problema: Módulo não encontrado
**Solução:**
```bash
pip install -r requirements.txt --upgrade
```

### Problema: Porta em uso
**Solução:**
```bash
# Backend em porta diferente
python backend/run.py (modificar em run.py)

# Frontend em porta diferente
streamlit run frontend/app.py --server.port 8502
```

## 9. Próximos Passos

1. Implementar autenticação com JWT
2. Conectar com banco de dados real
3. Adicionar testes automatizados
4. Configurar CI/CD
5. Containerizar com Docker

---

**Data de Criação:** 20/01/2025
**Versão:** 1.0.0
