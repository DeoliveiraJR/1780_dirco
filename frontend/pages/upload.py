"""
Página de Upload de Dados Financeiros
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_manager import set_dados_upload, get_dados_upload


def renderizar():
    st.markdown("### 📤 Upload de Dados Financeiros")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📤 Carregar Dados", "📊 Dados Carregados"])
    
    with tab1:
        upload_interface()
    
    with tab2:
        dados_carregados()


def upload_interface():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Selecione o arquivo Excel para importar")
        
        uploaded_file = st.file_uploader(
            "Escolha um arquivo Excel (.xlsx)",
            type=["xlsx", "xls"],
            key="file_uploader"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                
                st.success(f"✅ Arquivo carregado com sucesso!")
                st.info(f"📊 Total de registros: {len(df)}")
                
                with st.expander("📋 Visualizar dados carregados"):
                    st.dataframe(df, use_container_width=True)
                
                if st.button("✔️ Confirmar e Carregar Dados", use_container_width=True, type="primary"):
                    processar_dados(df)
                    
            except Exception as e:
                st.error(f"❌ Erro ao ler arquivo: {str(e)}")
    
    with col2:
        st.markdown("#### Estrutura Esperada")
        st.markdown("""
        **Colunas Obrigatórias:**
        
        - DATA_COMPLETA (dd/mm/yyyy)
        - MES (texto: janeiro)
        - ANO (texto: 2025)
        - COD_CATEGORIA
        - CATEGORIA
        - COD_PRODUTO
        - PRODUTO
        - CURVA_REALIZADO
        - PROJETADO_ANALITICO
        - PROJETADO_MERCADO
        - PROJETADO_AJUSTADO
        """)
        
        if st.button("📥 Baixar Template", use_container_width=True):
            gerar_template()


def processar_dados(df):
    try:
        required_columns = [
            'DATA_COMPLETA', 'MES', 'ANO', 'COD_CATEGORIA', 'CATEGORIA',
            'COD_PRODUTO', 'PRODUTO', 'CURVA_REALIZADO', 'PROJETADO_ANALITICO',
            'PROJETADO_MERCADO', 'PROJETADO_AJUSTADO'
        ]
        
        if not all(col in df.columns for col in required_columns):
            st.error("❌ Arquivo com colunas incompletas. Verifique a estrutura esperada.")
            return
        
        # Salvar no data_manager para compartilhar entre páginas
        set_dados_upload(df)
        
        dados_json = df.to_dict('records')
        
        try:
            response = requests.post(
                'http://localhost:5000/api/upload',
                json={'data': dados_json},
                timeout=10
            )
            
            if response.status_code == 200:
                st.session_state.dados_carregados = dados_json
                st.success("✅ Dados carregados com sucesso no sistema!")
                st.balloons()
            else:
                st.warning("⚠️ Dados carregados localmente (Backend indisponível)")
                st.session_state.dados_carregados = dados_json
                
        except requests.exceptions.RequestException:
            st.warning("⚠️ Dados carregados localmente (Backend indisponível)")
            st.session_state.dados_carregados = dados_json
    
    except Exception as e:
        st.error(f"❌ Erro ao processar dados: {str(e)}")


def dados_carregados():
    if 'dados_carregados' not in st.session_state or not st.session_state.dados_carregados:
        st.info("ℹ️ Nenhum dado carregado ainda. Faça upload na aba anterior.")
        return
    
    df_display = pd.DataFrame(st.session_state.dados_carregados)
    
    st.markdown(f"#### Total de Registros: {len(df_display)}")
    
    col_stats1, col_stats2, col_stats3 = st.columns(3)
    with col_stats1:
        st.metric("Categorias", df_display['CATEGORIA'].nunique())
    with col_stats2:
        st.metric("Produtos", df_display['PRODUTO'].nunique())
    with col_stats3:
        st.metric("Períodos", df_display['MES'].nunique())
    
    st.markdown("---")
    st.dataframe(df_display, use_container_width=True)
    
    if st.button("🗑️ Limpar Dados", use_container_width=True):
        st.session_state.dados_carregados = None
        st.rerun()


def gerar_template():
    meses = ['janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho',
             'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
    
    categorias = [
        {'COD': 'CAT001', 'NOME': 'Credito PF'},
        {'COD': 'CAT002', 'NOME': 'Credito PJ'},
        {'COD': 'CAT003', 'NOME': 'Investimentos'}
    ]
    
    produtos = [
        {'COD': 'PRD001', 'NOME': 'Credito Pessoal'},
        {'COD': 'PRD002', 'NOME': 'Emprestimo'},
        {'COD': 'PRD003', 'NOME': 'Fundo de Investimento'}
    ]
    
    dados = []
    for ano in [2025, 2026]:
        for mes_idx, mes in enumerate(meses[:3]):
            for cat in categorias:
                for prod in produtos:
                    dados.append({
                        'DATA_COMPLETA': f'15/{mes_idx+1:02d}/{ano}',
                        'MES': mes,
                        'ANO': str(ano),
                        'COD_CATEGORIA': cat['COD'],
                        'CATEGORIA': cat['NOME'],
                        'COD_PRODUTO': prod['COD'],
                        'PRODUTO': prod['NOME'],
                        'CURVA_REALIZADO': np.random.randint(100000, 1000000),
                        'PROJETADO_ANALITICO': np.random.randint(100000, 1000000),
                        'PROJETADO_MERCADO': np.random.randint(100000, 1000000),
                        'PROJETADO_AJUSTADO': np.random.randint(100000, 1000000)
                    })
    
    df_template = pd.DataFrame(dados)
    
    with st.spinner('Gerando template...'):
        try:
            from openpyxl import Workbook
            from openpyxl.styles import PatternFill, Alignment
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Dados"
            
            header_fill = PatternFill(start_color="0c3a66", end_color="0c3a66", fill_type="solid")
            header_font_color = "FFFFFF"
            
            for col_idx, col_name in enumerate(df_template.columns, 1):
                cell = ws.cell(row=1, column=col_idx, value=col_name)
                cell.fill = header_fill
            
            for row_idx, row in enumerate(df_template.values, 2):
                for col_idx, value in enumerate(row, 1):
                    ws.cell(row=row_idx, column=col_idx, value=value)
            
            for col in ws.columns:
                max_length = 15
                ws.column_dimensions[col[0].column_letter].width = max_length
            
            wb.save('template_dados.xlsx')
            
            with open('template_dados.xlsx', 'rb') as f:
                st.download_button(
                    label="📥 Baixar Template",
                    data=f.read(),
                    file_name="template_dados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Erro ao gerar template: {e}")
