"""
Data Manager - Gerencia dados compartilhados entre páginas
Armazena dados do upload, simulações e curvas ajustadas persistentes
Sincroniza automaticamente com o banco de dados backend
"""

import pandas as pd
import streamlit as st
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import sys

# Importar schema do backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
try:
    from database_schema import (
        carregar_dados_usuario, 
        get_curva_ajustada, 
        atualizar_curva_ajustada,
        listar_produtos,
        get_produto_projection
    )
except ImportError:
    print("[DATA_MANAGER] ⚠️  database_schema não disponível ainda")


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
    if "schema_backend" not in st.session_state:
        # Cache do schema carregado do backend
        st.session_state.schema_backend = None
    if "usuario_id" not in st.session_state:
        # ID do usuário logado (usado para sincronizar com backend)
        st.session_state.usuario_id = "usr_anonimo"


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
    """
    Recupera dados do upload (com curvas ajustadas aplicadas).
    Se não houver dados em session_state, tenta carregar da base compartilhada.
    """
    # Se tem dados em session_state, retorna
    if st.session_state.dados_upload is not None and not st.session_state.dados_upload.empty:
        df_cache = st.session_state.dados_upload
        if "CD_CPNT_RSTD" in df_cache.columns or "TIP_TD" in df_cache.columns:
            return df_cache
    
    # Senão, tenta carregar da base compartilhada
    df_compartilhada = carregar_base_dados_compartilhada()
    if df_compartilhada is not None and not df_compartilhada.empty:
        # Cache no session_state
        st.session_state.dados_upload = df_compartilhada
        st.session_state.dados_upload_original = df_compartilhada.copy()
        return df_compartilhada
    
    return None


def get_dados_upload_original():
    """Recupera dados originais do upload (sem ajustes)"""
    return st.session_state.dados_upload_original


# ============================================================================
# PERSISTÊNCIA DE CURVAS AJUSTADAS
# ============================================================================
def _gerar_combo_key(
    cliente: str,
    categoria: str,
    produto: str,
    cd_tip_agpd: str = "Todos",
    tip_td: str = "Todos",
) -> str:
    """Gera chave única para combinação de 5 dimensões."""
    return (
        f"{cliente or 'Todos'}::{categoria}::{produto}::"
        f"{cd_tip_agpd or 'Todos'}::{tip_td or 'Todos'}"
    )


def salvar_curva_ajustada(
    cliente: str,
    categoria: str,
    produto: str,
    curva: List[float],
    nome_simulacao: str = "",
    cd_tip_agpd: str = "Todos",
    tip_td: str = "Todos",
) -> bool:
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
    combo_key = _gerar_combo_key(cliente, categoria, produto, cd_tip_agpd, tip_td)
    
    # Garante que curva tem 12 elementos
    curva_normalizada = (list(curva) + [0.0] * 12)[:12]
    
    # Salva no dicionário de curvas persistentes
    st.session_state.curvas_ajustadas_persistentes[combo_key] = {
        "curva": curva_normalizada,
        "data_salvo": datetime.now().isoformat(),
        "nome": nome_simulacao,
        "cliente": cliente,
        "categoria": categoria,
        "produto": produto,
        "cd_tip_agpd": cd_tip_agpd,
        "tip_td": tip_td,
    }
    
    # Adiciona ao histórico
    entrada_historico = {
        "id": f"{combo_key}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "combo_key": combo_key,
        "cliente": cliente,
        "categoria": categoria,
        "produto": produto,
        "cd_tip_agpd": cd_tip_agpd,
        "tip_td": tip_td,
        "curva": curva_normalizada,
        "nome": nome_simulacao,
        "data_criacao": datetime.now().isoformat(),
        "usuario": st.session_state.get("usuario", "anonimo")
    }
    st.session_state.historico_simulacoes.append(entrada_historico)
    
    # Aplica a curva ajustada no DataFrame principal
    _aplicar_curva_no_dataframe(
        cliente,
        categoria,
        produto,
        curva_normalizada,
        cd_tip_agpd=cd_tip_agpd,
        tip_td=tip_td,
    )
    
    # Atualiza métricas
    atualizar_metricas_dashboard()
    
    print(f"[PERSIST] Curva salva: {combo_key} = {curva_normalizada[:3]}...")
    return True


