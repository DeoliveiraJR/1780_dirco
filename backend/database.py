"""
Mock Database Manager
Gerencia persistência de dados em arquivos para simular um banco de dados
- Usuários
- Uploads de arquivos (base de dados compartilhada)
- Simulações/curvas ajustadas por usuário
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from pathlib import Path

# Importar schema manager
from database_schema import parse_excel_to_json, salvar_dados_usuario, _criar_schema_vazio

# Caminhos das tabelas mockadas
BASE_DIR = Path(__file__).parent / "database"
USERS_FILE = BASE_DIR / "users.json"
UPLOADS_DIR = BASE_DIR / "uploads"
SIMULACOES_DIR = BASE_DIR / "simulacoes"
METADATA_DIR = BASE_DIR / "metadata"

# Criar diretórios se não existirem
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
SIMULACOES_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# GERENCIAMENTO DE USUÁRIOS
# ============================================================================

def carregar_usuarios() -> List[Dict]:
    """
    Carrega todos os usuários do arquivo mockado.
    
    Returns:
        Lista de dicionários com dados dos usuários
    """
    try:
        if USERS_FILE.exists():
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                usuarios = json.load(f)
                return usuarios if isinstance(usuarios, list) else []
        return []
    except Exception as e:
        print(f"[DB] Erro ao carregar usuários: {e}")
        return []


def validar_login(email: str, senha: str) -> Tuple[bool, Optional[Dict]]:
    """
    Valida credenciais de login.
    
    Args:
        email: Email do usuário
        senha: Senha fornecida
        
    Returns:
        (autenticado, dados_usuario)
    """
    usuarios = carregar_usuarios()
    
    for usuario in usuarios:
        if usuario.get("email") == email.lower() and usuario.get("senha") == senha:
            if usuario.get("ativo", True):
                return True, usuario
            else:
                return False, None
    
    return False, None


def obter_usuario_por_email(email: str) -> Optional[Dict]:
    """Obtém dados completos do usuário por email"""
    usuarios = carregar_usuarios()
    
    for usuario in usuarios:
        if usuario.get("email") == email.lower():
            return usuario
    
    return None


def obter_usuario_por_id(usuario_id: str) -> Optional[Dict]:
    """Obtém dados completos do usuário por ID"""
    usuarios = carregar_usuarios()
    
    for usuario in usuarios:
        if usuario.get("id") == usuario_id:
            return usuario
    
    return None


def eh_admin(usuario: Dict) -> bool:
    """Verifica se o usuário é admin"""
    return usuario.get("role") == "admin"


# ============================================================================
# GERENCIAMENTO DE UPLOADS (BASE DE DADOS COMPARTILHADA)
# ============================================================================

def salvar_upload_admin(arquivo_excel: bytes, nome_arquivo: str, usuario_id: str) -> Tuple[bool, str]:
    """
    Salva um arquivo de upload do admin na pasta de uploads.
    Também faz parse para JSON estruturado e sincroniza para todos os usuários.
    
    Args:
        arquivo_excel: Bytes do arquivo Excel
        nome_arquivo: Nome do arquivo original
        usuario_id: ID do usuário admin que está fazendo upload
        
    Returns:
        (sucesso, mensagem)
    """
    usuario = obter_usuario_por_id(usuario_id)
    
    if not usuario or not eh_admin(usuario):
        return False, "Apenas administradores podem fazer upload"
    
    try:
        # 1. Salva o arquivo XLSX original
        caminho_arquivo = UPLOADS_DIR / "base_dados_compartilhada.xlsx"
        
        with open(caminho_arquivo, 'wb') as f:
            f.write(arquivo_excel)
        
        # 2. Parse para DataFrame
        from io import BytesIO
        df = pd.read_excel(BytesIO(arquivo_excel))
        
        # 3. Salva metadados do upload
        metadata = {
            "arquivo_original": nome_arquivo,
            "arquivo_salvo": str(caminho_arquivo.relative_to(BASE_DIR.parent)),
            "usuario_id": usuario_id,
            "usuario_email": usuario.get("email"),
            "data_upload": datetime.now().isoformat(),
            "tamanho_bytes": len(arquivo_excel),
            "linhas": len(df),
            "colunas": list(df.columns)
        }
        
        metadata_file = METADATA_DIR / "ultimo_upload.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # 4. Parse para JSON estruturado (NOVO)
        print(f"[DB] Iniciando parse XLSX → JSON...")
        usuarios_sistema = carregar_usuarios()
        print(f"[DB] {len(usuarios_sistema)} usuários encontrados para sincronizar")
        
        for usr in usuarios_sistema:
            usr_id = usr.get("id")
            if usr_id:
                print(f"[DB] Parseando para usuário: {usr_id}")
                try:
                    schema = parse_excel_to_json(df, usr_id)
                    num_produtos = len(schema.get("produtos", {}))
                    print(f"[DB]   ✅ Schema criado: {num_produtos} produtos")
                    
                    sucesso, msg = salvar_dados_usuario(usr_id, schema)
                    if sucesso:
                        print(f"[DB]   ✅ Dados salvos com sucesso")
                    else:
                        print(f"[DB]   ❌ Erro ao salvar: {msg}")
                except Exception as parse_err:
                    print(f"[DB]   ❌ ERRO ao parsear para {usr_id}: {parse_err}")
                    import traceback
                    traceback.print_exc()
        
        print(f"[DB] Upload salvo e parseado: {caminho_arquivo}")
        return True, f"Arquivo '{nome_arquivo}' importado com sucesso!\n✅ Estrutura de dados atualizada para {len(usuarios_sistema)} usuários"
        
    except Exception as e:
        print(f"[DB] ❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Erro ao salvar upload: {str(e)}"


def carregar_base_dados_compartilhada() -> Optional[pd.DataFrame]:
    """
    Carrega o arquivo base de dados que é compartilhado entre todos os usuários.
    
    Returns:
        DataFrame com dados da base ou None se não existir
    """
    try:
        caminho_arquivo = UPLOADS_DIR / "base_dados_compartilhada.xlsx"
        
        if caminho_arquivo.exists():
            df = pd.read_excel(caminho_arquivo)
            print(f"[DB] Base de dados compartilhada carregada: {len(df)} linhas")
            return df
        
        print("[DB] Nenhuma base de dados compartilhada encontrada ainda")
        return None
        
    except Exception as e:
        print(f"[DB] Erro ao carregar base de dados compartilhada: {e}")
        return None


def obter_metadados_ultimo_upload() -> Optional[Dict]:
    """
    Obtém informações sobre o último upload realizado.
    
    Returns:
        Dicionário com metadados ou None
    """
    try:
        metadata_file = METADATA_DIR / "ultimo_upload.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
        
    except Exception as e:
        print(f"[DB] Erro ao carregar metadados: {e}")
        return None


# ============================================================================
# GERENCIAMENTO DE SIMULAÇÕES/CURVAS POR USUÁRIO
# ============================================================================

def salvar_curva_usuario(usuario_id: str, cliente: str, categoria: str, 
                         produto: str, curva: List[float], 
                         nome_simulacao: str = "") -> Tuple[bool, str]:
    """
    Salva a curva ajustada de um usuário específico.
    Cada usuário tem suas curvas isoladas em um arquivo JSON.
    
    IMPORTANTE: Ao primeira vez que salva, cria uma cópia da base para o usuário
    (para garantir isolamento de dados).
    
    Args:
        usuario_id: ID único do usuário
        cliente: Nome do cliente
        categoria: Categoria do produto
        produto: Nome do produto
        curva: Lista com 12 valores mensais
        nome_simulacao: Nome opcional da simulação
        
    Returns:
        (sucesso, mensagem)
    """
    try:
        # ============== NOVO: Cria cópia da base na primeira simulação do usuário ==============
        # Sempre tenta criar a base personalizada se não existir (operação idempotente)
        if not usuario_tem_base_editada(usuario_id):
            sucesso_copia, msg_copia = criar_base_usuario_copia(usuario_id)
            if sucesso_copia:
                print(f"[DB] Base personalizada criada automaticamente ao salvar simulação")
        
        # Cria arquivo específico do usuário para simulações
        arquivo_usuario = SIMULACOES_DIR / f"{usuario_id}_simulacoes.json"
        
        # Carrega simulações existentes do usuário
        if arquivo_usuario.exists():
            with open(arquivo_usuario, 'r', encoding='utf-8') as f:
                simulacoes = json.load(f)
        else:
            simulacoes = []
        
        # Gera chave única para a combinação
        combo_key = f"{cliente or 'Todos'}::{categoria}::{produto}"
        
        # Verifica se já existe simulação com essa chave
        simulacao_existente = None
        for sim in simulacoes:
            if sim.get("combo_key") == combo_key:
                simulacao_existente = sim
                break
        
        # Cria ou atualiza a simulação
        nova_simulacao = {
            "id": f"{combo_key}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "combo_key": combo_key,
            "cliente": cliente or "Todos",
            "categoria": categoria,
            "produto": produto,
            "curva": curva[:12],  # Garante 12 elementos
            "nome": nome_simulacao or f"Simulação {combo_key}",
            "data_criacao": datetime.now().isoformat(),
            "data_atualizacao": datetime.now().isoformat()
        }
        
        if simulacao_existente:
            # Atualiza existente
            simulacao_existente.update(nova_simulacao)
        else:
            # Adiciona nova
            simulacoes.append(nova_simulacao)
        
        # Salva no arquivo do usuário
        with open(arquivo_usuario, 'w', encoding='utf-8') as f:
            json.dump(simulacoes, f, indent=2, ensure_ascii=False)
        
        print(f"[DB] Curva salva para {usuario_id}: {combo_key}")
        return True, "Simulação salva com sucesso"
        
    except Exception as e:
        return False, f"Erro ao salvar simulação: {str(e)}"


def carregar_curvas_usuario(usuario_id: str) -> List[Dict]:
    """
    Carrega todas as curvas salvas de um usuário específico.
    
    Args:
        usuario_id: ID único do usuário
        
    Returns:
        Lista de simulações salvas do usuário
    """
    try:
        arquivo_usuario = SIMULACOES_DIR / f"{usuario_id}_simulacoes.json"
        
        if arquivo_usuario.exists():
            with open(arquivo_usuario, 'r', encoding='utf-8') as f:
                simulacoes = json.load(f)
                print(f"[DB] Carregadas {len(simulacoes)} simulações do usuário {usuario_id}")
                return simulacoes
        
        print(f"[DB] Nenhuma simulação encontrada para usuário {usuario_id}")
        return []
        
    except Exception as e:
        print(f"[DB] Erro ao carregar simulações: {e}")
        return []


def obter_curva_usuario(usuario_id: str, cliente: str, categoria: str, 
                       produto: str) -> Optional[List[float]]:
    """
    Obtém a curva ajustada de um usuário para uma combinação específica.
    
    Args:
        usuario_id: ID único do usuário
        cliente: Nome do cliente
        categoria: Categoria do produto
        produto: Nome do produto
        
    Returns:
        Lista com 12 valores ou None se não existir
    """
    simulacoes = carregar_curvas_usuario(usuario_id)
    combo_key = f"{cliente or 'Todos'}::{categoria}::{produto}"
    
    for simulacao in simulacoes:
        if simulacao.get("combo_key") == combo_key:
            return simulacao.get("curva", None)
    
    return None


def deletar_curva_usuario(usuario_id: str, combo_key: str) -> Tuple[bool, str]:
    """
    Deleta uma simulação específica do usuário.
    
    Args:
        usuario_id: ID único do usuário
        combo_key: Chave da combinação cliente::categoria::produto
        
    Returns:
        (sucesso, mensagem)
    """
    try:
        arquivo_usuario = SIMULACOES_DIR / f"{usuario_id}_simulacoes.json"
        
        if not arquivo_usuario.exists():
            return False, "Nenhuma simulação encontrada"
        
        with open(arquivo_usuario, 'r', encoding='utf-8') as f:
            simulacoes = json.load(f)
        
        # Remove a simulação
        simulacoes = [s for s in simulacoes if s.get("combo_key") != combo_key]
        
        # Salva de volta
        with open(arquivo_usuario, 'w', encoding='utf-8') as f:
            json.dump(simulacoes, f, indent=2, ensure_ascii=False)
        
        print(f"[DB] Curva deletada para {usuario_id}: {combo_key}")
        return True, "Simulação deletada com sucesso"
        
    except Exception as e:
        return False, f"Erro ao deletar simulação: {str(e)}"


def listar_usuarios_com_simulacoes() -> Dict[str, int]:
    """
    Lista todos os usuários que possuem simulações salvas e quantas cada um tem.
    
    Returns:
        Dicionário {usuario_id: quantidade_de_simulacoes}
    """
    resultado = {}
    
    try:
        for arquivo in SIMULACOES_DIR.glob("*_simulacoes.json"):
            usuario_id = arquivo.stem.replace("_simulacoes", "")
            with open(arquivo, 'r', encoding='utf-8') as f:
                simulacoes = json.load(f)
                resultado[usuario_id] = len(simulacoes)
    except Exception as e:
        print(f"[DB] Erro ao listar usuários com simulações: {e}")
    
    return resultado


# ============================================================================
# GERENCIAMENTO DE BASE POR USUÁRIO (NOVO)
# ============================================================================

def obter_nome_arquivo_base_usuario(usuario_id: str) -> str:
    """Gera nome padronizado do arquivo da base do usuário"""
    return f"base_usuario_{usuario_id}.xlsx"


def usuario_tem_base_editada(usuario_id: str) -> bool:
    """
    Verifica se o usuário já tem sua própria cópia da base (alterada).
    Se sim, ele tem uma versão personalizada.
    Se não, usa a base compartilhada.
    
    Args:
        usuario_id: ID do usuário
        
    Returns:
        True se usuário tem arquivo próprio
    """
    arquivo_usuario = UPLOADS_DIR / obter_nome_arquivo_base_usuario(usuario_id)
    return arquivo_usuario.exists()


def carregar_base_usuario(usuario_id: str) -> Optional[pd.DataFrame]:
    """
    Carrega a base de dados do usuário.
    
    Fluxo:
    1. Se usuário tem base editada → carrega sua cópia
    2. Se não tem → carrega base compartilhada
    
    Args:
        usuario_id: ID do usuário
        
    Returns:
        DataFrame com dados ou None
    """
    # Verifica se usuário tem sua própria cópia editada
    if usuario_tem_base_editada(usuario_id):
        arquivo_usuario = UPLOADS_DIR / obter_nome_arquivo_base_usuario(usuario_id)
        try:
            df = pd.read_excel(arquivo_usuario)
            print(f"[DB] Base personalizada do usuário {usuario_id} carregada: {len(df)} linhas")
            return df
        except Exception as e:
            print(f"[DB] Erro ao carregar base personalizada: {e}")
            # Fallback: carrega compartilhada
            return carregar_base_dados_compartilhada()
    else:
        # Carrega base compartilhada
        df = carregar_base_dados_compartilhada()
        if df is not None:
            print(f"[DB] Base compartilhada carregada para usuário {usuario_id}")
        return df


def criar_base_usuario_copia(usuario_id: str) -> Tuple[bool, str]:
    """
    Cria uma cópia personalizada da base para o usuário.
    Chamado quando usuário salva sua primeira simulação/curva.
    
    Args:
        usuario_id: ID do usuário
        
    Returns:
        (sucesso, mensagem)
    """
    try:
        # Se já tem cópia, não faz nada
        if usuario_tem_base_editada(usuario_id):
            return True, "Usuário já tem base personalizada"
        
        # Carrega base compartilhada
        df_compartilhada = carregar_base_dados_compartilhada()
        if df_compartilhada is None or df_compartilhada.empty:
            return False, "Base compartilhada não encontrada"
        
        # Cria cópia personalizada
        arquivo_usuario = UPLOADS_DIR / obter_nome_arquivo_base_usuario(usuario_id)
        
        with pd.ExcelWriter(arquivo_usuario, engine='openpyxl') as writer:
            df_compartilhada.to_excel(writer, sheet_name='Dados', index=False)
        
        print(f"[DB] Base personalizada criada para usuário {usuario_id}: {arquivo_usuario}")
        return True, f"Base personalizada criada para o usuário"
        
    except Exception as e:
        print(f"[DB] Erro ao criar base personalizada: {e}")
        return False, f"Erro ao criar base: {str(e)}"


def salvar_base_usuario(usuario_id: str, df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Salva as alterações na base do usuário.
    
    Args:
        usuario_id: ID do usuário
        df: DataFrame com alterações
        
    Returns:
        (sucesso, mensagem)
    """
    try:
        # Primeiro cria cópia se não existir
        if not usuario_tem_base_editada(usuario_id):
            criar_base_usuario_copia(usuario_id)
        
        # Salva as alterações
        arquivo_usuario = UPLOADS_DIR / obter_nome_arquivo_base_usuario(usuario_id)
        
        with pd.ExcelWriter(arquivo_usuario, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Dados', index=False)
        
        print(f"[DB] Base do usuário {usuario_id} salva: {arquivo_usuario}")
        return True, "Base do usuário atualizada"
        
    except Exception as e:
        print(f"[DB] Erro ao salvar base do usuário: {e}")
        return False, f"Erro ao salvar: {str(e)}"


# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

def inicializar_database() -> bool:
    """
    Inicializa a estrutura do mock database.
    Verifica se arquivos necessários existem, senão cria.
    
    Returns:
        True se inicializado com sucesso
    """
    try:
        # Garante que diretórios existem
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        SIMULACOES_DIR.mkdir(parents=True, exist_ok=True)
        METADATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Cria arquivo de usuários se não existir
        if not USERS_FILE.exists():
            usuarios_padrao = [
                {
                    "id": "usr_001",
                    "email": "admin@uan.com.br",
                    "nome": "Admin DIRCO",
                    "senha": "admin123",
                    "role": "admin",
                    "departamento": "DIRCO",
                    "funcao": "Administrador",
                    "data_criacao": datetime.now().isoformat(),
                    "ativo": True
                },
                {
                    "id": "usr_002",
                    "email": "teste@uan.com.br",
                    "nome": "Analista Teste",
                    "senha": "123456",
                    "role": "usuario",
                    "departamento": "Análise de Dados",
                    "funcao": "Analista de Projeções",
                    "data_criacao": datetime.now().isoformat(),
                    "ativo": True
                }
            ]
            
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(usuarios_padrao, f, indent=2, ensure_ascii=False)
        
        print("[DB] Database mockado inicializado com sucesso")
        return True
        
    except Exception as e:
        print(f"[DB] Erro ao inicializar database: {e}")
        return False


if __name__ == "__main__":
    # Testes básicos
    inicializar_database()
    
    # Teste de login
    sucesso, usuario = validar_login("admin@uan.com.br", "admin123")
    print(f"Login admin: {sucesso}, {usuario.get('nome') if usuario else 'None'}")
    
    sucesso, usuario = validar_login("teste@uan.com.br", "123456")
    print(f"Login usuario: {sucesso}, {usuario.get('nome') if usuario else 'None'}")
    
    # Teste de verificação de admin
    admin = obter_usuario_por_email("admin@uan.com.br")
    print(f"Admin? {eh_admin(admin)}")
