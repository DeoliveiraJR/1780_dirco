# Backend - UAN Dashboard DIRCO

## Objetivo deste documento

Este README foi criado para explicar, de forma simples e prática, como a camada de backend do projeto funciona hoje, quais partes são mockadas, onde os dados ficam armazenados, quais arquivos são importantes para manutenção e qual é o plano recomendado para evoluir para um backend completo no final do projeto.

A ideia é que este documento sirva como material de consulta para:
- manutenção do projeto;
- entendimento da estrutura atual;
- onboarding de novos responsáveis;
- planejamento da futura implementação definitiva de backend e API.

---

## Resumo executivo

Hoje o projeto **não utiliza um backend transacional completo com banco de dados relacional em produção**.

O que existe atualmente é uma arquitetura híbrida com:
- **Frontend em Streamlit** como camada principal da aplicação;
- **persistência mockada em arquivos locais** no diretório `backend/database/`;
- **algumas estruturas Flask legadas/MVP** dentro de `backend/app/`, que funcionam como base conceitual para a futura API;
- **estado temporário no frontend** usando `st.session_state`;
- **sincronização local no navegador** via `localStorage` para componentes interativos do simulador com Bokeh.

Em outras palavras:
- o sistema já possui persistência;
- porém essa persistência ainda é baseada principalmente em **arquivos JSON/XLSX/PKL**, e não em tabelas reais de banco;
- o backend atual serve como **camada mockada e funcional**, suficiente para o estágio atual do projeto;
- ao final do projeto, a recomendação é migrar para uma arquitetura de API + banco estruturado.

---

## Situação atual da arquitetura

## Como o sistema funciona hoje

Hoje o sistema opera com quatro camadas principais:

### 1. Frontend principal
O frontend é a camada central da aplicação e está implementado em Streamlit.

Ele é responsável por:
- autenticação visual e controle de sessão;
- upload de arquivos Excel;
- renderização do simulador;
- renderização da DRE;
- aplicação de filtros;
- edição de curvas e metodologias;
- acionamento das funções de persistência.

### 2. Backend mockado em arquivos
A pasta `backend/` contém a lógica de persistência local do projeto.

Em vez de salvar tudo em banco de dados, o sistema salva informações em arquivos como:
- `.json`
- `.xlsx`
- `.pkl`

Esses arquivos representam, na prática, as “tabelas mockadas” do sistema atual.

### 3. Estado de sessão do Streamlit
Parte do comportamento da aplicação depende de `st.session_state`.

Esse estado é usado para:
- guardar filtros ativos;
- guardar simulações carregadas na sessão;
- controlar modo de edição;
- manter estruturas temporárias da DRE;
- evitar recálculos e rerenders desnecessários.

### 4. LocalStorage do navegador
O `localStorage` é usado principalmente no simulador para sincronizar interações do gráfico/tabela Bokeh com o frontend.

Importante:
- o `localStorage` **não é o banco principal do projeto**;
- ele é apenas um mecanismo auxiliar de sincronização do lado do navegador;
- a persistência “durável” continua sendo feita em arquivos locais no backend mockado.

---

## Estrutura atual da pasta backend

```text
backend/
├─ app/
│  ├─ models/
│  ├─ routes/
│  ├─ services/
│  └─ __init__.py
├─ database/
│  ├─ dados/
│  ├─ indices/
│  ├─ metadata/
│  ├─ simulacoes/
│  ├─ uploads/
│  ├─ dre_linhas_store.json
│  └─ users.json
├─ README.md
├─ database.py
├─ database_schema.py
├─ debug_schema.py
├─ run.py
└─ test_fluxo.py
```

---

## O papel de cada arquivo principal

### `backend/database.py`
É o principal arquivo de persistência mockada do projeto.

Responsabilidades principais:
- carregar usuários;
- validar login;
- salvar uploads da base compartilhada;
- salvar e carregar simulações por usuário;
- salvar e carregar base compartilhada;
- gerenciar metadados de upload;
- processar e salvar índices econômicos;
- manter persistência de estruturas da DRE.