def carregar_curva_ajustada(
    cliente: str,
    categoria: str,
    produto: str,
    cd_tip_agpd: str = "Todos",
    tip_td: str = "Todos",
) -> Optional[List[float]]:
    """
    Carrega a curva ajustada salva para uma combinação específica.
    
    Returns:
        Lista com 12 valores ou None se não existir
    """
    combo_key = _gerar_combo_key(cliente, categoria, produto, cd_tip_agpd, tip_td)
    dados = st.session_state.curvas_ajustadas_persistentes.get(combo_key)
    
    if dados and "curva" in dados:
        print(f"[PERSIST] Curva carregada: {combo_key}")
        return dados["curva"]
    
    return None


def existe_curva_salva(
    cliente: str,
    categoria: str,
    produto: str,
    cd_tip_agpd: str = "Todos",
    tip_td: str = "Todos",
) -> bool:
    """Verifica se existe curva salva para a combinação"""
    combo_key = _gerar_combo_key(cliente, categoria, produto, cd_tip_agpd, tip_td)
    return combo_key in st.session_state.curvas_ajustadas_persistentes


def listar_curvas_salvas() -> Dict[str, dict]:
    """Retorna todas as curvas salvas"""
    return st.session_state.curvas_ajustadas_persistentes.copy()


def get_historico_simulacoes() -> List[dict]:
    """Retorna histórico completo de simulações"""
    return st.session_state.historico_simulacoes.copy()


