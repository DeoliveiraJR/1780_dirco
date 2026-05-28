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
INDICES_DIR = BASE_DIR / "indices"

# Criar diretórios se não existirem
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
SIMULACOES_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)
INDICES_DIR.mkdir(parents=True, exist_ok=True)


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
    Suporta múltiplas abas: DADOS (projeções) e INDICES_TESOU (índices econômicos).
    
    Fluxo:
    1. Se houver aba DADOS  salva em base_dados_compartilhada.xlsx
    2. Se houver aba INDICES_TESOU  salva em base_indices_compartilhada.xlsx
    3. Sincroniza dados com todos os usuários
    
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
        from io import BytesIO
        import openpyxl
        
        # 1. Detectar abas disponíveis
        arquivo_io = BytesIO(arquivo_excel)
        wb = openpyxl.load_workbook(arquivo_io)
        abas_disponíveis = wb.sheetnames
        print(f"[DB] Abas encontradas: {abas_disponíveis}")
        
        has_dados = any(aba.lower().strip() in ['dados', 'data'] for aba in abas_disponíveis)
        has_indices = any(aba.lower().strip() == 'indices_tesou' for aba in abas_disponíveis)
        print(f"[DB] has_dados={has_dados}, has_indices={has_indices}")
        print(f"[DB] Abas normalizadas: {[aba.lower().strip() for aba in abas_disponíveis]}")
        
        resultados = {"dados": False, "indices": False, "msg_dados": "", "msg_indices": ""}
        
        # 2. Processar aba DADOS (projeções)
        if has_dados:
            aba_dados = next((a for a in abas_disponíveis if a.lower().strip() in ['dados', 'data']), None)
            print(f"[DB] Processando aba de dados: {aba_dados}")
            
            try:
                df_dados = pd.read_excel(BytesIO(arquivo_excel), sheet_name=aba_dados)
                
                # Salva o arquivo de dados
                caminho_arquivo_dados = UPLOADS_DIR / "base_dados_compartilhada.xlsx"
                with open(caminho_arquivo_dados, 'wb') as f:
                    f.write(arquivo_excel)  # Mantém arquivo original com ambas as abas
                
                # Metadados de dados
                metadata_dados = {
                    "arquivo_original": nome_arquivo,
                    "arquivo_salvo": str(caminho_arquivo_dados.relative_to(BASE_DIR.parent)),
                    "aba_processada": aba_dados,
                    "usuario_id": usuario_id,
                    "usuario_email": usuario.get("email"),
                    "data_upload": datetime.now().isoformat(),
                    "tamanho_bytes": len(arquivo_excel),
                    "linhas": len(df_dados),
                    "colunas": list(df_dados.columns),
                    "tipo": "projecoes"
                }
                
                metadata_file = METADATA_DIR / "ultimo_upload_dados.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata_dados, f, indent=2, ensure_ascii=False)
                
                # Parse para JSON estruturado e sincroniza
                print(f"[DB] Iniciando parse DADOS  JSON...")
                usuarios_sistema = carregar_usuarios()
                
                for usr in usuarios_sistema:
                    usr_id = usr.get("id")
                    if usr_id:
                        try:
                            schema = parse_excel_to_json(df_dados, usr_id)
                            sucesso, msg = salvar_dados_usuario(usr_id, schema)
                            if not sucesso:
                                print(f"[DB]     Erro ao salvar para {usr_id}: {msg}")
                        except Exception as e:
                            print(f"[DB]     Erro ao parsear para {usr_id}: {e}")
                
                resultados["dados"] = True
                resultados["msg_dados"] = f" Base de Projeções: {len(df_dados)} registros importados"
                print(f"[DB] Dados salvos: {caminho_arquivo_dados}")
                
            except Exception as e:
                print(f"[DB]  Erro ao processar dados: {e}")
                resultados["msg_dados"] = f" Erro ao importar projeções: {str(e)}"
        
        # 3. Processar aba INDICES_TESOU
        if has_indices:
            print(f"[DB]   Entrando no fluxo de indices (has_indices=True)")
            aba_indices = next((a for a in abas_disponíveis if a.lower().strip() == 'indices_tesou'), None)
            print(f"[DB] aba_indices encontrada: {aba_indices}")
            if not aba_indices:
                print(f"[DB]   Aba INDICES_TESOU nao encontrada, pulando...")
                has_indices = False
            else:
                print(f"[DB] Processando aba de indices: {aba_indices}")
            
            try:
                print(f"[DB]  Lendo DataFrame da aba {aba_indices}")
                df_indices = pd.read_excel(BytesIO(arquivo_excel), sheet_name=aba_indices)
                print(f"[DB]  DataFrame lido: {len(df_indices)} linhas, {len(df_indices.columns)} colunas")
                print(f"[DB]  Colunas: {list(df_indices.columns)}")
                
                # Salva o arquivo de índices
                caminho_arquivo_indices = UPLOADS_DIR / "base_indices_compartilhada.xlsx"
                with open(caminho_arquivo_indices, 'wb') as f:
                    f.write(arquivo_excel)
                
                # Metadados de índices
                metadata_indices = {
                    "arquivo_original": nome_arquivo,
                    "arquivo_salvo": str(caminho_arquivo_indices.relative_to(BASE_DIR.parent)),
                    "aba_processada": aba_indices,
                    "usuario_id": usuario_id,
                    "usuario_email": usuario.get("email"),
                    "data_upload": datetime.now().isoformat(),
                    "tamanho_bytes": len(arquivo_excel),
                    "linhas": len(df_indices),
                    "colunas": list(df_indices.columns),
                    "tipo": "indices"
                }
                
                metadata_file = METADATA_DIR / "ultimo_upload_indices.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata_indices, f, indent=2, ensure_ascii=False)
                
                # Processar índices para JSON estruturado
                print(f"[DB]  Processando indices para JSON estruturado...")
                try:
                    dados_indices_json = processar_indices_para_json(df_indices)
                    print(f"[DB]  processar_indices_para_json retornou: {dados_indices_json.get('metadata') if dados_indices_json else 'None'}")
                    if dados_indices_json and dados_indices_json.get("indices"):
                        print(f"[DB]  Chamando salvar_indices_json...")
                        sucesso_json, msg_json = salvar_indices_json(dados_indices_json)
                        print(f"[DB]  salvar_indices_json: sucesso={sucesso_json}, msg={msg_json}")
                        
                        resultados["indices"] = True
                        indices_unicos = dados_indices_json['metadata'].get('indices_unicos', 0)
                        resultados["msg_indices"] = f" Indices Economicos: {len(df_indices)} registros importados ({indices_unicos} indices unicos)"
                        print(f"[DB]  Indices salvos com sucesso!")
                    else:
                        print(f"[DB]   Nenhum indice valido apos processamento")
                        resultados["msg_indices"] = "Nenhum indice valido apos processamento"
                except Exception as e_json:
                    print(f"[DB]  Erro ao processar JSON de indices: {e_json}")
                    import traceback
                    traceback.print_exc()
                    resultados["msg_indices"] = f"Indices salvos em XLSX mas erro ao processar JSON: {str(e_json)}"
                
            except Exception as e:
                print(f"[DB] Erro ao processar indices: {e}")
                resultados["msg_indices"] = f"Erro ao importar indices: {str(e)}"
        
        # 4. Montar mensagem final
        print(f"[DB] === RESULTADO FINAL ===")
        print(f"[DB] resultados['dados'] = {resultados['dados']}")
        print(f"[DB] resultados['indices'] = {resultados['indices']}")
        print(f"[DB] msg_dados: {resultados['msg_dados']}")
        print(f"[DB] msg_indices: {resultados['msg_indices']}")
        
        mensagem = ""
        if resultados["dados"]:
            mensagem += resultados["msg_dados"] + "\n"
        if resultados["indices"]:
            mensagem += resultados["msg_indices"] + "\n"
        
        print(f"[DB] mensagem final: {mensagem}")
        
        if not mensagem:
            print(f"[DB]  Nenhuma aba válida encontrada")
            return False, "Nenhuma aba válida encontrada (DADOS ou INDICES_TESOU)"
        
        print(f"[DB]  Upload finalizado com sucesso")
        return True, mensagem.strip()
        
    except Exception as e:
        print(f"[DB]  ERRO GERAL: {e}")
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
        metadata_file = METADATA_DIR / "ultimo_upload_dados.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Fallback para arquivo anterior (compatibilidade)
        metadata_file_old = METADATA_DIR / "ultimo_upload.json"
        if metadata_file_old.exists():
            with open(metadata_file_old, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
        
    except Exception as e:
        print(f"[DB] Erro ao carregar metadados: {e}")
        return None


def carregar_indices_compartilhados() -> Optional[pd.DataFrame]:
    """
    Carrega a base de índices econômicos compartilhada entre todos os usuários.
    
    Returns:
        DataFrame com índices ou None se não existir
    """
    try:
        caminho_arquivo = UPLOADS_DIR / "base_indices_compartilhada.xlsx"
        
        if caminho_arquivo.exists():
            df = pd.read_excel(caminho_arquivo, sheet_name="INDICES_TESOU")
            print(f"[DB] Índices compartilhados carregados: {len(df)} linhas")
            return df
        
        print("[DB] Nenhuma base de índices encontrada ainda")
        return None
        
    except Exception as e:
        print(f"[DB] Erro ao carregar índices compartilhados: {e}")
        return None


def obter_metadados_ultimo_upload_indices() -> Optional[Dict]:
    """
    Obtém informações sobre o último upload de índices.
    
    Returns:
        Dicionário com metadados ou None
    """
    try:
        metadata_file = METADATA_DIR / "ultimo_upload_indices.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
        
    except Exception as e:
        print(f"[DB] Erro ao carregar metadados de índices: {e}")
        return None


def indices_existem() -> bool:
    """
    Verifica se já foram importados índices econômicos.
    
    Returns:
        True se índices existem
    """
    try:
        caminho_arquivo = UPLOADS_DIR / "base_indices_compartilhada.xlsx"
        return caminho_arquivo.exists()
    except Exception:
        return False


# ============================================================================
# PROCESSAMENTO E ARMAZENAMENTO ESTRUTURADO DE ÍNDICES
# ============================================================================

def processar_indices_para_json(df_indices: pd.DataFrame) -> Dict:
    """
    Processa DataFrame de índices e converte para estrutura JSON normalizada.
    
    Esperado:
    - DT_ALVO: Data alvo (coluna de data)
    - DT_PRJ: Data de projeção (coluna de data)
    - VL_PJTD: Valor projetado (numérico)
    - NM_IN: Nome do índice (texto)
    - Outras colunas: preservadas como estão
    
    Args:
        df_indices: DataFrame com dados dos índices
        
    Returns:
        Dicionário estruturado com metadados e dados dos índices
    """
    print(f"[DB] processar_indices_para_json() chamado")
    print(f"[DB]   - df_indices: {type(df_indices)}, shape={df_indices.shape if df_indices is not None else 'None'}")
    
    if df_indices is None or df_indices.empty:
        print(f"[DB]   DataFrame vazio ou None")
        return {"metadata": {}, "indices": {}}
    
    try:
        df = df_indices.copy()
        
        # Normalizar nomes de colunas (upper, strip)
        df.columns = [col.upper().strip() for col in df.columns]
        
        # Estrutura base
        resultado = {
            "metadata": {
                "total_linhas": len(df),
                "colunas": list(df.columns),
                "data_processamento": datetime.now().isoformat(),
                "versao": "1.0"
            },
            "indices": {}
        }
        
        # Iterar e estruturar por nome de índice
        for idx, row in df.iterrows():
            try:
                nm_in = str(row.get("NM_IN", f"INDICE_{idx}")).strip()
                if not nm_in or nm_in.lower() == "nan":
                    nm_in = f"INDICE_{idx}"
                
                # Se é primeira ocorrência deste índice, criar entrada
                if nm_in not in resultado["indices"]:
                    resultado["indices"][nm_in] = {
                        "nome": nm_in,
                        "registros": [],
                        "data_primeira": None,
                        "data_ultima": None
                    }
                
                # Processar datas
                dt_alvo = None
                dt_prj = None
                
                if "DT_ALVO" in df.columns:
                    try:
                        dt_alvo_val = row.get("DT_ALVO")
                        if pd.notna(dt_alvo_val):
                            if isinstance(dt_alvo_val, (int, float)):
                                # Serial Excel
                                dt_alvo = pd.Timestamp(1899, 12, 30) + pd.Timedelta(days=dt_alvo_val)
                                dt_alvo = dt_alvo.strftime("%Y-%m-%d")
                            else:
                                dt_alvo = pd.to_datetime(dt_alvo_val, errors='coerce').strftime("%Y-%m-%d")
                    except Exception as e:
                        print(f"[DB] Erro ao processar DT_ALVO linha {idx}: {e}")
                
                if "DT_PRJ" in df.columns:
                    try:
                        dt_prj_val = row.get("DT_PRJ")
                        if pd.notna(dt_prj_val):
                            if isinstance(dt_prj_val, (int, float)):
                                dt_prj = pd.Timestamp(1899, 12, 30) + pd.Timedelta(days=dt_prj_val)
                                dt_prj = dt_prj.strftime("%Y-%m-%d")
                            else:
                                dt_prj = pd.to_datetime(dt_prj_val, errors='coerce').strftime("%Y-%m-%d")
                    except Exception as e:
                        print(f"[DB] Erro ao processar DT_PRJ linha {idx}: {e}")
                
                # Valor projetado
                vl_pjtd = None
                if "VL_PJTD" in df.columns:
                    try:
                        vl_pjtd = float(row.get("VL_PJTD", 0) or 0)
                    except (ValueError, TypeError):
                        vl_pjtd = 0
                
                # Montar registro
                registro = {
                    "dt_alvo": dt_alvo,
                    "dt_prj": dt_prj,
                    "vl_pjtd": vl_pjtd
                }
                
                # Adicionar outras colunas
                for col in df.columns:
                    if col not in ["DT_ALVO", "DT_PRJ", "VL_PJTD", "NM_IN"]:
                        registro[col.lower()] = str(row.get(col, ""))
                
                resultado["indices"][nm_in]["registros"].append(registro)
                
                # Atualizar datas extremas
                if dt_alvo:
                    if resultado["indices"][nm_in]["data_primeira"] is None:
                        resultado["indices"][nm_in]["data_primeira"] = dt_alvo
                    resultado["indices"][nm_in]["data_ultima"] = dt_alvo
                
            except Exception as e:
                print(f"[DB] Erro ao processar linha {idx}: {e}")
                continue
        
        # Resumo por índice
        resultado["metadata"]["indices_unicos"] = len(resultado["indices"])
        
        print(f"[DB] processar_indices_para_json() resultado:")
        print(f"[DB]   - indices_unicos: {resultado['metadata'].get('indices_unicos')}")
        print(f"[DB]   - total_linhas: {resultado['metadata'].get('total_linhas')}")
        print(f"[DB]   - indices keys: {list(resultado['indices'].keys())[:5]}")  # Primeiras 5
        
        return resultado
        
    except Exception as e:
        print(f"[DB] Erro ao processar índices: {e}")
        import traceback
        traceback.print_exc()
        return {"metadata": {}, "indices": {}}


def salvar_indices_json(dados_indices: Dict) -> Tuple[bool, str]:
    """
    Salva índices processados em formato JSON estruturado.
    
    Args:
        dados_indices: Dicionário com estrutura de índices processados
        
    Returns:
        (sucesso, mensagem)
    """
    try:
        arquivo_json = INDICES_DIR / "indices_compartilhados.json"
        
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(dados_indices, f, indent=2, ensure_ascii=False)
        
        print(f"[DB] Índices salvos em JSON: {arquivo_json}")
        return True, f"Índices processados e salvos: {dados_indices['metadata'].get('indices_unicos', 0)} índices únicos"
        
    except Exception as e:
        print(f"[DB] Erro ao salvar índices JSON: {e}")
        return False, f"Erro ao salvar índices: {str(e)}"


def carregar_indices_json() -> Optional[Dict]:
    """
    Carrega índices estruturados do arquivo JSON.
    
    Returns:
        Dicionário com estrutura de índices ou None
    """
    try:
        arquivo_json = INDICES_DIR / "indices_compartilhados.json"
        
        if arquivo_json.exists():
            with open(arquivo_json, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
        
    except Exception as e:
        print(f"[DB] Erro ao carregar índices JSON: {e}")
        return None


def obter_indices_por_nome(nome_indice: str) -> Optional[List[Dict]]:
    """
    Obtém registros de um índice específico pelo nome.
    
    Args:
        nome_indice: Nome do índice (ex: "SELIC", "DI")
        
    Returns:
        Lista com registros do índice ou None
    """
    try:
        dados = carregar_indices_json()
        if dados and "indices" in dados:
            if nome_indice in dados["indices"]:
                return dados["indices"][nome_indice].get("registros", [])
        return None
    except Exception as e:
        print(f"[DB] Erro ao obter índice {nome_indice}: {e}")
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
    1. Se usuário tem base editada  carrega sua cópia
    2. Se não tem  carrega base compartilhada
    
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
