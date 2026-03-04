#!/usr/bin/env python3
"""
Script de Teste - Mock Database
Valida a implementação do sistema de persistência
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import (
    inicializar_database,
    validar_login,
    obter_usuario_por_email,
    eh_admin,
    carregar_usuarios,
    salvar_curva_usuario,
    carregar_curvas_usuario,
    obter_curva_usuario,
    listar_usuarios_com_simulacoes
)

def teste_autenticacao():
    print("\n" + "="*60)
    print("🧪 TESTE 1: AUTENTICAÇÃO")
    print("="*60)
    
    # Teste 1.1: Login admin
    print("\n1️⃣ Login Admin")
    sucesso, usuario = validar_login("admin@uan.com.br", "admin123")
    print(f"   ✓ Email: {usuario.get('email') if sucesso else 'FALHA'}")
    print(f"   ✓ Nome: {usuario.get('nome') if sucesso else 'FALHA'}")
    print(f"   ✓ Role: {usuario.get('role') if sucesso else 'FALHA'}")
    print(f"   ✓ Admin?: {eh_admin(usuario) if sucesso else 'N/A'}")
    
    # Teste 1.2: Login usuário comum
    print("\n2️⃣ Login Usuário Comum")
    sucesso2, usuario2 = validar_login("teste@uan.com.br", "123456")
    print(f"   ✓ Email: {usuario2.get('email') if sucesso2 else 'FALHA'}")
    print(f"   ✓ Nome: {usuario2.get('nome') if sucesso2 else 'FALHA'}")
    print(f"   ✓ Role: {usuario2.get('role') if sucesso2 else 'FALHA'}")
    print(f"   ✓ Admin?: {eh_admin(usuario2) if sucesso2 else 'N/A'}")
    
    # Teste 1.3: Login inválido
    print("\n3️⃣ Login Inválido")
    sucesso3, usuario3 = validar_login("invalido@test.com", "wrongpass")
    print(f"   ✓ Rejeitado corretamente: {not sucesso3}")
    
    return sucesso and sucesso2 and not sucesso3

def teste_usuarios():
    print("\n" + "="*60)
    print("🧪 TESTE 2: GERENCIAMENTO DE USUÁRIOS")
    print("="*60)
    
    print("\n1️⃣ Carregar Usuários")
    usuarios = carregar_usuarios()
    print(f"   ✓ Total de usuários: {len(usuarios)}")
    
    for usuario in usuarios:
        print(f"   - {usuario.get('nome')} ({usuario.get('role')})")
    
    print("\n2️⃣ Buscar Usuário por Email")
    usuario = obter_usuario_por_email("admin@uan.com.br")
    print(f"   ✓ Encontrado: {usuario.get('nome') if usuario else 'NÃO ENCONTRADO'}")
    
    return len(usuarios) >= 2

def teste_curvas():
    print("\n" + "="*60)
    print("🧪 TESTE 3: PERSISTÊNCIA DE CURVAS")
    print("="*60)
    
    usuario_id = "usr_002"
    cliente = "Todos"
    categoria = "Teste"
    produto = "Produto Teste"
    curva_teste = [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210]
    
    # Teste 3.1: Salvar curva
    print("\n1️⃣ Salvar Curva")
    sucesso, msg = salvar_curva_usuario(usuario_id, cliente, categoria, produto, curva_teste)
    print(f"   ✓ {msg}")
    
    # Teste 3.2: Carregar curva específica
    print("\n2️⃣ Carregar Curva Específica")
    curva_carregada = obter_curva_usuario(usuario_id, cliente, categoria, produto)
    if curva_carregada:
        print(f"   ✓ Encontrada: {curva_carregada[:3]}... (primeiros 3 meses)")
        print(f"   ✓ Valores corretos: {curva_carregada == curva_teste}")
    else:
        print("   ✗ Curva não encontrada")
    
    # Teste 3.3: Carregar todas as curvas do usuário
    print("\n3️⃣ Carregar Todas as Curvas do Usuário")
    curvas = carregar_curvas_usuario(usuario_id)
    print(f"   ✓ Total de curvas salvas: {len(curvas)}")
    for sim in curvas:
        print(f"   - {sim.get('combo_key')}: {sim.get('nome')}")
    
    # Teste 3.4: Simular segundo usuário
    print("\n4️⃣ Simular Segundo Usuário (Isolamento)")
    usuario_id_2 = "usr_001"
    sucesso2, msg2 = salvar_curva_usuario(
        usuario_id_2, 
        cliente, 
        "Outra Categoria", 
        "Outro Produto",
        [50] * 12
    )
    print(f"   ✓ {msg2}")
    
    # Teste 3.5: Verificar isolamento
    print("\n5️⃣ Verificar Isolamento entre Usuários")
    curvas_user1 = carregar_curvas_usuario(usuario_id)
    curvas_user2 = carregar_curvas_usuario(usuario_id_2)
    print(f"   ✓ Curvas do usuário 1: {len(curvas_user1)}")
    print(f"   ✓ Curvas do usuário 2: {len(curvas_user2)}")
    print(f"   ✓ Isoladas: {len(curvas_user1) != len(curvas_user2)}")
    
    return sucesso and curva_carregada == curva_teste

def teste_usuarios_com_simulacoes():
    print("\n" + "="*60)
    print("🧪 TESTE 4: LISTAR USUÁRIOS COM SIMULAÇÕES")
    print("="*60)
    
    print("\n1️⃣ Usuários com Simulações")
    usuarios_sims = listar_usuarios_com_simulacoes()
    print(f"   ✓ Total de usuários com simulações: {len(usuarios_sims)}")
    
    for usuario_id, qtd in usuarios_sims.items():
        print(f"   - {usuario_id}: {qtd} simulações")
    
    return True

def main():
    print("\n" + "█"*60)
    print("█  TESTE DO MOCK DATABASE SYSTEM")
    print("█"*60)
    
    # Inicializa database
    print("\n🔧 Inicializando database...")
    inicializar_database()
    print("   ✓ Database inicializado")
    
    # Executa testes
    testes = [
        ("Autenticação", teste_autenticacao),
        ("Usuários", teste_usuarios),
        ("Curvas (Persistência)", teste_curvas),
        ("Usuários com Simulações", teste_usuarios_com_simulacoes)
    ]
    
    resultados = []
    for nome, funcao_teste in testes:
        try:
            resultado = funcao_teste()
            resultados.append((nome, resultado))
        except Exception as e:
            print(f"\n   ✗ Erro: {str(e)}")
            resultados.append((nome, False))
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    for nome, resultado in resultados:
        status = "✓ PASSOU" if resultado else "✗ FALHOU"
        print(f"{status} - {nome}")
    
    total_passou = sum(1 for _, r in resultados if r)
    total_testes = len(resultados)
    
    print(f"\n🎯 Total: {total_passou}/{total_testes} testes passaram")
    
    if total_passou == total_testes:
        print("\n✅ TODOS OS TESTES PASSARAM!")
    else:
        print(f"\n⚠️ {total_testes - total_passou} teste(s) falharam")
    
    return total_passou == total_testes

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)