def _aplicar_curva_no_dataframe(
    cliente: str,
    categoria: str,
    produto: str,
    curva: List[float],
    cd_tip_agpd: str = "Todos",
    tip_td: str = "Todos",
) -> None:
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

    if "CD_TIP_AGPD" in df.columns and cd_tip_agpd and cd_tip_agpd != "Todos":
        mask = mask & (df["CD_TIP_AGPD"].astype(str).apply(_norm) == _norm(cd_tip_agpd))
    if "TIP_TD" in df.columns and tip_td and tip_td != "Todos":
        mask = mask & (df["TIP_TD"].astype(str).apply(_norm) == _norm(tip_td))
    
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
    IMPORTANTE: Salva um SNAPSHOT COMPLETO de todas as curvas ajustadas.
    Agora também salva Data, Hora e Usuário.
    """
    usuario = st.session_state.get("usuario", "anonimo")
    cliente = cenarios.get("Cliente", "Todos")
    cd_tip_agpd = cenarios.get("CD_TIP_AGPD", "Todos")
    tip_td = cenarios.get("TIP_TD", "Todos")
    curva_ajustada = dados_grafico.get("Ajustada", [0.0] * 12)
    
    # Primeiro persiste a curva atual
    salvar_curva_ajustada(
        cliente,
        categoria,
        produto,
        curva_ajustada,
        nome,
        cd_tip_agpd=cd_tip_agpd,
        tip_td=tip_td,
    )
    
    # SNAPSHOT COMPLETO: Copia todas as curvas persistentes neste momento
    # Isso permite restaurar o estado COMPLETO de todas as curvas
    import copy
    snapshot_curvas = copy.deepcopy(st.session_state.curvas_ajustadas_persistentes)
    
    # Data e hora da simulação
    dt_agora = datetime.now()
    data_str = dt_agora.strftime("%d/%m/%Y")  # Formato brasileiro
    hora_str = dt_agora.strftime("%H:%M:%S")
    
    simulacao = {
        "id": f"{usuario}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "nome": nome,
        "categoria": categoria,
        "produto": produto,
        "cliente": cliente,
        "cd_tip_agpd": cd_tip_agpd,
        "tip_td": tip_td,
        "taxa_crescimento": taxa_crescimento,
        "volatilidade": volatilidade,
        "cenarios": cenarios,
        "dados_grafico": dados_grafico,
        "ajustada": curva_ajustada,
        "snapshot_curvas": snapshot_curvas,  # SNAPSHOT de TODAS as curvas
        "data_criacao": datetime.now().isoformat(),
        "data_salvo": data_str,  # Data formatada (DD/MM/YYYY)
        "hora_salvo": hora_str,  # Hora formatada (HH:MM:SS)
        "usuario": usuario,  # Nome do usuário que salvou
        "status": "Ativa"
    }
    
    print(f"[SIMULAÇÃO] Salva: {nome} | {cliente}/{categoria}/{produto} | Usuário: {usuario} | Data: {data_str} {hora_str} | Snapshot com {len(snapshot_curvas)} curvas")
    
    # Adiciona à lista do usuário (SEMPRE cria uma nova versão, não atualiza)
    if usuario not in st.session_state.simulacoes_salvas:
        st.session_state.simulacoes_salvas[usuario] = []
    
    # SEMPRE adiciona como nova simulação ao histórico (permite múltiplas versões)
    st.session_state.simulacoes_salvas[usuario].append(simulacao)
    
    # Mantém compatibilidade com lista antiga
    st.session_state.simulacoes.append(simulacao)
    
    return simulacao


def get_simulacoes_usuario(usuario=None):
    """
    Retorna todas as simulações do usuário com dados normalizados.
    Automaticamente adiciona data_salvo, hora_salvo, usuario e número de versão para simulações antigas.
    Retorna em ordem DECRESCENTE (mais recentes primeiro).
    """
    if usuario is None:
        usuario = st.session_state.get("usuario", "anonimo")
    
    simulacoes = st.session_state.simulacoes_salvas.get(usuario, [])
    
    # Normaliza simulações antigas para ter sempre os campos de data/hora/usuario
    simulacoes_normalizadas = []
    for sim in simulacoes:
        sim_copia = sim.copy()
        
        # Se não tem data_salvo, tenta extrair de data_criacao
        if "data_salvo" not in sim_copia:
            if "data_criacao" in sim_copia:
                try:
                    dt = datetime.fromisoformat(sim_copia["data_criacao"])
                    sim_copia["data_salvo"] = dt.strftime("%d/%m/%Y")
                    sim_copia["hora_salvo"] = dt.strftime("%H:%M:%S")
                except:
                    sim_copia["data_salvo"] = "-"
                    sim_copia["hora_salvo"] = "-"
            else:
                sim_copia["data_salvo"] = "-"
                sim_copia["hora_salvo"] = "-"
        
        # Se não tem usuario, adiciona padrão
        if "usuario" not in sim_copia:
            sim_copia["usuario"] = "anonimo"
        
        simulacoes_normalizadas.append(sim_copia)
    
    # Retorna em ordem DECRESCENTE (mais recentes primeiro)
    return list(reversed(simulacoes_normalizadas))


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
    RESTAURA O SNAPSHOT COMPLETO de todas as curvas ajustadas.
    Isso garante que ao restaurar, TODAS as curvas voltam ao estado daquela simulação.
    """
    import copy
    usuario = st.session_state.get("usuario", "anonimo")
    simulacoes = st.session_state.simulacoes_salvas.get(usuario, [])
    
    for sim in simulacoes:
        if sim.get("id") == simulacao_id:
            cliente = sim.get("cliente", "Todos")
            categoria = sim.get("categoria", "")
            produto = sim.get("produto", "")
            curva = sim.get("ajustada", [0.0] * 12)
            nome = sim.get("nome", "Simulação Restaurada")
            
            # ============== RESTAURAR SNAPSHOT COMPLETO ==============
            # Se existe snapshot, restaura TODAS as curvas daquele momento
            snapshot = sim.get("snapshot_curvas")
            if snapshot:
                # Substitui TODO o dicionário de curvas pelo snapshot
                st.session_state.curvas_ajustadas_persistentes = copy.deepcopy(snapshot)
                print(f"[RESTAURAR] Snapshot restaurado com {len(snapshot)} curvas")
                
                # Aplica cada curva do snapshot no DataFrame
                for combo_key, dados in snapshot.items():
                    curva_snap = dados.get("curva", [])
                    cli = dados.get("cliente", "Todos")
                    cat = dados.get("categoria", "")
                    prd = dados.get("produto", "")
                    if curva_snap and len(curva_snap) == 12:
                        _aplicar_curva_no_dataframe(cli, cat, prd, curva_snap)
            else:
                # Fallback: só restaura a curva do produto específico (simulações antigas)
                salvar_curva_ajustada(cliente, categoria, produto, curva, nome)
                _aplicar_curva_no_dataframe(cliente, categoria, produto, curva)
            
            # Restaura os dados no session_state
            st.session_state["ajustada"] = curva[:]
            st.session_state["filtros"] = {
                "cliente": cliente,
                "categoria": categoria,
                "produto": produto,
                "nome": nome
            }
            
            # Reseta o sync_counter para evitar que localStorage sobrescreva a curva restaurada
            st.session_state["sync_counter"] = 0
            
            # Força limpeza do localStorage e detecção de combo mudou
            st.session_state["_limpar_localStorage"] = True
            st.session_state["last_combo"] = None
            
            print(f"[RESTAURAR] Simulação restaurada: {nome}")
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