Esse é hoje o arquivo mais importante do “backend real em uso”.

### `backend/database_schema.py`
É o responsável por transformar dados importados em uma estrutura JSON organizada por produto, cliente, categoria, ano e projeções.

Responsabilidades principais:
- converter Excel para schema estruturado;
- salvar dados por usuário;
- carregar dados por usuário;
- consultar curvas ajustadas;
- atualizar projeções já estruturadas.

Esse arquivo representa a lógica de “normalização” dos dados importados para o modelo interno do sistema.

### `backend/app/`
Essa pasta contém uma estrutura Flask de MVP/legado, pensada como base para a futura API.

Ela já demonstra a direção arquitetural desejada:
- `routes/` para endpoints;
- `services/` para regras de negócio;
- `models/` para modelos de dados;
- `app/__init__.py` como application factory.

Hoje essa camada existe mais como fundação arquitetural e referência de evolução do que como backend principal da aplicação Streamlit.

### `backend/run.py`
Script simples para subir o servidor Flask legado de desenvolvimento.

### `backend/database/`
É a “base de dados mockada” do projeto.

É onde os dados persistidos ficam salvos localmente em arquivos.

---

## Estrutura atual das “tabelas” mockadas

Como ainda não existe banco relacional definitivo, hoje as tabelas são representadas por arquivos.

## 1. Usuários

Arquivo:
- `backend/database/users.json`

Função:
- armazenar usuários mockados do sistema;
- login;
- perfil;
- role/permissão.

Campos típicos:
- `id`
- `email`
- `nome`
- `senha`
- `role`
- `departamento`
- `funcao`
- `data_criacao`
- `ativo`

Observação:
- hoje as credenciais ainda estão em JSON local;
- em produção isso deve migrar para tabela de usuários com senha criptografada.

---

## 2. Base compartilhada de dados

Arquivos principais:
- `backend/database/uploads/base_dados_compartilhada.xlsx`
- `backend/database/uploads/base_dados_compartilhada.pkl`

Função:
- armazenar a base compartilhada importada pelo admin;
- servir de fonte para páginas como Simulador e DRE;
- manter leitura mais rápida via cache em `.pkl`.

Importante:
- o Excel original pode conter abas como `DADOS`, `TD_DRE` e `INDICES_TESOU`;
- o sistema atual combina corretamente `DADOS` + `TD_DRE` para evitar DRE zerada;
- o `.pkl` é apenas cache de leitura, não a fonte primária de negócio.

---

## 3. Bases personalizadas por usuário

Arquivos típicos:
- `backend/database/uploads/base_usuario_usr_001.xlsx`
- `backend/database/uploads/base_usuario_usr_002.xlsx`

Função:
- isolar a base de trabalho do usuário quando necessário;
- preservar cenários e ajustes sem afetar imediatamente a base compartilhada.

Uso prático:
- são cópias locais da base principal para suportar isolamento de edição/simulação.

---

## 4. Dados estruturados por usuário

Arquivos:
- `backend/database/dados/usr_001_dados.json`
- `backend/database/dados/usr_002_dados.json`

Função:
- armazenar os dados transformados pelo schema interno;
- organizar projeções por produto, cliente, categoria e ano;
- permitir busca estruturada da curva ajustada.

Essa camada já se parece mais com uma tabela de negócio do que o Excel bruto.

---

## 5. Simulações do simulador por usuário

Arquivos:
- `backend/database/simulacoes/usr_001_simulacoes.json`
- `backend/database/simulacoes/usr_002_simulacoes.json`

Função:
- guardar curvas ajustadas criadas no simulador;
- manter histórico/cenários por usuário;
- permitir restauração e continuidade de trabalho.

Campos comuns:
- `id`
- `combo_key`
- `cliente`
- `categoria`
- `produto`
- `curva`
- `nome`
- `data_criacao`
- `data_atualizacao`

