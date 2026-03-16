"""
Schema Manager - Gerencia estrutura de dados persistente em JSON
Converte uploads XLSX em estrutura JSON organizada
Sincroniza dados entre frontend e backend
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import unicodedata

# Diretórios
BASE_DIR = Path(__file__).parent / "database"
DADOS_DIR = BASE_DIR / "dados"
DADOS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# UTILIDADES
# ============================================================================
def _normalizar_texto(texto: str) -> str:
    """Normaliza texto para comparação (remove acentos, minúsculas)"""
    if texto is None:
        return ""
    texto = str(texto).strip().lower()
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                  if unicodedata.category(c) != 'Mn')


def _gerar_combo_key(cliente: str, categoria: str, produto: str) -> str:
    """Gera chave única para combinação"""
    return f"{cliente or 'Todos'}::{categoria}::{produto}"


# ============================================================================
# PARSE EXCEL → JSON ESTRUTURADO
# ============================================================================
def parse_excel_to_json(df: pd.DataFrame, usuario_id: str) -> Dict:
    """
    Converte DataFrame do upload em estrutura JSON hierárquica.
    
    Estrutura esperada do Excel:
    - TIPO_CLIENTE: Cliente
    - CATEGORIA: Categoria
    - PRODUTO: Produto
    - MES: Mês (1-12 ou nome)
    - ANO: Ano
    - PROJETADO_ANALITICO: Valor analítico
    - PROJETADO_MERCADO: Valor mercado
    - PROJETADO_AJUSTADO: Valor ajustado
    
    Returns:
        Dicionário estruturado com todos os dados
    """
    if df is None or df.empty:
        return _criar_schema_vazio(usuario_id)
    
    schema = {
        "metadata": {
            "usuario_id": usuario_id,
            "data_ultima_atualizacao": datetime.now().isoformat(),
            "versao_schema": "1.0",
            "total_linhas_origem": len(df)
        },
        "produtos": {}
    }
    
    # Normalizar nomes de colunas
    df.columns = [col.upper().strip() for col in df.columns]
    
    # Iterar pelas linhas
    for idx, row in df.iterrows():
        try:
            cliente = str(row.get("TIPO_CLIENTE", "Todos")).strip()
            categoria = str(row.get("CATEGORIA", "")).strip()
            produto = str(row.get("PRODUTO", "")).strip()
            
            if not categoria or not produto:
                continue
            
            # Chave do produto
            combo_key = _gerar_combo_key(cliente, categoria, produto)
            
            # Criar entrada se não existe
            if combo_key not in schema["produtos"]:
                schema["produtos"][combo_key] = {
                    "dados_base": {
                        "cliente": cliente,
                        "categoria": categoria,
                        "produto": produto,
                        "cod_bloco": str(row.get("COD_BLOCO", "")),
                        "cod_produto": str(row.get("COD_PRODUTO", "")),
                        "cod_categoria": str(row.get("COD_CATEGORIA", ""))
                    },
                    "projecoes": {},
                    "simulacoes": []
                }
            
            # Extrair mês e ano
            mes = int(row.get("MES_NUM", row.get("MES", 0))) if row.get("MES_NUM") or row.get("MES") else 0
            if mes < 1 or mes > 12:
                continue
            
            ano = int(row.get("ANO", 0)) if row.get("ANO") else 0
            if ano < 2000:
                continue
            
            ano_str = str(ano)
            
            # Criar estrutura do ano se não existe
            if ano_str not in schema["produtos"][combo_key]["projecoes"]:
                schema["produtos"][combo_key]["projecoes"][ano_str] = {
                    "meses": [0] * 12,
                    "analitica": [0.0] * 12,
                    "mercado": [0.0] * 12,
                    "ajustada": [0.0] * 12
                }
            
            # Preencher dados
            proj = schema["produtos"][combo_key]["projecoes"][ano_str]
            idx_mes = mes - 1
            
            proj["meses"][idx_mes] = mes
            proj["analitica"][idx_mes] = float(row.get("PROJETADO_ANALITICO", 0) or 0)
            proj["mercado"][idx_mes] = float(row.get("PROJETADO_MERCADO", 0) or 0)
            proj["ajustada"][idx_mes] = float(row.get("PROJETADO_AJUSTADO", 0) or 0)
            
        except Exception as e:
            print(f"[SCHEMA] Erro ao processar linha {idx}: {e}")
            continue
    
    return schema


def _criar_schema_vazio(usuario_id: str) -> Dict:
    """Cria um schema vazio"""
    return {
        "metadata": {
            "usuario_id": usuario_id,
            "data_ultima_atualizacao": datetime.now().isoformat(),
            "versao_schema": "1.0",
            "total_linhas_origem": 0
        },
        "produtos": {}
    }


# ============================================================================
# PERSISTÊNCIA
# ============================================================================
def salvar_dados_usuario(usuario_id: str, schema: Dict) -> Tuple[bool, str]:
    """
    Salva a estrutura de dados do usuário em JSON.
    
    Args:
        usuario_id: ID do usuário
        schema: Dicionário com estrutura de dados
        
    Returns:
        (sucesso, mensagem)
    """
    try:
        arquivo = DADOS_DIR / f"{usuario_id}_dados.json"
        
        # Atualizar timestamp
        schema["metadata"]["data_ultima_atualizacao"] = datetime.now().isoformat()
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
        total_produtos = len(schema.get("produtos", {}))
        print(f"[SCHEMA] Dados salvos: {arquivo} ({total_produtos} produtos)")
        return True, f"Dados salvos com sucesso ({total_produtos} produtos)"
        
    except Exception as e:
        msg = f"Erro ao salvar dados: {str(e)}"
        print(f"[SCHEMA] {msg}")
        return False, msg


def carregar_dados_usuario(usuario_id: str) -> Optional[Dict]:
    """
    Carrega a estrutura de dados do usuário.
    
    Returns:
        Dicionário com dados ou None
    """
    try:
        arquivo = DADOS_DIR / f"{usuario_id}_dados.json"
        
        if arquivo.exists():
            with open(arquivo, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            print(f"[SCHEMA] Dados carregados: {len(schema.get('produtos', {}))} produtos")
            return schema
        
        return None
        
    except Exception as e:
        print(f"[SCHEMA] Erro ao carregar dados: {e}")
        return None


# ============================================================================
# QUERIES (Interface simplificada para acessar dados)
# ============================================================================
def get_produto_projection(usuario_id: str, cliente: str, categoria: str, 
                           produto: str, ano: int) -> Optional[Dict]:
    """
    Retorna a projeção de um produto para um ano específico.
    
    Returns:
        {
            "meses": [1, 2, ..., 12],
            "analitica": [100, 110, ...],
            "mercado": [95, 105, ...],
            "ajustada": [100, 110, ...]
        }
        ou None se não encontrado
    """
    schema = carregar_dados_usuario(usuario_id)
    if not schema:
        return None
    
    combo_key = _gerar_combo_key(cliente, categoria, produto)
    produto_data = schema["produtos"].get(combo_key)
    
    if not produto_data:
        return None
    
    anos = produto_data.get("projecoes", {})
    return anos.get(str(ano))


def get_curva_ajustada(usuario_id: str, cliente: str, categoria: str, 
                       produto: str, ano: int) -> Optional[List[float]]:
    """
    Retorna apenas a curva ajustada (12 valores) para um produto/ano.
    
    Returns:
        Lista [v1, v2, ..., v12] ou None
    """
    proj = get_produto_projection(usuario_id, cliente, categoria, produto, ano)
    if proj:
        return proj.get("ajustada")
    return None


def atualizar_curva_ajustada(usuario_id: str, cliente: str, categoria: str, 
                             produto: str, ano: int, curva_ajustada: List[float]) -> Tuple[bool, str]:
    """
    Atualiza a curva ajustada de um produto.
    
    Args:
        usuario_id: ID do usuário
        cliente: Cliente
        categoria: Categoria
        produto: Produto
        ano: Ano da projeção
        curva_ajustada: Lista com 12 valores
        
    Returns:
        (sucesso, mensagem)
    """
    try:
        schema = carregar_dados_usuario(usuario_id)
        if not schema:
            return False, "Dados do usuário não encontrados"
        
        combo_key = _gerar_combo_key(cliente, categoria, produto)
        
        if combo_key not in schema["produtos"]:
            return False, f"Produto não encontrado: {combo_key}"
        
        if str(ano) not in schema["produtos"][combo_key]["projecoes"]:
            return False, f"Ano {ano} não encontrado para este produto"
        
        # Normalizar curva (garantir 12 elementos)
        curva_normalizada = (list(curva_ajustada) + [0.0] * 12)[:12]
        
        # Atualizar
        schema["produtos"][combo_key]["projecoes"][str(ano)]["ajustada"] = curva_normalizada
        
        # Salvar
        sucesso, msg = salvar_dados_usuario(usuario_id, schema)
        if sucesso:
            msg = f"Curva atualizada com sucesso para {combo_key} (ano {ano})"
        
        return sucesso, msg
        
    except Exception as e:
        msg = f"Erro ao atualizar curva: {str(e)}"
        print(f"[SCHEMA] {msg}")
        return False, msg


def listar_produtos(usuario_id: str) -> List[Dict]:
    """
    Retorna lista de todos os produtos cadastrados.
    
    Returns:
        Lista de dicionários com dados dos produtos
    """
    schema = carregar_dados_usuario(usuario_id)
    if not schema:
        return []
    
    produtos = []
    for combo_key, dados in schema["produtos"].items():
        produtos.append({
            "combo_key": combo_key,
            "cliente": dados["dados_base"]["cliente"],
            "categoria": dados["dados_base"]["categoria"],
            "produto": dados["dados_base"]["produto"],
            "anos_disponiveis": list(dados["projecoes"].keys()),
            "total_simulacoes": len(dados.get("simulacoes", []))
        })
    
    return produtos