# ============================================================================
# INTEGRAÇÃO COM MOCK DATABASE (PERSISTÊNCIA EM ARQUIVOS)
# ============================================================================
def carregar_base_dados_compartilhada():
    """
    Carrega a base de dados do usuário com isolamento garantido.
    
    Fluxo:
    1. Se usuário tem base editada → carrega sua cópia
    2. Se não tem → carrega base compartilhada
    
    Isso garante que cada usuário veja sua própria versão da base
    se já tiver feito edições.
    
    Returns:
        DataFrame com dados da base ou None
    """
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
        from database import carregar_base_usuario
        
        usuario_id = st.session_state.get("usuario_id", "")
        
        # Se não há usuário autenticado, carrega base compartilhada
        if not usuario_id:
            from database import carregar_base_dados_compartilhada as db_carregar_compartilhada
            df = db_carregar_compartilhada()
        else:
            # Carrega base específica do usuário (isolada com suas edições)
            df = carregar_base_usuario(usuario_id)
        
        if df is not None:
            # Garante coluna PROJETADO_AJUSTADO existe
            if "PROJETADO_AJUSTADO" not in df.columns:
                if "PROJETADO_ANALITICO" in df.columns:
                    df["PROJETADO_AJUSTADO"] = df["PROJETADO_ANALITICO"].copy()
                else:
                    df["PROJETADO_AJUSTADO"] = 0.0
            return df
        return None
    except Exception as e:
        print(f"[DATA_MANAGER] Erro ao carregar base: {e}")
        return None


def salvar_upload_admin(arquivo_bytes: bytes, nome_arquivo: str, usuario_id: str = None) -> Tuple[bool, str]:
    """
    Salva um arquivo de upload do admin na base de dados compartilhada.
    Quando admin faz upload, INVALIDA as bases personalizadas dos usuários
    (para que elas sejam recriadas a partir da nova base compartilhada).
    
    Args:
        arquivo_bytes: Bytes do arquivo Excel
        nome_arquivo: Nome do arquivo original
        usuario_id: ID do usuário (opcional, obtém de session_state se não fornecido)
        
    Returns:
        (sucesso, mensagem)
    """
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
        from database import salvar_upload_admin as db_salvar, eh_admin, obter_usuario_por_email
        
        usuario_email = st.session_state.get("usuario_email", "")
        if usuario_id is None:
            usuario_id = st.session_state.get("usuario_id", "")
        
        if not usuario_email or not usuario_id:
            return False, "Usuário não autenticado"
        
        # Valida se é admin via database
        usuario = obter_usuario_por_email(usuario_email)
        if not usuario or not eh_admin(usuario):
            return False, "Apenas administradores podem fazer upload"
        
        # Salva no database
        try:
            sucesso, msg = db_salvar(arquivo_bytes, nome_arquivo, usuario_id)
            
            if sucesso:
                # Invalida cache do session_state
                st.session_state.dados_upload = None
                st.session_state.dados_upload_original = None
                st.session_state._curvas_aplicadas_sessao = False
                
                # NOVO: Flag para invalidar bases personalizadas dos usuarios
                # Proximo login recarregara e criara nova base se tiver edicoes
                st.session_state._novo_upload_realizado = True
                
                print(f"[DATA_MANAGER] Upload salvo. Cache invalidado.")
            
            return sucesso, msg
        
        except Exception as e_db:
            print(f"[DATA_MANAGER] Erro ao chamar backend: {e_db}")
            import traceback
            traceback.print_exc()
            # Retorna erro claro
            return False, f"Erro ao conectar com backend: {str(e_db)}"
        
    except Exception as e:
        return False, f"Erro ao salvar upload: {str(e)}"