---

## 6. Metadados de upload

Arquivos:
- `backend/database/metadata/ultimo_upload_dados.json`
- `backend/database/metadata/ultimo_upload_indices.json`

Função:
- registrar qual arquivo foi importado;
- salvar data/hora do upload;
- guardar abas disponíveis;
- registrar colunas e volume de linhas;
- facilitar auditoria e troubleshooting.

---

## 7. Índices econômicos estruturados

Arquivos:
- `backend/database/uploads/base_indices_compartilhada.xlsx`
- `backend/database/indices/indices_compartilhados.json`

Função:
- armazenar a aba `INDICES_TESOU`;
- normalizar os registros de índices;
- disponibilizar séries históricas para uso na DRE.

Campos esperados na base de índices:
- `DT_ALVO`
- `DT_PRJ`
- `VL_PJTD`
- `NM_IN`

---

## 8. Estruturas persistidas da DRE

Arquivo:
- `backend/database/dre_linhas_store.json`

Função:
- persistir a estrutura da DRE por escopo;
- armazenar linhas, metodologias e estados calculados;
- suportar restauração da DRE em cenários específicos.

Observação importante:
- hoje a DRE possui regras de persistência próprias e parte do comportamento depende também de `session_state`;
- portanto este arquivo não deve ser interpretado como única fonte da verdade sem considerar a lógica do frontend.

---

## Como funciona o fluxo atual do backend

## Fluxo 1. Upload da base pelo admin

1. O usuário admin faz upload do Excel na interface.
2. O sistema identifica as abas disponíveis.
3. Se existir `DADOS`, ela é processada como base principal.
4. Se existir `TD_DRE`, ela é preservada para compor corretamente a DRE.
5. Se existir `INDICES_TESOU`, ela é processada separadamente.
6. Os arquivos são salvos em `backend/database/uploads/`.
7. Os metadados do upload são salvos em `backend/database/metadata/`.
8. Os dados também podem ser convertidos para JSON estruturado por usuário.
9. O cache `.pkl` da base é renovado.

Resultado:
- a base compartilhada passa a ser a referência do sistema.

---

## Fluxo 2. Simulador

1. O frontend carrega a base compartilhada.
2. O usuário aplica filtros.
3. O gráfico/tabela Bokeh permite ajustes.
4. Parte das mudanças transitórias trafega pelo `localStorage`.
5. Ao salvar, a curva ajustada é persistida no backend mockado.
6. A simulação é gravada em `backend/database/simulacoes/`.

Resultado:
- a simulação fica restaurável.

---

## Fluxo 3. DRE

1. A DRE lê a base correta, respeitando filtros e contexto.
2. Componentes da DRE podem usar `TD_DRE`, dados simulados, índices e metodologias.
3. O sistema recalcula fórmulas e estruturas conforme o contexto.
4. Parte do estado fica em sessão.
5. Parte é persistida em arquivo para restauração posterior.

Resultado:
- a DRE consegue operar mesmo sem backend SQL final, usando a persistência mockada atual.

---

## O que está mockado hoje

Hoje estão mockados principalmente:

- cadastro e autenticação de usuários por `users.json`;
- persistência de projeções por arquivos JSON;
- persistência de simulações por usuário em JSON;
- base compartilhada em arquivos Excel locais;
- cache local em `.pkl`;
- estruturas da DRE em arquivos JSON;
- parte do fluxo de sincronização frontend por `session_state` e `localStorage`.

Isso significa que:
- o sistema funciona;
- porém ainda não possui todos os controles típicos de produção empresarial, como:
  - banco relacional;
  - autenticação robusta;
  - versionamento transacional;
  - auditoria completa;
  - API REST central como camada oficial única.

---

## Papel do localStorage no projeto

Como houve dúvida sobre isso, aqui está a explicação correta:

O `localStorage` é usado no projeto, mas **não como backend principal**.

Ele é utilizado como apoio em interações do simulador para:
- sincronizar valores editados no Bokeh;
- transportar alterações temporárias do navegador para o Streamlit;
- evitar perda imediata de edição antes do save;
- ajudar na integração entre frontend e componente gráfico.

Portanto:
- `localStorage` = apoio de sincronização no navegador;
- `session_state` = estado temporário do lado Streamlit;
- `backend/database/*.json|xlsx|pkl` = persistência mockada atual.

---

## Limitações da arquitetura atual

A arquitetura atual atende bem ao estágio do projeto, mas possui limitações naturais:

- persistência baseada em arquivos pode ser sensível a concorrência;
- múltiplos usuários simultâneos exigem mais cuidado;
- login em JSON não é seguro para produção;
- trilha de auditoria ainda é limitada;
- não há banco relacional consolidando tudo;
- não há API REST definitiva atendendo frontend externo;
- parte do estado ainda depende do processo do Streamlit e da sessão do navegador.

---

## Quando essa arquitetura atual é suficiente

Ela é suficiente para:
- MVP funcional;
- homologação;
- prototipagem;
- uso controlado por equipe pequena;
- validação de regras de negócio;
- refinamento das regras da DRE e do simulador antes da versão final.

---

## Arquitetura recomendada para o backend final

A recomendação para o backend definitivo é separar claramente:

### 1. Frontend
- Streamlit, ou no futuro outra camada visual se necessário.

### 2. API backend oficial
- FastAPI ou Flask estruturado;
- autenticação;
- regras de negócio;
- validação;
- versionamento de simulações;
- auditoria.

### 3. Banco de dados relacional
Sugestão:
- PostgreSQL.

### 4. Camada de arquivos
Para armazenar:
- uploads originais;
- anexos;
- exports;
- snapshots quando necessário.

---

## Proposta de arquitetura final

```text
Frontend (Streamlit)
        |
        v
API Backend
        |
        +-- Auth / Usuários / Permissões
        +-- Upload / Ingestão de Arquivos
        +-- Simulações
        +-- DRE / Metodologias
        +-- Índices Econômicos
        +-- Auditoria / Versionamento
        |
        v
Banco de Dados Relacional (PostgreSQL)
        |
        +-- tabelas de negócio
        +-- histórico de versões
        +-- relacionamentos
```

---

## Checklist de implementação do backend final

## Etapa 1. Definir o modelo de dados oficial

### Tabelas recomendadas

#### `usuarios`
Finalidade:
- cadastro de usuários;
- autenticação;
- perfil;
- permissões.

Campos recomendados:
- `id`
- `nome`
- `email`
- `senha_hash`
- `role`
- `departamento`
- `ativo`
- `created_at`
- `updated_at`

#### `uploads`
Finalidade:
- registrar todo upload de arquivo.

Campos recomendados:
- `id`
- `usuario_id`
- `nome_arquivo_original`
- `tipo_upload`
- `caminho_arquivo`
- `status_processamento`
- `data_upload`
- `metadata_json`

#### `bases_compartilhadas`
Finalidade:
- versionar a base ativa do sistema.

Campos recomendados:
- `id`
- `upload_id`
- `versao`
- `ativa`
- `data_ativacao`
- `created_at`

#### `produtos`
Finalidade:
- catálogo mestre de produtos.

Campos recomendados:
- `id`
- `codigo_produto`
- `nome_produto`
- `categoria`
- `cliente_tipo`
- `cod_bloco`
- `cod_categoria`
- `ativo`

#### `projecoes_produto`
Finalidade:
- armazenar projeções mensais por produto/ano/mês.

Campos recomendados:
- `id`
- `produto_id`
- `ano`
- `mes`
- `realizado`
- `projetado_analitico`
- `projetado_mercado`
- `projetado_ajustado`
- `fonte`
- `created_at`
- `updated_at`

