"""
Data Manager - Gerencia dados compartilhados entre páginas
Armazena dados do upload, simulações e curvas ajustadas persistentes
"""

import pandas as pd
import streamlit as st
import json
from datetime import datetime
from typing import Optional, List, Dict


# ============================================================================
# INICIALIZAÇÃO DO SESSION STATE
# ============================================================================
def init_data_state():
    if "dados_upload" not in st.session_state:
        st.session_state.dados_upload = None
    if "dados_upload_original" not in st.session_state:
        st.session_state.dados_upload_original = None  # Backup do upload original
    if "simulacoes" not in st.session_state:
        st.session_state.simulacoes = []
    if "simulacoes_salvas" not in st.session_state:
        st.session_state.simulacoes_salvas = {}  # {usuario: [lista de simulações]}
    if "metricas_dashboard" not in st.session_state:
        st.session_state.metricas_dashboard = {
            "valor_total": 0,
            "realizado_atual": 0,
            "taxa_acuracia": 0,
            "simulacoes_ativas": 0
        }
    if "ajustada" not in st.session_state:
        st.session_state.ajustada = [0.0] * 12
    if "ajustes_categoria" not in st.session_state:
        st.session_state.ajustes_categoria = {}
    if "sync_counter" not in st.session_state:
        st.session_state.sync_counter = 0
    if "last_combo" not in st.session_state:
        st.session_state.last_combo = None
    # ============== NOVO: Curvas ajustadas persistentes por combo ==============
    if "curvas_ajustadas_persistentes" not in st.session_state:
        # Estrutura: {combo_key: {"curva": [12], "data_salvo": iso, "nome": str}}
        st.session_state.curvas_ajustadas_persistentes = {}
    if "historico_simulacoes" not in st.session_state:
        # Histórico completo de todas as simulações salvas
        st.session_state.historico_simulacoes = []
    if "scores_mape" not in st.session_state:
        # Dicionário {cod_produto: mape_value} para o card SCORE
        st.session_state.scores_mape = {}
        _carregar_scores_mape()


def _carregar_scores_mape():
    """
    Carrega tabela de SCORES (MAPE por produto) do arquivo CSV.
    O MAPE é a métrica de erro do modelo de ML para cada produto.
    """
    import os
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data", "raw", "scores_mape.csv"
    )
    try:
        if os.path.exists(csv_path):
            import pandas as pd
            df_scores = pd.read_csv(csv_path)
            st.session_state.scores_mape = dict(
                zip(df_scores['COD_BLOCO'].astype(str), df_scores['MAPE'])
            )
            print(f"[SCORES] Carregados {len(st.session_state.scores_mape)} scores")
    except Exception as e:
        print(f"[SCORES] Erro ao carregar scores: {e}")
        st.session_state.scores_mape = {}


def get_score_mape(cod_produto: str) -> float:
    """
    Retorna o MAPE (score) para um código de produto.
    Retorna None se não encontrado.
    """
    if not st.session_state.scores_mape:
        _carregar_scores_mape()
    return st.session_state.scores_mape.get(str(cod_produto), None)


def get_score_by_produto_nome(produto_nome: str, df=None) -> float:
    """
    Busca o MAPE pelo nome do produto.
    Tenta extrair o código do nome se estiver no formato "CODIGO: NOME"
    ou busca na coluna COD_PRODUTO do DataFrame.
    """
    # Tenta extrair código do nome (formato "111111120: INVESTIMENTO")
    if ':' in str(produto_nome):
        codigo = str(produto_nome).split(':')[0].strip()
        mape = get_score_mape(codigo)
        if mape is not None:
            return mape
    
    # Busca no DataFrame se disponível
    if df is not None and not df.empty:
        if 'COD_PRODUTO' in df.columns:
            # Normaliza para comparação
            df_filtered = df[df['PRODUTO'].astype(str).str.lower().str.strip() 
                           == str(produto_nome).lower().strip()]
            if not df_filtered.empty:
                cod = str(df_filtered.iloc[0]['COD_PRODUTO'])
                mape = get_score_mape(cod)
                if mape is not None:
                    return mape
    
    return None