def eh_usuario_admin() -> bool:
    """Verifica se o usuário autenticado é um admin"""
    try:
        return st.session_state.get("usuario_role") == "admin"
    except:
        return False


def sincronizar_curva_com_arquivo(cliente: str, categoria: str, 
                                  produto: str, curva: List[float]) -> bool:
    """
    Sincroniza uma curva ajustada com o arquivo de simulações do usuário.
    Salva em: backend/database/simulacoes/{usuario_id}_simulacoes.json
    
    Args:
        cliente: Nome do cliente
        categoria: Categoria do produto
        produto: Nome do produto
        curva: Lista com 12 valores
        
    Returns:
        True se sincronizado com sucesso
    """
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
        from database import salvar_curva_usuario
        
        usuario_id = st.session_state.get("usuario_id", "")
        usuario_nome = st.session_state.get("usuario_nome", "")
        
        if not usuario_id:
            print("[DATA_MANAGER] Usuário não autenticado, não sincronizando")
            return False
        
        # Salva no arquivo
        sucesso, msg = salvar_curva_usuario(
            usuario_id=usuario_id,
            cliente=cliente or "Todos",
            categoria=categoria,
            produto=produto,
            curva=curva
        )
        
        if sucesso:
            print(f"[DATA_MANAGER] Curva sincronizada com arquivo: {usuario_nome}/{categoria}/{produto}")
        
        return sucesso
        
    except Exception as e:
        print(f"[DATA_MANAGER] Erro ao sincronizar curva: {e}")
        return False


def carregar_curvas_usuario_do_arquivo() -> Dict[str, List[float]]:
    """
    Carrega todas as curvas salvas do usuário atual do arquivo.
    
    Returns:
        Dicionário {combo_key: lista_com_12_valores}
    """
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
        from database import carregar_curvas_usuario
        
        usuario_id = st.session_state.get("usuario_id", "")
        
        if not usuario_id:
            return {}
        
        simulacoes = carregar_curvas_usuario(usuario_id)
        
        # Converte para dicionário de combo_key -> curva
        resultado = {}
        for sim in simulacoes:
            combo_key = sim.get("combo_key")
            curva = sim.get("curva")
            if combo_key and curva:
                resultado[combo_key] = curva
        
        return resultado
        
    except Exception as e:
        print(f"[DATA_MANAGER] Erro ao carregar curvas do arquivo: {e}")
        return {}


def restaurar_curvas_de_arquivo() -> int:
    """
    Restaura todas as curvas do usuário do arquivo para o session_state.
    Útil ao fazer login ou recarregar a página.
    
    Returns:
        Quantidade de curvas restauradas
    """
    try:
        curvas_arquivo = carregar_curvas_usuario_do_arquivo()
        
        if not curvas_arquivo:
            return 0
        
        for combo_key, curva in curvas_arquivo.items():
            # Reconstitui os dados
            partes = combo_key.split("::")
            if len(partes) >= 3:
                cliente, categoria, produto = partes[0], partes[1], partes[2]
                
                # Salva no session_state (compatibilidade)
                salvar_curva_ajustada(cliente, categoria, produto, curva)
        
        print(f"[DATA_MANAGER] {len(curvas_arquivo)} curvas restauradas do arquivo")
        return len(curvas_arquivo)
        
    except Exception as e:
        print(f"[DATA_MANAGER] Erro ao restaurar curvas: {e}")
        return 0


