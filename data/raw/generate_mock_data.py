"""
Script para gerar dados mockados em formato Excel
para o sistema de projeção financeira
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def gerar_dados_mockados():
    """
    Gera dados mockados para teste do sistema
    """
    
    # Configurações
    meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 
             'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
    categorias = ['Pessoa Física', 'Pessoa Jurídica', 'Financiamento Imobiliário', 
                  'Cartão de Crédito', 'Empréstimo Pessoal', 'Renda Fixa', 
                  'Fundos de Investimento', 'Seguros']
    
    dados = []
    
    # Gerar dados para 24 meses (2 anos) com múltiplas categorias
    data_inicio = datetime(2024, 1, 1)
    
    for i in range(24):  # 24 meses de dados
        data_atual = data_inicio + timedelta(days=30 * i)
        mes_idx = data_atual.month - 1
        mes_nome = meses[mes_idx]
        ano = data_atual.year
        
        # Para cada mês, gerar dados para todas as categorias
        for categoria in categorias:
            # Gerar valor base com flutuação
            valor_base = np.random.uniform(1000, 5000)
            
            # Aplicar tendência realista (crescimento gradual)
            tendencia = 1 + (i * 0.02)  # 2% de crescimento por mês
            valor_base = valor_base * tendencia
            
            # Valores realizado (com maior variação)
            curva_realizado = valor_base * np.random.uniform(0.9, 1.1)
            
            # Projeção analítica (base para simulações)
            projetado_analitico = valor_base * np.random.uniform(0.95, 1.05)
            
            # Projeção de mercado (com maior variação)
            projetado_mercado = valor_base * np.random.uniform(0.85, 1.15)
            
            # Projeção ajustada (inicialmente igual à analítica)
            projetado_ajustado = projetado_analitico
            
            # Formatar datas
            data_completa = f"{data_atual.day:02d}/{mes_idx + 1:02d}/{ano}"
            
            dados.append({
                'DATA_COMPLETA': data_completa,
                'MES': mes_nome,
                'ANO': str(ano),
                'CATEGORIA': categoria,
                'CURVA_REALIZADO': f"R$ {curva_realizado:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','),
                'PROJETADO_ANALITICO': f"R$ {projetado_analitico:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','),
                'PROJETADO_MERCADO': f"R$ {projetado_mercado:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','),
                'PROJETADO_AJUSTADO': f"R$ {projetado_ajustado:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','),
            })
    
    # Criar DataFrame
    df = pd.DataFrame(dados)
    
    # Salvar em Excel
    output_path = os.path.join(os.path.dirname(__file__), 'projecoes_financeiras.xlsx')
    
    # Criar writer do Excel
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Projeções', index=False)
        
        # Ajustar largura das colunas
        worksheet = writer.sheets['Projeções']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            )
            worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
    
    print(f"✓ Arquivo gerado com sucesso: {output_path}")
    print(f"  Total de registros: {len(df)}")
    print(f"  Período: 2024-2025")
    print(f"  Categorias: {len(categorias)}")
    print(f"\nPrimeiras linhas:")
    print(df.head())
    
    return df

if __name__ == "__main__":
    gerar_dados_mockados()