# ============================================================================
# RESET COMPLETO - Limpa todos os estados
# ============================================================================
def resetar_tudo():
    """
    Reseta completamente todos os estados do session_state.
    Deve ser chamado quando quiser começar do zero.
    """
    st.session_state.dados_upload = None
    st.session_state.simulacoes = []
    st.session_state.simulacoes_salvas = {}
    st.session_state.metricas_dashboard = {
        "valor_total": 0,
        "realizado_atual": 0,
        "taxa_acuracia": 0,
        "simulacoes_ativas": 0
    }
    st.session_state.ajustada = [0.0] * 12
    st.session_state.ajustes_categoria = {}
    st.session_state.sync_counter = 0
    st.session_state.last_combo = None
    st.session_state.filtros = {}
    st.session_state.curva_analitica = []
    st.session_state.curva_mercado = []
    # Flag para limpar localStorage no próximo render
    st.session_state._limpar_localStorage = True


def resetar_simulacao_atual():
    """
    Reseta apenas a simulação atual (curva ajustada volta para analítica).
    Mantém os dados de upload e simulações salvas.
    """
    st.session_state.ajustada = st.session_state.get("curva_analitica", [0.0] * 12)[:]
    st.session_state.sync_counter = st.session_state.get("sync_counter", 0) + 1
    st.session_state.ajustes_categoria = {}
    st.session_state._limpar_localStorage = True


# ============================================================================
# DADOS DE UPLOAD
# ============================================================================
def set_dados_upload(df):
    """Armazena dados do upload no session state"""
    st.session_state.dados_upload = df
    # Guarda backup do original para referência
    if st.session_state.dados_upload_original is None:
        st.session_state.dados_upload_original = df.copy() if df is not None else None
    atualizar_metricas_dashboard()


def get_dados_upload():
    """Recupera dados do upload (com curvas ajustadas aplicadas)"""
    return st.session_state.dados_upload


def get_dados_upload_original():
    """Recupera dados originais do upload (sem ajustes)"""
    return st.session_state.dados_upload_original


# ============================================================================
# PERSISTÊNCIA DE CURVAS AJUSTADAS
# ============================================================================
def _gerar_combo_key(cliente: str, categoria: str, produto: str) -> str:
    """Gera chave única para combinação cliente/categoria/produto"""
    return f"{cliente or 'Todos'}::{categoria}::{produto}"


def salvar_curva_ajustada(cliente: str, categoria: str, produto: str, 
                          curva: List[float], nome_simulacao: str = "") -> bool:
    """
    Salva a curva ajustada para uma combinação específica.
    Persiste no session_state e atualiza o DataFrame principal.
    
    Args:
        cliente: Nome do cliente (ou "Todos")
        categoria: Nome da categoria
        produto: Nome do produto
        curva: Lista com 12 valores mensais
        nome_simulacao: Nome opcional da simulação
        
    Returns:
        True se salvo com sucesso
    """
    combo_key = _gerar_combo_key(cliente, categoria, produto)
    
    # Garante que curva tem 12 elementos
    curva_normalizada = (list(curva) + [0.0] * 12)[:12]
    
    # Salva no dicionário de curvas persistentes
    st.session_state.curvas_ajustadas_persistentes[combo_key] = {
        "curva": curva_normalizada,
        "data_salvo": datetime.now().isoformat(),
        "nome": nome_simulacao,
        "cliente": cliente,
        "categoria": categoria,
        "produto": produto
    }
    
    # Adiciona ao histórico
    entrada_historico = {
        "id": f"{combo_key}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "combo_key": combo_key,
        "cliente": cliente,
        "categoria": categoria,
        "produto": produto,
        "curva": curva_normalizada,
        "nome": nome_simulacao,
        "data_criacao": datetime.now().isoformat(),
        "usuario": st.session_state.get("usuario", "anonimo")
    }
    st.session_state.historico_simulacoes.append(entrada_historico)
    
    # Aplica a curva ajustada no DataFrame principal
    _aplicar_curva_no_dataframe(cliente, categoria, produto, curva_normalizada)
    
    # Atualiza métricas
    atualizar_metricas_dashboard()
    
    print(f"[PERSIST] Curva salva: {combo_key} = {curva_normalizada[:3]}...")
    return True


def carregar_curva_ajustada(cliente: str, categoria: str, produto: str) -> Optional[List[float]]:
    """
    Carrega a curva ajustada salva para uma combinação específica.
    
    Returns:
        Lista com 12 valores ou None se não existir
    """
    combo_key = _gerar_combo_key(cliente, categoria, produto)
    dados = st.session_state.curvas_ajustadas_persistentes.get(combo_key)
    
    if dados and "curva" in dados:
        print(f"[PERSIST] Curva carregada: {combo_key}")
        return dados["curva"]
    
    return None