# ============================================================================
# SINCRONIZAÇÃO COM BACKEND SCHEMA
# ============================================================================
def carregar_dados_do_backend(usuario_id: str) -> Optional[Dict]:
    """
    Carrega a estrutura de dados completa do usuário do backend.
    
    Returns:
        Dicionário com schema de dados ou None
    """
    try:
        schema = carregar_dados_usuario(usuario_id)
        if schema:
            print(f"[SYNC] Schema carregado do backend: {len(schema.get('produtos', {}))} produtos")
        return schema
    except Exception as e:
        print(f"[SYNC] Erro ao carregar schema do backend: {e}")
        return None


def sincronizar_curva_para_backend(usuario_id: str, cliente: str, categoria: str, 
                                   produto: str, ano: int, curva_ajustada: List[float]) -> bool:
    """
    Sincroniza uma curva ajustada para o backend.
    Atualiza o JSON no backend/database/dados/
    
    Args:
        usuario_id: ID do usuário
        cliente: Cliente
        categoria: Categoria
        produto: Produto
        ano: Ano da projeção
        curva_ajustada: Lista com 12 valores
        
    Returns:
        True se sincronizado com sucesso
    """
    try:
        sucesso, msg = atualizar_curva_ajustada(usuario_id, cliente, categoria, 
                                                 produto, ano, curva_ajustada)
        if sucesso:
            print(f"[SYNC] Curva sincronizada para backend: {cliente}::{categoria}::{produto}::{ano}")
        return sucesso
    except Exception as e:
        print(f"[SYNC] Erro ao sincronizar curva: {e}")
        return False


def obter_curva_do_backend(usuario_id: str, cliente: str, categoria: str, 
                           produto: str, ano: int) -> Optional[List[float]]:
    """
    Obtém uma curva ajustada do backend.
    
    Returns:
        Lista [v1, v2, ..., v12] ou None
    """
    try:
        curva = get_curva_ajustada(usuario_id, cliente, categoria, produto, ano)
        return curva
    except Exception as e:
        print(f"[SYNC] Erro ao obter curva do backend: {e}")
        return None


def listar_produtos_do_backend(usuario_id: str) -> List[Dict]:
    """
    Lista todos os produtos disponíveis para um usuário.
    
    Returns:
        Lista de produtos com metadados
    """
    try:
        produtos = listar_produtos(usuario_id)
        return produtos
    except Exception as e:
        print(f"[SYNC] Erro ao listar produtos: {e}")
        return []


def sincronizar_session_com_backend(usuario_id: str) -> bool:
    """
    Sincroniza o session_state completo com o schema do backend.
    Carrega os dados persistidos do usuário.
    
    Returns:
        True se sincronização bem sucedida
    """
    try:
        schema = carregar_dados_do_backend(usuario_id)
        if not schema:
            print(f"[SYNC] Nenhum dado encontrado no backend para {usuario_id}")
            return False
        
        # Armazenar schema no session_state para acesso rápido
        st.session_state.schema_backend = schema
        
        # Carregar curvas persistidas do backend
        for combo_key, produto_data in schema.get("produtos", {}).items():
            # Extrair dados da chave
            partes = combo_key.split("::")
            if len(partes) >= 3:
                cliente, categoria, produto = partes[0], partes[1], partes[2]
                
                # Buscar a projeção mais recente (ano maior)
                projecoes = produto_data.get("projecoes", {})
                if projecoes:
                    ano_maior = max(int(a) for a in projecoes.keys())
                    curva_ajustada = projecoes[str(ano_maior)].get("ajustada")
                    
                    if curva_ajustada and len(curva_ajustada) == 12:
                        # Restaurar no session_state
                        salvar_curva_ajustada(cliente, categoria, produto, 
                                            curva_ajustada, f"Backend {ano_maior}")
        
        print(f"[SYNC] Session sincronizado com backend para {usuario_id}")
        return True
        
    except Exception as e:
        print(f"[SYNC] Erro ao sincronizar session com backend: {e}")
        return False


# Inicializar ao importar
init_data_state()
