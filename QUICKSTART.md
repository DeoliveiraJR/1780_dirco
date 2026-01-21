# 🚀 Guia Rápido de Início

Bem-vindo ao UAN Dashboard! Este guia ajuda você a iniciar rapidamente.

## ⚡ Início em 5 Minutos

### 1️⃣ Preparar Ambiente

```bash
# Clonar/abrir o projeto
cd UAN

# Criar ambiente virtual
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate
# Ativar (Linux/macOS)
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2️⃣ Gerar Dados de Teste

```bash
cd data/raw
python generate_mock_data.py
cd ../..
```

Resultado: `projecoes_financeiras.xlsx` criado com 192 registros.

### 3️⃣ Iniciar Backend (Terminal 1)

```bash
python backend/run.py
```

✅ Backend rodando em `http://localhost:5000`

### 4️⃣ Iniciar Frontend (Terminal 2)

```bash
streamlit run frontend/app.py
```

✅ Frontend rodando em `http://localhost:8501`

## 📍 Navegação

- **🔐 Autenticação**: Login (não funcional - use "teste@uan.com.br" / "123456")
- **📊 Dashboard**: Visualizar gráficos e tabelas com dados
- **🎯 Simulador**: Criar e gerenciar simulações
- **👤 Perfil**: Dados do usuário, segurança, histórico

## 🧪 Testando

### Backend
```bash
# Verificar status
curl http://localhost:5000/api/data/status

# Obter dados (exemplo)
curl "http://localhost:5000/api/data/dados?categoria=Pessoa%20Física"
```

### Frontend
- Navegar pelas abas
- Testar filtros no Dashboard
- Criar simulação no Simulador
- Visualizar perfil

## 📁 Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `backend/run.py` | Inicia servidor Flask |
| `frontend/app.py` | Inicia interface Streamlit |
| `data/raw/generate_mock_data.py` | Gera dados de teste |
| `requirements.txt` | Dependências Python |
| `README.md` | Documentação completa |
| `SETUP.md` | Setup detalhado |

## 🔧 Troubleshooting Rápido

**Porta 5000 em uso?**
```bash
# Editar backend/run.py e mudar port para 5001
python backend/run.py
```

**Streamlit não abre?**
```bash
streamlit cache clear
streamlit run frontend/app.py --server.port 8502
```

**Módulo não encontrado?**
```bash
pip install -r requirements.txt --upgrade
```

## 📈 Estrutura de Dados

Arquivo Excel tem estas colunas:
- `DATA_COMPLETA`: 01/01/2025
- `MES`: janeiro
- `ANO`: 2025
- `CATEGORIA`: Pessoa Física
- `CURVA_REALIZADO`: R$ 2.500,00
- `PROJETADO_ANALITICO`: R$ 2.600,00
- `PROJETADO_MERCADO`: R$ 2.400,00
- `PROJETADO_AJUSTADO`: R$ 2.550,00

## 🎯 Próximas Ações

1. ✅ Setup completo
2. ✅ Dados mockados
3. ⏭️ Testar endpoints
4. ⏭️ Explorar dashboard
5. ⏭️ Criar simulações

## 💬 Dúvidas?

Consulte:
- `README.md` - Documentação completa
- `SETUP.md` - Setup detalhado
- `DEVELOPMENT.md` - Histórico e arquitetura

---

**Tudo pronto! Divirta-se explorando o UAN Dashboard! 🎉**
