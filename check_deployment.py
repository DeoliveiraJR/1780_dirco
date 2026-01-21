#!/usr/bin/env python
"""
Script de validação pré-deployment
Verifica se todas as dependências e configurações estão corretas
"""

import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Verifica versão do Python"""
    print("🔍 Verificando versão do Python...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro} ✅")
    return version.major >= 3 and version.minor >= 9

def check_imports():
    """Verifica se todos os módulos podem ser importados"""
    print("\n🔍 Verificando imports necessários...")
    
    required_modules = [
        'streamlit',
        'plotly',
        'pandas',
        'numpy',
        'openpyxl',
        'requests',
        'PIL',  # Pillow usa PIL como nome
        'bokeh'
    ]
    
    all_good = True
    for module in required_modules:
        try:
            __import__(module)
            print(f"   {module:<15} ✅")
        except ImportError:
            print(f"   {module:<15} ❌ NOT INSTALLED")
            all_good = False
    
    return all_good

def check_file_structure():
    """Verifica estrutura de arquivos"""
    print("\n🔍 Verificando estrutura de arquivos...")
    
    required_files = [
        'frontend/app.py',
        'frontend/data_manager.py',
        'frontend/styles.py',
        'frontend/pages/dashboard.py',
        'frontend/pages/simulador.py',
        'frontend/pages/upload.py',
        'frontend/pages/autenticacao.py',
        'requirements.txt',
        '.streamlit/config.toml',
        'Dockerfile'
    ]
    
    all_good = True
    for file in required_files:
        path = Path(file)
        if path.exists():
            size = path.stat().st_size
            print(f"   {file:<40} ✅ ({size} bytes)")
        else:
            print(f"   {file:<40} ❌ NOT FOUND")
            all_good = False
    
    return all_good

def check_streamlit_config():
    """Verifica configuração do Streamlit"""
    print("\n🔍 Verificando configuração do Streamlit...")
    
    config_path = Path('.streamlit/config.toml')
    if config_path.exists():
        with open(config_path, 'r') as f:
            content = f.read()
            if '[theme]' in content and '[server]' in content:
                print(f"   {str(config_path):<40} ✅")
                return True
    
    print(f"   {str(config_path):<40} ⚠️ BASIC CONFIG")
    return True

def check_requirements():
    """Verifica requirements.txt"""
    print("\n🔍 Verificando requirements.txt...")
    
    req_path = Path('requirements.txt')
    if req_path.exists():
        with open(req_path, 'r') as f:
            lines = f.readlines()
            print(f"   {len(lines)} dependências encontradas ✅")
            
            # Mostrar principais
            important = ['streamlit', 'plotly', 'pandas', 'flask']
            for imp in important:
                for line in lines:
                    if imp in line.lower():
                        print(f"   - {line.strip()}")
                        break
        return True
    
    print(f"   requirements.txt ❌ NOT FOUND")
    return False

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         UAN DASHBOARD - PRÉ-DEPLOYMENT CHECK             ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    checks = [
        check_python_version(),
        check_imports(),
        check_file_structure(),
        check_streamlit_config(),
        check_requirements()
    ]
    
    print("\n" + "="*60)
    
    if all(checks):
        print("\n✅ TUDO OK! Seu projeto está pronto para deployment!\n")
        print("Próximos passos:")
        print("1. Vá para https://streamlit.io/cloud")
        print("2. Faça upload deste projeto")
        print("3. Configure para rodar frontend/app.py")
        print("4. Clique em Deploy!")
        return 0
    else:
        print("\n⚠️ ALGUNS PROBLEMAS ENCONTRADOS")
        print("   Por favor, corrija os itens marcados com ❌")
        print("   Rode: pip install -r requirements.txt")
        return 1

if __name__ == '__main__':
    sys.exit(main())
