"""
Debug Tool - Verifica se o schema foi criado corretamente
Usa este script para diagnosticar problemas de sincronização
"""

import json
from pathlib import Path
from database_schema import carregar_dados_usuario

BASE_DIR = Path(__file__).parent / "database"
DADOS_DIR = BASE_DIR / "dados"


def verificar_arquivos_criados():
    """Verifica arquivos JSON criados"""
    print("\n" + "="*80)
    print("🔍 VERIFICANDO ARQUIVOS CRIADOS")
    print("="*80)
    
    if not DADOS_DIR.exists():
        print(f"❌ Diretório não existe: {DADOS_DIR}")
        return
    
    arquivos = list(DADOS_DIR.glob("*.json"))
    
    if not arquivos:
        print(f"❌ NENHUM arquivo JSON encontrado em {DADOS_DIR}")
        return
    
    print(f"\n✅ {len(arquivos)} arquivo(s) encontrado(s):")
    for arq in arquivos:
        tamanho = arq.stat().st_size
        print(f"   - {arq.name} ({tamanho} bytes)")


def debugar_usuario(usuario_id: str):
    """Debugar dados de um usuário específico"""
    print("\n" + "="*80)
    print(f"🔍 DEBUGANDO USUÁRIO: {usuario_id}")
    print("="*80)
    
    arquivo = DADOS_DIR / f"{usuario_id}_dados.json"
    
    if not arquivo.exists():
        print(f"❌ Arquivo não existe: {arquivo}")
        return
    
    print(f"✅ Arquivo encontrado: {arquivo}")
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # Metadata
        metadata = schema.get("metadata", {})
        print(f"\n📋 METADATA:")
        print(f"   Usuario ID: {metadata.get('usuario_id')}")
        print(f"   Última atualização: {metadata.get('data_ultima_atualizacao')}")
        print(f"   Total linhas origem: {metadata.get('total_linhas_origem')}")
        
        # Produtos
        produtos = schema.get("produtos", {})
        print(f"\n📦 PRODUTOS: {len(produtos)} encontrados")
        
        for combo_key, produto_data in list(produtos.items())[:5]:  # Mostra primeiros 5
            print(f"\n   {combo_key}:")
            
            projecoes = produto_data.get("projecoes", {})
            for ano, proj_data in projecoes.items():
                analitica = proj_data.get("analitica", [])
                ajustada = proj_data.get("ajustada", [])
                
                has_analitica = any(v != 0.0 for v in analitica)
                has_ajustada = any(v != 0.0 for v in ajustada)
                
                print(f"      Ano {ano}:")
                print(f"        ✓ Analítica: {analitica[:3]}... ({len(analitica)} meses, populated={has_analitica})")
                print(f"        ✓ Ajustada:  {ajustada[:3]}... ({len(ajustada)} meses, populated={has_ajustada})")
        
        if len(produtos) > 5:
            print(f"\n   ... e {len(produtos) - 5} produto(s) mais")
        
        return schema
        
    except Exception as e:
        print(f"❌ Erro ao carregar: {e}")
        return None


def debugar_curva_especifica(usuario_id: str, cliente: str, categoria: str, produto: str, ano: int):
    """Debugar curva de um produto específico"""
    print("\n" + "="*80)
    print(f"🔍 DEBUGANDO CURVA ESPECÍFICA")
    print("="*80)
    
    from database_schema import get_curva_ajustada
    
    print(f"Usuario: {usuario_id}")
    print(f"Produto: {cliente} / {categoria} / {produto} / {ano}")
    
    try:
        curva = get_curva_ajustada(usuario_id, cliente, categoria, produto, ano)
        
        if curva:
            print(f"\n✅ CURVA ENCONTRADA:")
            print(f"   Valores: {curva}")
            print(f"   Total: {sum(curva):.2f}")
            print(f"   Populated: {any(v != 0.0 for v in curva)}")
        else:
            print(f"\n❌ CURVA NÃO ENCONTRADA")
            
            # Debugar por que não foi encontrada
            print(f"\n   Tentando carregar schema...")
            schema = carregar_dados_usuario(usuario_id)
            
            if not schema:
                print(f"   ❌ Schema não carregado para {usuario_id}")
                return
            
            from database_schema import _gerar_combo_key
            combo_key = _gerar_combo_key(cliente, categoria, produto)
            print(f"   Chave procurada: {combo_key}")
            
            produtos = schema.get("produtos", {})
            print(f"   Produtos no schema: {list(produtos.keys())[:3]}...")
            
            if combo_key not in produtos:
                print(f"   ❌ Combo key NÃO EXISTE no schema")
                # Mostrar chaves similares
                similar = [k for k in produtos.keys() if categoria in k]
                if similar:
                    print(f"   Chaves similares encontradas: {similar[:3]}")
            else:
                print(f"   ✓ Combo key encontrada no schema")
                proj = produtos[combo_key].get("projecoes", {})
                print(f"   Anos disponíveis: {list(proj.keys())}")
                
                if str(ano) not in proj:
                    print(f"   ❌ Ano {ano} NÃO existe")
                else:
                    print(f"   ✓ Ano {ano} existe")
                    curva_schema = proj[str(ano)].get("ajustada")
                    print(f"   Curva no schema: {curva_schema}")
        
    except Exception as e:
        print(f"❌ Erro ao debugar: {e}")
        import traceback
        traceback.print_exc()


def teste_fluxo_completo():
    """Teste completo do fluxo"""
    print("\n" + "="*80)
    print("🧪 TESTE COMPLETO DO FLUXO")
    print("="*80)
    
    print("\n1️⃣ Verificando arquivos criados...")
    verificar_arquivos_criados()
    
    print("\n2️⃣ Listando usuários com schema...")
    arquivos = list(DADOS_DIR.glob("*_dados.json"))
    if arquivos:
        usuario_id = arquivos[0].name.replace("_dados.json", "")
        print(f"   Encontrado: {usuario_id}")
        
        print(f"\n3️⃣ Debugando usuário {usuario_id}...")
        schema = debugar_usuario(usuario_id)
        
        if schema:
            produtos = schema.get("produtos", {})
            if produtos:
                combo_key = list(produtos.keys())[0]
                cliente, categoria, produto = combo_key.split("::")
                
                print(f"\n4️⃣ Debugando curva: {cliente} / {categoria} / {produto}...")
                debugar_curva_especifica(usuario_id, cliente, categoria, produto, 2026)
    else:
        print("   ❌ Nenhum arquivo encontrado")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        teste_fluxo_completo()
    elif sys.argv[1] == "arquivos":
        verificar_arquivos_criados()
    elif sys.argv[1] == "usuario" and len(sys.argv) > 2:
        debugar_usuario(sys.argv[2])
    elif sys.argv[1] == "curva" and len(sys.argv) >= 6:
        usuario_id = sys.argv[2]
        cliente = sys.argv[3]
        categoria = sys.argv[4]
        produto = sys.argv[5]
        ano = int(sys.argv[6]) if len(sys.argv) > 6 else 2026
        debugar_curva_especifica(usuario_id, cliente, categoria, produto, ano)
    else:
        print("Uso:")
        print("  python debug_schema.py                        # Teste completo")
        print("  python debug_schema.py arquivos               # Verificar arquivos")
        print("  python debug_schema.py usuario <usuario_id>   # Debugar usuário")
        print("  python debug_schema.py curva <user> <cli> <cat> <prod> [ano]")