def existe_curva_salva(cliente: str, categoria: str, produto: str) -> bool:
    """Verifica se existe curva salva para a combinação"""
    combo_key = _gerar_combo_key(cliente, categoria, produto)
    return combo_key in st.session_state.curvas_ajustadas_persistentes


def listar_curvas_salvas() -> Dict[str, dict]:
    """Retorna todas as curvas salvas"""
    return st.session_state.curvas_ajustadas_persistentes.copy()


def get_historico_simulacoes() -> List[dict]:
    """Retorna histórico completo de simulações"""
    return st.session_state.historico_simulacoes.copy()


def _aplicar_curva_no_dataframe(cliente: str, categoria: str, produto: str, 
                                 curva: List[float]) -> None:
    """
    Aplica a curva ajustada diretamente no DataFrame de dados.
    Atualiza a coluna PROJETADO_AJUSTADO para o produto/categoria específico.
    """
    df = st.session_state.dados_upload
    if df is None or df.empty:
        return
    
    # Normalização de texto para comparação
    def _norm(s):
        import unicodedata
        if s is None:
            return ""
        s = unicodedata.normalize("NFKD", str(s))
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        return s.strip().lower()
    
    # Identificar coluna de cliente
    col_cli = None
    if "TIPO_CLIENTE" in df.columns:
        col_cli = "TIPO_CLIENTE"
    elif "TP_CLIENTE" in df.columns:
        col_cli = "TP_CLIENTE"
    
    # Identificar coluna de mês
    if "MES_NUM" not in df.columns and "MES" in df.columns:
        df["MES_NUM"] = df["MES"].apply(lambda x: _mes_to_num_simple(x))
    
    # Garantir coluna PROJETADO_AJUSTADO existe
    if "PROJETADO_AJUSTADO" not in df.columns:
        if "PROJETADO_ANALITICO" in df.columns:
            df["PROJETADO_AJUSTADO"] = df["PROJETADO_ANALITICO"].copy()
        else:
            df["PROJETADO_AJUSTADO"] = 0.0
    
    # Máscara para filtrar registros do produto/categoria/cliente
    mask = (df["CATEGORIA"].astype(str).apply(_norm) == _norm(categoria)) & \
           (df["PRODUTO"].astype(str).apply(_norm) == _norm(produto))
    
    if cliente and cliente != "Todos" and col_cli:
        mask = mask & (df[col_cli].astype(str).apply(_norm) == _norm(cliente))
    
    # Atualizar valores por mês
    for i, valor in enumerate(curva):
        mes_num = i + 1  # Mês 1-12
        mask_mes = mask & (df["MES_NUM"] == mes_num)
        
        if mask_mes.any():
            df.loc[mask_mes, "PROJETADO_AJUSTADO"] = valor
    
    # Atualiza o DataFrame no session_state
    st.session_state.dados_upload = df
    print(f"[PERSIST] DataFrame atualizado: {categoria}/{produto} com {len(curva)} meses")


def _mes_to_num_simple(mes: str) -> int:
    """Converte nome do mês para número (1-12)"""
    meses = {
        "jan": 1, "janeiro": 1,
        "fev": 2, "fevereiro": 2,
        "mar": 3, "março": 3, "marco": 3,
        "abr": 4, "abril": 4,
        "mai": 5, "maio": 5,
        "jun": 6, "junho": 6,
        "jul": 7, "julho": 7,
        "ago": 8, "agosto": 8,
        "set": 9, "setembro": 9,
        "out": 10, "outubro": 10,
        "nov": 11, "novembro": 11,
        "dez": 12, "dezembro": 12
    }
    mes_lower = str(mes).lower().strip()[:3]
    return meses.get(mes_lower, 0)


def aplicar_todas_curvas_salvas() -> int:
    """
    Aplica TODAS as curvas salvas ao DataFrame principal.
    Deve ser chamada ao iniciar a página para garantir que 
    todas as curvas persistidas estejam refletidas nos dados.
    
    Returns:
        Quantidade de curvas aplicadas
    """
    curvas = st.session_state.curvas_ajustadas_persistentes
    if not curvas:
        return 0
    
    count = 0
    for combo_key, dados in curvas.items():
        curva = dados.get("curva", [])
        cliente = dados.get("cliente", "Todos")
        categoria = dados.get("categoria", "")
        produto = dados.get("produto", "")
        
        if curva and categoria and produto:
            _aplicar_curva_no_dataframe(cliente, categoria, produto, curva)
            count += 1
    
    if count > 0:
        print(f"[PERSIST] Aplicadas {count} curvas salvas no DataFrame")
    
    return count