#### `simulacoes`
Finalidade:
- cabeçalho da simulação.

Campos recomendados:
- `id`
- `usuario_id`
- `nome`
- `descricao`
- `status`
- `versao`
- `ativa`
- `created_at`
- `updated_at`

#### `simulacao_itens`
Finalidade:
- valores da curva ajustada por produto dentro de cada simulação.

Campos recomendados:
- `id`
- `simulacao_id`
- `produto_id`
- `ano`
- `mes`
- `valor_ajustado`
- `preenchido`
- `origem_valor`

#### `indices_economicos`
Finalidade:
- armazenar séries históricas de índices.

Campos recomendados:
- `id`
- `nome_indice`
- `data_alvo`
- `data_projecao`
- `valor_projetado`
- `payload_extra_json`

#### `dre_estruturas`
Finalidade:
- cadastro das linhas da DRE.

Campos recomendados:
- `id`
- `codigo_linha`
- `descricao`
- `tipo_linha`
- `ordem_exibicao`
- `eh_totalizador`
- `ativo`

#### `dre_cenarios`
Finalidade:
- cabeçalho de cenários DRE por usuário/filtro/simulação.

Campos recomendados:
- `id`
- `usuario_id`
- `simulacao_id`
- `ano_referencia`
- `cliente`
- `categoria`
- `produto`
- `cd_tip_agpd`
- `tip_td`
- `revisao`
- `created_at`
- `updated_at`

#### `dre_valores`
Finalidade:
- valores mensais por linha DRE.

Campos recomendados:
- `id`
- `dre_cenario_id`
- `codigo_linha`
- `mes`
- `valor`
- `preenchido`
- `origem`
- `created_at`

#### `dre_metodologias`
Finalidade:
- registrar metodologias aplicadas na DRE.

Campos recomendados:
- `id`
- `dre_cenario_id`
- `codigo_linha_destino`
- `nome_metodologia`
- `formula`
- `periodo_inicio`
- `periodo_fim`
- `parametros_json`
- `created_at`

#### `logs_auditoria`
Finalidade:
- rastrear alterações importantes.

Campos recomendados:
- `id`
- `usuario_id`
- `entidade`
- `entidade_id`
- `acao`
- `payload_json`
- `created_at`

---

## Etapa 2. Criar a API oficial

### Módulos recomendados da API

#### Auth
Endpoints sugeridos:
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

#### Usuários
- `GET /api/usuarios`
- `POST /api/usuarios`
- `PATCH /api/usuarios/{id}`

#### Uploads
- `POST /api/uploads/base`
- `POST /api/uploads/indices`
- `GET /api/uploads/ultimo`
- `GET /api/uploads/{id}/status`

#### Produtos e projeções
- `GET /api/produtos`
- `GET /api/projecoes`
- `GET /api/projecoes/{produto_id}`
- `PATCH /api/projecoes/{produto_id}`

#### Simulações
- `GET /api/simulacoes`
- `POST /api/simulacoes`
- `GET /api/simulacoes/{id}`
- `PATCH /api/simulacoes/{id}`
- `POST /api/simulacoes/{id}/ativar`
- `POST /api/simulacoes/{id}/duplicar`

#### DRE
- `GET /api/dre/contexto`
- `GET /api/dre/cenario`
- `POST /api/dre/cenario`
- `PATCH /api/dre/linhas/{codigo}`
- `POST /api/dre/metodologias`
- `DELETE /api/dre/metodologias/{id}`

#### Índices econômicos
- `GET /api/indices`
- `GET /api/indices/{nome}`
- `POST /api/indices/upload`

#### Auditoria
- `GET /api/auditoria`
- `GET /api/auditoria/{entidade}/{id}`

---

## Etapa 3. Definir a arquitetura do backend final

### Camadas recomendadas

#### Camada 1. Routes / Controllers
Responsável por:
- receber requisições;
- validar entrada;
- chamar services;
- devolver resposta HTTP.

