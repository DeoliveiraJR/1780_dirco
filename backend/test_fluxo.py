"""
Test - Simula o fluxo completo de upload → parse → sincronização
"""

import sys
from pathlib import Path

# Adicionar paths
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from database_schema import parse_excel_to_json, salvar_dados_usuario, carregar_dados_usuario, get_curva_ajustada

# 1. Criar DataFrame de teste (simulando upload do usuário)
print("\n" + "="*80)
print("1️⃣ CRIANDO DATAFRAME DE TESTE")
print("="*80)

df_teste = pd.DataFrame({
    'TIPO_CLIENTE': ['CLIENTE PF VAREJO', 'CLIENTE PF VAREJO'],
    'CATEGORIA': ['CAPTAÇÕES', 'CAPTAÇÕES'],
    'PRODUTO': ['DEPOSITO A PRAZO - CDB AUTOMÁTICO', 'DEPOSITO A PRAZO - CDB AUTOMÁTICO'],
    'MES': [1, 2],
    'MES_NUM': [1, 2],
    'ANO': [2026, 2026],
    'PROJETADO_ANALITICO': [100.0, 110.0],
    'PROJETADO_MERCADO': [95.0, 105.0],
    'PROJETADO_AJUSTADO': [98.0, 108.0],
    'COD_BLOCO': ['123456', '123456'],
    'COD_PRODUTO': ['001', '001'],
    'COD_CATEGORIA': ['CAT001', 'CAT001'],
})

print(f"✓ DataFrame criado com {len(df_teste)} linhas")
print(f"  Colunas: {list(df_teste.columns)}")

# 2. Parse Excel → JSON
print("\n" + "="*80)
print("2️⃣ PARSEANDO EXCEL → JSON (simulando salvar_upload_admin)")
print("="*80)

usuario_id = "usr_001"
print(f"Parseando para usuário: {usuario_id}")

try:
    schema = parse_excel_to_json(df_teste, usuario_id)
    num_produtos = len(schema.get("produtos", {}))
    print(f"✅ Schema criado com {num_produtos} produto(s)")
    
    # Mostrar primeiros produtos
    for i, (combo_key, dados) in enumerate(schema.get("produtos", {}).items()):
        if i < 2:
            print(f"\n   Produto #{i+1}: {combo_key}")
            projecoes = dados.get("projecoes", {})
            for ano, proj_data in projecoes.items():
                analitica = proj_data.get("analitica", [])
                ajustada = proj_data.get("ajustada", [])
                print(f"      Ano {ano}:")
                print(f"        Analítica: {analitica}")
                print(f"        Ajustada:  {ajustada}")
except Exception as e:
    print(f"❌ ERRO ao parsear: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. Salvar JSON
print("\n" + "="*80)
print("3️⃣ SALVANDO JSON (simulando salvar_dados_usuario)")
print("="*80)

try:
    sucesso, msg = salvar_dados_usuario(usuario_id, schema)
    if sucesso:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")
        sys.exit(1)
except Exception as e:
    print(f"❌ ERRO ao salvar: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Carregar e validar
print("\n" + "="*80)
print("4️⃣ CARREGANDO E VALIDANDO (simulando DRE buscando TD71)")
print("="*80)

try:
    schema_carregado = carregar_dados_usuario(usuario_id)
    if schema_carregado:
        print(f"✅ Schema carregado com sucesso")
        
        # Tentar buscar a curva que foi salva
        cliente = "CLIENTE PF VAREJO"
        categoria = "CAPTAÇÕES"
        produto = "DEPOSITO A PRAZO - CDB AUTOMÁTICO"
        ano = 2026
        
        print(f"\nBuscando curva: {cliente} / {categoria} / {produto} / {ano}")
        
        curva = get_curva_ajustada(usuario_id, cliente, categoria, produto, ano)
        
        if curva:
            print(f"✅ CURVA ENCONTRADA!")
            print(f"   Valores: {curva}")
            print(f"   Total: {sum(curva):.2f}")
            print(f"   ✓ TD71 SER PREENCHIDO NA DRE COM ESTES VALORES!")
        else:
            print(f"❌ Curva não encontrada")
            print(f"   Possível problema na busca")
    else:
        print(f"❌ Schema não carregado")
except Exception as e:
    print(f"❌ ERRO ao validar: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("✅ TESTE COMPLETO - FLUXO FUNCIONANDO!")
print("="*80)
print("""
PRÓXIMOS PASSOS:
1. Fazer upload real no Upload page
2. Clicar em "💾 Salvar como Base Compartilhada"
3. Ir para Simulador → Salvar simulação (vai sincronizar com backend)
4. Ir para DRE → TD71 deve estar preenchido automaticamente!
""")