# ============================================================================
# SIMULAÇÕES - CRUD
# ============================================================================
def adicionar_simulacao(nome, categoria, produto, taxa_crescimento, 
                        volatilidade, cenarios, dados_grafico):
    """
    Adiciona uma nova simulação ao session_state.
    TAMBÉM persiste a curva ajustada e atualiza o DataFrame.
    """
    usuario = st.session_state.get("usuario", "anonimo")
    cliente = cenarios.get("Cliente", "Todos")
    curva_ajustada = dados_grafico.get("Ajustada", [0.0] * 12)
    
    simulacao = {
        "id": f"{usuario}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "nome": nome,
        "categoria": categoria,
        "produto": produto,
        "cliente": cliente,
        "taxa_crescimento": taxa_crescimento,
        "volatilidade": volatilidade,
        "cenarios": cenarios,
        "dados_grafico": dados_grafico,
        "ajustada": curva_ajustada,
        "data_criacao": datetime.now().isoformat(),
        "status": "Ativa"
    }
    
    # ============== NOVO: Persiste curva ajustada ==============
    salvar_curva_ajustada(cliente, categoria, produto, curva_ajustada, nome)
    print(f"[SIMULAÇÃO] Salva: {nome} | {cliente}/{categoria}/{produto}")
    
    # Adiciona à lista do usuário
    if usuario not in st.session_state.simulacoes_salvas:
        st.session_state.simulacoes_salvas[usuario] = []
    
    # Verifica se já existe simulação com mesmo nome para mesma combo
    combo_key = f"{categoria}::{produto}::{cliente}"
    existente = None
    for i, sim in enumerate(st.session_state.simulacoes_salvas[usuario]):
        sim_combo = f"{sim.get('categoria')}::{sim.get('produto')}::{sim.get('cliente', 'Todos')}"
        if sim.get("nome") == nome and sim_combo == combo_key:
            existente = i
            break
    
    if existente is not None:
        # Atualiza simulação existente
        st.session_state.simulacoes_salvas[usuario][existente] = simulacao
    else:
        # Adiciona nova
        st.session_state.simulacoes_salvas[usuario].append(simulacao)
    
    # Mantém compatibilidade com lista antiga
    st.session_state.simulacoes.append(simulacao)
    
    return simulacao


def get_simulacoes_usuario(usuario=None):
    """Retorna todas as simulações do usuário"""
    if usuario is None:
        usuario = st.session_state.get("usuario", "anonimo")
    return st.session_state.simulacoes_salvas.get(usuario, [])


def get_simulacao_por_combo(categoria, produto, cliente="Todos"):
    """Busca simulação salva para uma combinação específica"""
    usuario = st.session_state.get("usuario", "anonimo")
    simulacoes = st.session_state.simulacoes_salvas.get(usuario, [])
    
    for sim in reversed(simulacoes):  # Mais recente primeiro
        if (sim.get("categoria") == categoria and 
            sim.get("produto") == produto and
            sim.get("cliente", "Todos") == cliente):
            return sim
    return None


def restaurar_simulacao(simulacao_id):
    """
    Restaura uma simulação salva para o estado atual.
    Também carrega a curva persistida e aplica no DataFrame.
    """
    usuario = st.session_state.get("usuario", "anonimo")
    simulacoes = st.session_state.simulacoes_salvas.get(usuario, [])
    
    for sim in simulacoes:
        if sim.get("id") == simulacao_id:
            cliente = sim.get("cliente", "Todos")
            categoria = sim.get("categoria", "")
            produto = sim.get("produto", "")
            curva = sim.get("ajustada", [0.0] * 12)
            
            # Restaura os dados no session_state
            st.session_state["ajustada"] = curva[:]
            st.session_state["filtros"] = {
                "cliente": cliente,
                "categoria": categoria,
                "produto": produto,
                "nome": sim.get("nome", "")
            }
            
            # Aplica a curva no DataFrame
            _aplicar_curva_no_dataframe(cliente, categoria, produto, curva)
            
            print(f"[RESTAURAR] Simulação restaurada: {sim.get('nome')}")
            return sim
    return None


def deletar_simulacao(simulacao_id):
    """Deleta uma simulação por ID"""
    usuario = st.session_state.get("usuario", "anonimo")
    if usuario in st.session_state.simulacoes_salvas:
        st.session_state.simulacoes_salvas[usuario] = [
            s for s in st.session_state.simulacoes_salvas[usuario] 
            if s.get("id") != simulacao_id
        ]
    # Compatibilidade
    st.session_state.simulacoes = [
        s for s in st.session_state.simulacoes 
        if s.get("id") != simulacao_id
    ]