#### Camada 2. Services
Responsável por:
- regras de negócio;
- orquestração;
- versionamento;
- cálculos transacionais;
- integração DRE e simulador.

#### Camada 3. Repositories
Responsável por:
- acesso ao banco;
- queries;
- persistência;
- isolamento do ORM.

#### Camada 4. Models / Schemas
Responsável por:
- entidades;
- validações;
- contratos de entrada e saída.

#### Camada 5. Infraestrutura
Responsável por:
- conexão com banco;
- migrations;
- fila futura;
- storage de arquivos;
- logs.

---

## Checklist sugerido de execução por fases

### Fase 1. Preparação
- mapear todas as entidades atuais em arquivos;
- congelar a estrutura mínima de dados;
- definir banco escolhido;
- definir framework da API;
- definir autenticação.

### Fase 2. Banco de dados
- criar migrations;
- criar tabelas principais;
- popular usuários iniciais;
- criar tabelas de auditoria e versionamento.

### Fase 3. Upload e ingestão
- criar endpoint de upload;
- persistir arquivo bruto;
- processar abas `DADOS`, `TD_DRE` e `INDICES_TESOU`;
- versionar base compartilhada;
- gerar logs de processamento.

### Fase 4. Simulador
- migrar save/load das simulações para banco;
- armazenar curvas por produto e período;
- permitir ativação de versão de simulação;
- controlar revisão da simulação ativa.

### Fase 5. DRE
- persistir cenários DRE por escopo;
- persistir linhas, metodologias e flags de preenchimento;
- garantir sincronização com simulação ativa;
- permitir restauração confiável de cenário.

### Fase 6. Segurança e governança
- implementar senha hash;
- controle de permissões;
- logs de auditoria;
- rastreabilidade de alterações.

### Fase 7. Desligamento do mock local
- migrar leitura dos JSON/XLSX para banco;
- reduzir dependência de arquivos locais;
- manter apenas storage de anexos e exports;
- descontinuar persistência crítica em `session_state` e JSON local.

---

## Recomendação importante de manutenção no estado atual

Enquanto o backend definitivo não for implementado, recomenda-se:

- manter backup da pasta `backend/database/`;
- evitar edição manual de arquivos JSON sem conhecimento da estrutura;
- usar sempre os fluxos da aplicação para salvar simulações e DRE;
- tratar arquivos `.pkl` apenas como cache;
- não considerar `localStorage` como fonte definitiva de dados;
- validar sempre o último upload em `metadata/`;
- revisar se a base compartilhada contém as abas necessárias para a DRE.

---

## O que o cliente precisa saber em uma frase

Hoje o projeto já possui persistência funcional, mas ela ainda é baseada em arquivos locais e estado de sessão; o backend final planejado será uma API estruturada com banco relacional, versionamento, auditoria e maior segurança.

---

## Arquivos mais importantes para manutenção imediata

- `backend/database.py`
- `backend/database_schema.py`
- `backend/database/users.json`
- `backend/database/uploads/`
- `backend/database/simulacoes/`
- `backend/database/dados/`
- `backend/database/indices/`
- `backend/database/metadata/`
- `backend/database/dre_linhas_store.json`

---

## Status atual

- Backend definitivo com banco relacional: **não implementado ainda**
- Persistência mockada local: **implementada e em uso**
- Estrutura Flask MVP/legada: **existente**
- Integração principal da aplicação: **Streamlit + persistência local**
- Simulador com apoio de `localStorage`: **sim**
- DRE com persistência híbrida de sessão + arquivo: **sim**

---

## Próximo objetivo recomendado

O próximo grande passo técnico do projeto é transformar o backend mockado atual em um backend oficial com:
- API;
- banco relacional;
- autenticação segura;
- versionamento de simulações;
- persistência sólida da DRE;
- trilha de auditoria.

Esse passo deve ser tratado como fase final de consolidação da arquitetura do produto.