def get_simulacoes():
    """Retorna todas as simulações (compatibilidade)"""
    return st.session_state.simulacoes


# ============================================================================
# AJUSTES POR CATEGORIA (para propagar alterações do drag-and-drop)
# ============================================================================
def set_ajuste_categoria(categoria, valores):
    """Salva ajuste temporário para uma categoria"""
    st.session_state.ajustes_categoria[categoria] = valores


def get_ajuste_categoria(categoria):
    """Recupera ajuste temporário de uma categoria"""
    return st.session_state.ajustes_categoria.get(categoria, None)


def limpar_ajustes_categoria():
    """Limpa todos os ajustes temporários"""
    st.session_state.ajustes_categoria = {}


# ============================================================================
# MÉTRICAS DO DASHBOARD
# ============================================================================
def atualizar_metricas_dashboard():
    """Atualiza métricas do dashboard baseado nos dados do upload"""
    if st.session_state.dados_upload is not None:
        df = st.session_state.dados_upload
        
        st.session_state.metricas_dashboard = {
            "valor_total": float(df['PROJETADO_AJUSTADO'].sum()) 
                if 'PROJETADO_AJUSTADO' in df.columns else 0,
            "realizado_atual": float(df['CURVA_REALIZADO'].sum()) 
                if 'CURVA_REALIZADO' in df.columns else 0,
            "taxa_acuracia": calcular_acuracia(df),
            "simulacoes_ativas": len(get_simulacoes_usuario())
        }


def calcular_acuracia(df):
    """Calcula taxa de acurácia entre realizado e projetado"""
    if 'CURVA_REALIZADO' in df.columns and 'PROJETADO_ANALITICO' in df.columns:
        realizado = df['CURVA_REALIZADO'].sum()
        projetado = df['PROJETADO_ANALITICO'].sum()
        if projetado > 0:
            acuracia = (realizado / projetado) * 100
            return min(100, max(0, acuracia))
    return 0


def get_metricas_dashboard():
    """Retorna as métricas do dashboard"""
    return st.session_state.metricas_dashboard


# ============================================================================
# PERSISTÊNCIA (simulada via session_state - em produção usaria DB)
# ============================================================================
def exportar_simulacoes_json():
    """Exporta todas as simulações do usuário para JSON"""
    usuario = st.session_state.get("usuario", "anonimo")
    dados = st.session_state.simulacoes_salvas.get(usuario, [])
    return json.dumps(dados, default=str, indent=2)


def importar_simulacoes_json(json_str):
    """Importa simulações de um JSON"""
    usuario = st.session_state.get("usuario", "anonimo")
    try:
        dados = json.loads(json_str)
        if isinstance(dados, list):
            st.session_state.simulacoes_salvas[usuario] = dados
            return True
    except Exception:
        pass
    return False


# ============================================================================
# GERAR DADOS DE EXEMPLO
# ============================================================================
def gerar_dados_exemplo():
    """Gera dados de exemplo para demonstração"""
    import numpy as np
    
    datas = pd.date_range('2025-01-01', periods=12, freq='MS')
    categorias = ['Credito PF', 'Credito PJ', 'Investimentos']
    produtos = ['Credito Pessoal', 'Emprestimo', 'Fundo de Investimento']
    
    dados = []
    for data in datas:
        for cat_idx, categoria in enumerate(categorias):
            for prod_idx, produto in enumerate(produtos):
                realizado = np.random.uniform(200000, 800000)
                projetado = realizado * np.random.uniform(1.0, 1.3)
                
                dados.append({
                    'DATA_COMPLETA': data.strftime('%d/%m/%Y'),
                    'MES': data.strftime('%B').lower(),
                    'ANO': data.year,
                    'COD_CATEGORIA': f'CAT{cat_idx:02d}',
                    'CATEGORIA': categoria,
                    'COD_PRODUTO': f'PRD{prod_idx:02d}',
                    'PRODUTO': produto,
                    'CURVA_REALIZADO': realizado,
                    'PROJETADO_ANALITICO': projetado,
                    'PROJETADO_MERCADO': projetado * 0.95,
                    'PROJETADO_AJUSTADO': projetado * 0.98
                })
    
    return pd.DataFrame(dados)


# Inicializar ao importar
init_data_state()
