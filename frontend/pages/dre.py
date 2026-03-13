"""
Página de DRE Gerencial (Demonstrativo de Resultado Gerencial)
Permite simular e editar variáveis da DRE com layout mês-a-mês
Suporta metodologias de cálculo automáticas
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

# Importar utilitários
from utils_ext.css import make_stylesheet
from utils_ext.formatters import fmt_br
from utils_ext.series import (
    _norm_txt, _mes_to_num, _variacao_mensal
)
from utils_ext.constants import (
    MESES_FULL, MESES_NUM, MESES_ABR, MESES_ABR_LIST, COR_ANALITICA, COR_MERCADO, 
    COR_AJUSTADA, COR_RLZD_BASE, CAT_COLORS
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_manager import get_dados_upload, carregar_curva_ajustada


# ============================================================================
# ESTRUTURA DA DRE
# ============================================================================

class EstruturaLinehaDRE:
    """Representa uma linha da DRE (variável ou totalizador)"""
    
    def __init__(self, codigo: str, descricao: str, tipo: str = "variavel", 
                 formula: str = None, valores: list = None, eh_negrito: bool = False):
        """
        Args:
            codigo: Código único (ex: 'TD71', 'MFB')
            descricao: Descrição legível
            tipo: 'variavel' (editável) ou 'totalizador' (calculado)
            formula: Fórmula de cálculo (ex: '=TD71+TD72' ou '=0.05*TD21')
            valores: Lista com 12 valores mensais [jan...dez]
            eh_negrito: Se True, a linha fica em negrito (totalizador/agrupador)
        """
        self.codigo = codigo
        self.descricao = descricao
        self.tipo = tipo  # 'variavel', 'totalizador', 'agrupador'
        self.formula = formula
        self.valores = valores or [0.0] * 12
        self.eh_negrito = eh_negrito
        self.metodologia = None  # Referência à metodologia aplicada


# ============================================================================
# ESTRUTURA DA DRE (baseado no PDF)
# ============================================================================

ESTRUTURA_DRE = [
    # ===== RECEITA =====
    EstruturaLinehaDRE("TD71", "Receita Financeira", tipo="variavel"),
    EstruturaLinehaDRE("TD72", "Despesa Financeira", tipo="variavel"),
    EstruturaLinehaDRE("TD90", "Receita de Oportunidade", tipo="variavel"),
    EstruturaLinehaDRE("TD91", "Despesa de Oportunidade", tipo="variavel"),
    EstruturaLinehaDRE("TD70", "Variação Cambial", tipo="variavel"),
    
    # ===== SPREAD E AJUSTES =====
    EstruturaLinehaDRE("TD87", "Spread Contrato Câmbio", tipo="variavel", eh_negrito=False),
    EstruturaLinehaDRE("TD88", "Alienação Ativos Financeiros", tipo="variavel", eh_negrito=False),
    EstruturaLinehaDRE("TD95", "Resultado Descasamentos", tipo="variavel", eh_negrito=False),
    EstruturaLinehaDRE("TD96", "Ajuste Oportunidade", tipo="variavel", eh_negrito=False),
    EstruturaLinehaDRE("TD97", "Valor Justo", tipo="variavel", eh_negrito=False),
    
    # ===== MARGEM BRUTA =====
    EstruturaLinehaDRE("MFB", "Margem Financeira Bruta", tipo="totalizador", 
                       formula="=TD71+TD72+TD90+TD91+TD70+TD87+TD88+TD95+TD96+TD97", 
                       eh_negrito=True),
    
    # ===== RECEITA/CUSTO DIFERIDO =====
    EstruturaLinehaDRE("TD11", "Receita Diferida", tipo="variavel"),
    EstruturaLinehaDRE("TD12", "Custo Diferido", tipo="variavel"),
    
    # ===== MARGEM BRUTA EFETIVA =====
    EstruturaLinehaDRE("MFBE", "Margem Financeira Bruta Efetiva", tipo="totalizador",
                       formula="=MFB+TD11+TD12",
                       eh_negrito=True),
    
    # ===== PROVISÕES E AJUSTES =====
    EstruturaLinehaDRE("TD76", "Provisão Perda Esperada", tipo="variavel"),
    EstruturaLinehaDRE("TD16", "Provisão Perda Esperada - Crédito Liberar", tipo="variavel"),
    EstruturaLinehaDRE("TD92", "Recuperação de Perdas", tipo="variavel"),
    EstruturaLinehaDRE("TD81", "Abatimento Negocial", tipo="variavel"),
]


# ============================================================================
# INICIALIZAR ESTADOS
# ============================================================================

def _init_dre_state():
    """Inicializa estados da página DRE no session_state"""
    
    if "dre_dados" not in st.session_state:
        # Carrega ou cria dados padrão da DRE
        st.session_state.dre_dados = {}
        for linha in ESTRUTURA_DRE:
            st.session_state.dre_dados[linha.codigo] = {
                "descricao": linha.descricao,
                "tipo": linha.tipo,
                "formula": linha.formula,
                "valores": linha.valores.copy(),
                "eh_negrito": linha.eh_negrito,
                "metodologia": linha.metodologia,
            }
        
        # Carregar TD71 da simulação se disponível
        _carregar_td71_simulacao()
    
    if "dre_metodologias" not in st.session_state:
        st.session_state.dre_metodologias = {}
    
    if "dre_filtros" not in st.session_state:
        st.session_state.dre_filtros = {
            "cliente": "Todos",
            "categoria": "",
            "produto": ""
        }
    
    # Inicializar dicionário de DREs salvas se não existir
    if "dre_salvas" not in st.session_state:
        st.session_state.dre_salvas = {}


def _carregar_td71_simulacao(cliente: str = "Todos", categoria: str = "", produto: str = ""):
    """
    Carrega valores de TD71 a partir da curva ajustada salva no simulador.
    Tenta em ordem:
    1. Carregar curva persistida para cliente/categoria/produto
    2. Carregar de st.session_state.ajustada (se usuário passou pelo simulador)
    3. Deixar em zero
    """
    try:
        # 1. Tentar carregar curva persistida para essa combinação específica
        if cliente or categoria or produto:
            curva_persistida = carregar_curva_ajustada(cliente, categoria, produto)
            if curva_persistida and len(curva_persistida) == 12:
                st.session_state.dre_dados["TD71"]["valores"] = list(curva_persistida)
                print(f"[DRE] TD71 carregado de curva persistida: {cliente}::{categoria}::{produto}")
                return
        
        # 2. Tentar carregar do session_state do simulador (usuário veio direto do simulador)
        ajustada = st.session_state.get("ajustada", None)
        if ajustada and len(ajustada) == 12:
            st.session_state.dre_dados["TD71"]["valores"] = list(ajustada)
            print("[DRE] TD71 sincronizado com simulador (session_state.ajustada)")
            return
        
        # 3. Se nada funcionar, deixa em zero (será preenchido manualmente)
        print("[DRE] Nenhuma curva ajustada encontrada para TD71 - valores em zero")
        
    except Exception as e:
        print(f"[DRE] Erro ao carregar TD71: {e}")


# ============================================================================
# CÁLCULOS
# ============================================================================

def _calcular_totalizadores():
    """Calcula linhas do tipo 'totalizador' baseado nas fórmulas"""
    dre_dados = st.session_state.dre_dados
    
    for linha in ESTRUTURA_DRE:
        if linha.tipo == "totalizador" and linha.formula:
            # Avaliar a fórmula
            valores_novos = _avaliar_formula(linha.formula, dre_dados)
            dre_dados[linha.codigo]["valores"] = valores_novos
    
    st.session_state.dre_dados = dre_dados


def _avaliar_formula(formula: str, dre_dados: dict) -> list:
    """
    Avalia uma fórmula como '=TD71+TD72' ou '=0.05*TD71'
    Retorna lista com 12 valores mensais
    
    Args:
        formula: String com fórmula (ex: '=TD71+TD72')
        dre_dados: Dicionário com dados da DRE
        
    Returns:
        Lista com 12 valores calculados
    """
    if not formula or not formula.startswith("="):
        return [0.0] * 12
    
    formula_limpa = formula[1:]  # Remove '='
    
    # Preparar contexto: {codigo: [12 valores]}
    contexto = {}
    for codigo, dados in dre_dados.items():
        valores = dados.get("valores", [0.0] * 12)
        contexto[codigo] = valores
    
    # Avaliar a fórmula para cada mês
    valores_resultado = []
    
    for mes_idx in range(12):
        # Construir expressão para este mês específico
        # Substituir códigos de variáveis pelos valores do mês
        expr = formula_limpa
        
        # Ordenar por comprimento decrescente para evitar conflitos
        # Ex: TD70 não seja substituído quando fazemos replace em TD701
        codigos_ordenados = sorted(contexto.keys(), key=len, reverse=True)
        
        for codigo in codigos_ordenados:
            valor_mes = contexto[codigo][mes_idx]
            # Envolver em float() para garantir operações matemáticas
            expr = expr.replace(codigo, f"float({valor_mes})")
        
        try:
            resultado = eval(expr)
            valores_resultado.append(float(resultado))
            print(f"[DRE] Fórmula '{formula}' mês {mes_idx}: {resultado}")
        except Exception as e:
            print(f"[DRE] Erro ao avaliar fórmula '{formula}' mês {mes_idx}: {e}")
            valores_resultado.append(0.0)
    
    return valores_resultado


# ============================================================================
# PERSISTÊNCIA
# ============================================================================

def salvar_dre_usuario():
    """
    Salva dados da DRE para o usuário atual no session_state.
    Isso permite que os dados persistam entre navegações de página.
    """
    usuario = st.session_state.get("usuario", "anonimo")
    filtros = st.session_state.get("dre_filtros", {})
    dre_dados = st.session_state.get("dre_dados", {})
    dre_metodologias = st.session_state.get("dre_metodologias", {})
    
    # Cria chave única para esta combinação cliente/categoria/produto
    combo_key = f"{filtros.get('cliente', 'Todos')}::{filtros.get('categoria', '')}::{filtros.get('produto', '')}"
    
    # Inicializa dicionário de DREs salvas se não existir
    if "dre_salvas" not in st.session_state:
        st.session_state.dre_salvas = {}
    
    if usuario not in st.session_state.dre_salvas:
        st.session_state.dre_salvas[usuario] = {}
    
    # Salva dados da DRE
    st.session_state.dre_salvas[usuario][combo_key] = {
        "cliente": filtros.get("cliente", "Todos"),
        "categoria": filtros.get("categoria", ""),
        "produto": filtros.get("produto", ""),
        "dre_dados": dre_dados,
        "dre_metodologias": dre_metodologias,
        "data_salvo": datetime.now().isoformat(),
    }
    
    print(f"[DRE] Salva para usuário {usuario}: {combo_key}")
    st.success(f"✅ DRE salva com sucesso para {filtros.get('produto', 'Sem produto')}!")


def carregar_dre_usuario(cliente: str, categoria: str, produto: str):
    """
    Carrega dados da DRE do usuário se existirem para esta combinação.
    
    Args:
        cliente, categoria, produto: Filtros para localizar a DRE
        
    Returns:
        Dicionário com dre_dados e dre_metodologias, ou None
    """
    usuario = st.session_state.get("usuario", "anonimo")
    combo_key = f"{cliente}::{categoria}::{produto}"
    
    try:
        dre_salvas = st.session_state.get("dre_salvas", {}).get(usuario, {})
        dre_salva = dre_salvas.get(combo_key, None)
        
        if dre_salva:
            print(f"[DRE] Carregada para usuário {usuario}: {combo_key}")
            return dre_salva
        else:
            print(f"[DRE] Nenhuma DRE salva para: {combo_key}")
            return None
    except Exception as e:
        print(f"[DRE] Erro ao carregar: {e}")
        return None



# ============================================================================
# RENDERIZAÇÃO
# ============================================================================

def renderizar():
    """Renderiza a página de DRE Gerencial"""
    
    _init_dre_state()
    
    # ===== HEADER =====
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0c3a66 0%, #06b6d4 100%); 
                padding: 24px; border-radius: 12px; margin-bottom: 24px;
                box-shadow: 0 8px 16px rgba(0,0,0,0.1);">
        <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 800;">
            📊 DRE Gerencial - Demonstrativo de Resultado
        </h1>
        <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 13px;">
            Simule e projete os componentes do Demonstrativo de Resultado Gerencial
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== FILTROS (Cliente, Categoria, Produto) =====
    # Carregar dados para filtros
    df_upload = get_dados_upload()
    
    col_cli, col_cat, col_prod, col_ano, col_modo, col_btn = st.columns([1.2, 1.2, 1.5, 1, 1, 1])
    
    # Cliente
    with col_cli:
        clientes = ["Todos"]
        if df_upload is not None and "TIPO_CLIENTE" in df_upload.columns:
            cli_list = sorted([c for c in df_upload["TIPO_CLIENTE"].dropna().astype(str).unique() if c.strip() != ""])
            clientes.extend(cli_list)
        
        cliente_sel = st.selectbox(
            "👤 Cliente",
            clientes,
            index=0,
            key="dre_cliente_filter",
            label_visibility="collapsed"
        )
        st.session_state.dre_filtros["cliente"] = cliente_sel
    
    # Categoria
    with col_cat:
        categorias = [""]
        if df_upload is not None and "CATEGORIA" in df_upload.columns:
            df_cli = df_upload if cliente_sel == "Todos" else df_upload[df_upload["TIPO_CLIENTE"].astype(str) == cliente_sel]
            cat_list = sorted([c for c in df_cli["CATEGORIA"].dropna().astype(str).unique() if c.strip() != ""])
            categorias = [""] + cat_list
        
        categoria_sel = st.selectbox(
            "📁 Categoria",
            categorias,
            index=0,
            key="dre_categoria_filter",
            label_visibility="collapsed"
        )
        st.session_state.dre_filtros["categoria"] = categoria_sel
    
    # Produto
    with col_prod:
        produtos = [""]
        if df_upload is not None and categoria_sel and "CATEGORIA" in df_upload.columns:
            df_cat = df_upload[df_upload["CATEGORIA"].astype(str) == categoria_sel]
            prod_list = sorted([p for p in df_cat["PRODUTO"].dropna().astype(str).unique() if p.strip() != ""][:10])
            produtos = [""] + prod_list
        
        produto_sel = st.selectbox(
            "📦 Produto",
            produtos,
            index=0,
            key="dre_produto_filter",
            label_visibility="collapsed"
        )
        st.session_state.dre_filtros["produto"] = produto_sel
    
    # Ano
    with col_ano:
        ano_sel = st.selectbox(
            "📅 Ano",
            [2024, 2025, 2026, 2027],
            index=2,
            key="dre_ano_filter",
            label_visibility="collapsed"
        )
    
    # Modo Visualização
    with col_modo:
        modo_viz = st.toggle(
            "🔒 Viz",
            value=False,
            key="dre_modo_visualizacao",
            label_visibility="collapsed"
        )
    
    # Botão Salvar
    with col_btn:
        if st.button("💾 Salvar", use_container_width=True, type="primary"):
            salvar_dre_usuario()
    
    # ===== SINCRONIZAR TD71 COM OS FILTROS SELECIONADOS =====
    # Carrega a curva ajustada para a combinação cliente/categoria/produto selecionada
    _carregar_td71_simulacao(cliente_sel, categoria_sel, produto_sel)
    
    st.divider()
    
    # ===== ABAS =====
    tab_editor, tab_metodologias, tab_analise = st.tabs([
        "📝 Editor DRE",
        "🔧 Metodologias",
        "📈 Análise"
    ])
    
    with tab_editor:
        _renderizar_editor_dre()
    
    with tab_metodologias:
        _renderizar_metodologias()
    
    with tab_analise:
        _renderizar_analise()


def _renderizar_editor_dre():
    """Renderiza o editor principal da DRE com layout tabular profissional"""
    
    st.markdown("### 📋 Estrutura da DRE - Projeção Mensal (2026)")
    
    dre_dados = st.session_state.dre_dados
    modo_viz = st.session_state.get("dre_modo_visualizacao", False)
    
    # Preparar dados para exibição
    dados_tabela = []
    for linha in ESTRUTURA_DRE:
        codigo = linha.codigo
        dados = dre_dados.get(codigo, {})
        eh_negrito = dados.get("eh_negrito", False)
        tipo = dados.get("tipo", "variavel")
        valores_linha = dados.get("valores", [0.0] * 12)
        
        dados_tabela.append({
            "codigo": codigo,
            "descricao": dados.get("descricao", ""),
            "eh_negrito": eh_negrito,
            "tipo": tipo,
            "valores": valores_linha,
        })
    
    # ===== RENDERIZAR TABELA COM HTML/CSS =====
    st.markdown("""
    <style>
    .dre-tabela {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 13px;
    }
    .dre-tabela th {
        background: linear-gradient(135deg, #0c3a66 0%, #06b6d4 100%);
        color: white;
        font-weight: 600;
        padding: 12px 8px;
        text-align: center;
        border: 1px solid #0a2847;
    }
    .dre-tabela th.codigo-col { text-align: left; width: 60px; }
    .dre-tabela th.desc-col { text-align: left; width: 240px; }
    .dre-tabela th.mes-col { width: 45px; }
    
    .dre-tabela td {
        padding: 10px 8px;
        border: 1px solid #e2e8f0;
    }
    .dre-tabela td.codigo-col {
        font-weight: 600;
        color: #0c3a66;
    }
    .dre-tabela td.desc-col {
        color: #334155;
    }
    .dre-tabela td.mes-col {
        text-align: right;
        padding-right: 12px;
    }
    
    .dre-tabela tbody tr {
        background-color: #ffffff;
        transition: background-color 0.2s;
    }
    .dre-tabela tbody tr:hover {
        background-color: #f0f9ff;
    }
    .dre-tabela tbody tr.negrito {
        background: linear-gradient(90deg, #fce7f3 0%, #f8fafc 100%);
        font-weight: 600;
        border-top: 2px solid #f9a8d4;
        border-bottom: 2px solid #f9a8d4;
    }
    .dre-tabela tbody tr.negrito td {
        color: #c026d3;
    }
    .dre-tabela tbody tr:nth-child(odd) {
        background-color: #fafbfc;
    }
    .dre-tabela tbody tr:nth-child(odd):hover {
        background-color: #eff6ff;
    }
    .dre-input-valor {
        width: 100%;
        border: none;
        background: transparent;
        text-align: right;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ===== CRIAR ESTRUTURA DA TABELA =====
    html_table = '<table class="dre-tabela"><thead><tr>'
    html_table += '<th class="codigo-col">TD</th>'
    html_table += '<th class="desc-col">Descrição</th>'
    
    for mes in MESES_ABR_LIST:
        html_table += f'<th class="mes-col">{mes}</th>'
    
    html_table += '</tr></thead><tbody>'
    
    # ===== PREENCHER DADOS =====
    for i, linha_data in enumerate(dados_tabela):
        codigo = linha_data["codigo"]
        descricao = linha_data["descricao"]
        eh_negrito = linha_data["eh_negrito"]
        tipo = linha_data["tipo"]
        valores = linha_data["valores"]
        
        classe_linha = "negrito" if eh_negrito else ""
        html_table += f'<tr class="{classe_linha}">'
        
        # Código
        html_table += f'<td class="codigo-col">{codigo}</td>'
        
        # Descrição
        html_table += f'<td class="desc-col">{descricao}</td>'
        
        # Valores dos meses
        for mes_idx in range(12):
            valor = valores[mes_idx]
            
            if tipo == "variavel" and not modo_viz:
                # Input editável (usar st.number_input dentro de coluna)
                html_table += f'<td class="mes-col" id="cell_{codigo}_{mes_idx}"></td>'
            else:
                # Apenas visualização
                valor_formatado = fmt_br(valor) if valor != 0 else "0"
                html_table += f'<td class="mes-col">{valor_formatado}</td>'
        
        html_table += '</tr>'
    
    html_table += '</tbody></table>'
    st.markdown(html_table, unsafe_allow_html=True)
    
    # ===== INPUTS EDITÁVEIS (renderizar após a tabela para melhor UX) =====
    if not modo_viz:
        st.markdown("---")
        st.markdown("#### ✏️ Editar Valores")
        
        for linha_data in dados_tabela:
            codigo = linha_data["codigo"]
            tipo = linha_data["tipo"]
            
            if tipo == "variavel":
                with st.expander(f"📝 {codigo} - {linha_data['descricao']}", expanded=False):
                    valores_atual = dre_dados[codigo]["valores"]
                    
                    cols = st.columns(12)
                    for mes_idx, mes in enumerate(MESES_ABR_LIST):
                        with cols[mes_idx]:
                            novo_valor = st.number_input(
                                mes,
                                value=float(valores_atual[mes_idx]),
                                format="%.2f",
                                key=f"input_{codigo}_{mes_idx}",
                                label_visibility="collapsed",
                                step=100.0
                            )
                            dre_dados[codigo]["valores"][mes_idx] = novo_valor
    
    st.session_state.dre_dados = dre_dados
    _calcular_totalizadores()
    
    # ===== RESUMO EM CARDS =====
    st.markdown("---")
    st.markdown("### 📊 Resumo de Resultado")
    
    dre_dados = st.session_state.dre_dados
    total_mfb = sum(dre_dados.get("MFB", {}).get("valores", []))
    total_mfbe = sum(dre_dados.get("MFBE", {}).get("valores", []))
    total_td71 = sum(dre_dados.get("TD71", {}).get("valores", []))
    total_td11 = sum(dre_dados.get("TD11", {}).get("valores", []))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Margem Bruta", fmt_br(total_mfb))
    
    with col2:
        st.metric("📊 Margem Efetiva", fmt_br(total_mfbe))
    
    with col3:
        st.metric("📈 Receita Financeira", fmt_br(total_td71))
    
    with col4:
        st.metric("📋 Receita Diferida", fmt_br(total_td11))


def _renderizar_metodologias():
    """Renderiza página de configuração de metodologias"""
    
    st.markdown("### 🔧 Configuração de Metodologias")
    st.markdown("""
    As metodologias permitem calcular automaticamente valores de variáveis baseado em fórmulas.
    
    **Exemplos:**
    - Receita de Oportunidade = 5% da Receita Financeira: `=0.05*TD71`
    - Margem Financeira Bruta = Soma de Receitas: `=TD71+TD90+TD70`
    """)
    
    col_novo, col_listar = st.columns([1.2, 1.8], gap="large")
    
    with col_novo:
        st.markdown("#### ➕ Criar Nova Metodologia")
        
        with st.form("form_nova_metodologia", clear_on_submit=True):
            nome_metodologia = st.text_input(
                "Nome da Metodologia",
                placeholder="ex: Despesa 60% Receita",
                label_visibility="collapsed"
            )
            
            descricao_met = st.text_area(
                "Descrição (opcional)",
                placeholder="Descreva o propósito desta metodologia",
                height=60,
                label_visibility="collapsed"
            )
            
            formula_metodologia = st.text_input(
                "Fórmula de Cálculo",
                placeholder="ex: =0.60*TD71 ou =TD71+TD72",
                label_visibility="collapsed",
                help="Use '=' no início e códigos de variáveis (TD71, TD72, etc)"
            )
            
            aplicavel_a = st.multiselect(
                "Aplicável às variáveis (selecione pelo menos 1):",
                [linha.codigo for linha in ESTRUTURA_DRE if linha.tipo == "variavel"],
                help="Escolha quais variáveis receberão o cálculo desta fórmula"
            )
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submitted = st.form_submit_button("✅ Criar", use_container_width=True, type="primary")
            
            if submitted:
                if nome_metodologia and formula_metodologia and aplicavel_a:
                    if not formula_metodologia.startswith("="):
                        st.error("⚠️ A fórmula deve começar com '='")
                    else:
                        # Validar fórmula
                        try:
                            _avaliar_formula(formula_metodologia, st.session_state.dre_dados)
                            
                            # Salvar metodologia
                            nova_met = {
                                "nome": nome_metodologia,
                                "descricao": descricao_met,
                                "formula": formula_metodologia,
                                "aplicavel_a": aplicavel_a,
                                "data_criacao": datetime.now().isoformat()
                            }
                            st.session_state.dre_metodologias[nome_metodologia] = nova_met
                            st.success(f"✅ Metodologia '{nome_metodologia}' criada!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro na fórmula: {str(e)}")
                else:
                    st.error("⚠️ Preencha: Nome, Fórmula e selecione variáveis")
    
    with col_listar:
        st.markdown("#### 📋 Metodologias Salvas")
        metodologias = st.session_state.dre_metodologias
        
        if not metodologias:
            st.info("Nenhuma metodologia criada ainda")
        else:
            for nome, dados in list(metodologias.items()):
                with st.expander(f"📌 {nome}", expanded=False):
                    st.markdown(f"**Fórmula:** `{dados['formula']}`")
                    
                    if dados.get('descricao'):
                        st.markdown(f"**Descrição:** {dados['descricao']}")
                    
                    st.markdown(f"**Aplicável a:** `{', '.join(dados['aplicavel_a'])}`")
                    st.caption(f"Criada em: {dados['data_criacao'][:10]}")
                    
                    col_apply, col_del = st.columns(2)
                    
                    with col_apply:
                        if st.button(f"✨ Aplicar", key=f"apply_met_{nome}", use_container_width=True):
                            try:
                                print(f"\n[DRE] Iniciando aplicação da metodologia '{nome}'...")
                                
                                # Aplicar metodologia às variáveis especificadas
                                dre_dados = st.session_state.dre_dados.copy()
                                
                                print(f"[DRE] Variáveis a atualizar: {dados['aplicavel_a']}")
                                print(f"[DRE] Fórmula: {dados['formula']}")
                                
                                for var_codigo in dados['aplicavel_a']:
                                    if var_codigo in dre_dados:
                                        # Calcular valores usando a fórmula
                                        valores_novo = _avaliar_formula(dados['formula'], dre_dados)
                                        
                                        # Antes de aplicar, mostrar valores antigos
                                        valores_antigos = dre_dados[var_codigo]["valores"][:3]
                                        print(f"[DRE] {var_codigo} ANTES: {valores_antigos}...")
                                        
                                        # Aplicar novos valores
                                        dre_dados[var_codigo]["valores"] = valores_novo
                                        valores_novos = valores_novo[:3]
                                        print(f"[DRE] {var_codigo} DEPOIS: {valores_novos}...")
                                        print(f"[DRE] Metodologia '{nome}' aplicada a {var_codigo}")
                                
                                # Salvar dados no session state
                                st.session_state.dre_dados = dre_dados
                                
                                # ===== RECALCULAR TOTALIZADORES IMEDIATAMENTE =====
                                # Isso garante que MFB e MFBE sejam recalculados com os novos valores
                                print(f"[DRE] Recalculando totalizadores...")
                                _calcular_totalizadores()
                                
                                print(f"[DRE] Aplicação concluída!\n")
                                st.success(f"✅ Aplicado a {len(dados['aplicavel_a'])} variável(is)!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao aplicar: {str(e)}")
                                print(f"[DRE] Erro ao aplicar metodologia: {e}")
                                import traceback
                                traceback.print_exc()
                    
                    with col_del:
                        if st.button(f"🗑️ Deletar", key=f"del_met_{nome}", use_container_width=True):
                            del st.session_state.dre_metodologias[nome]
                            st.success("Metodologia deletada")
                            st.rerun()
    
    # ===== EXEMPLOS DE METODOLOGIAS =====
    st.markdown("---")
    st.markdown("#### 💡 Exemplos Sugeridos")
    
    col_ex1, col_ex2, col_ex3 = st.columns(3)
    
    with col_ex1:
        st.markdown("""
        **Receita Op. = 5% Receita Fin.**
        ```
        =0.05*TD71
        ```
        Aplicável a: **TD90**
        """)
    
    with col_ex2:
        st.markdown("""
        **Despesa = 60% Receita**
        ```
        =0.60*TD71
        ```
        Aplicável a: **TD72**
        """)
    
    with col_ex3:
        st.markdown("""
        **Spread = Receita + Desp**
        ```
        =TD71+TD72
        ```
        Aplicável a: **TD87**
        """)


def _renderizar_analise():
    """Renderiza página de análise com gráficos e métricas"""
    
    st.markdown("### 📊 Análise e Relatórios")
    
    dre_dados = st.session_state.dre_dados
    
    # ===== MÉTRICAS PRINCIPAIS =====
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    td71_total = sum(dre_dados.get("TD71", {}).get("valores", [0]*12))
    td72_total = sum(dre_dados.get("TD72", {}).get("valores", [0]*12))
    mfb_total = sum(dre_dados.get("MFB", {}).get("valores", [0]*12))
    
    with col_m1:
        st.metric(
            "📈 Receita Financeira (TD71)",
            fmt_br(td71_total),
            delta=f"Média: R$ {fmt_br(td71_total/12)}/mês"
        )
    
    with col_m2:
        st.metric(
            "💰 Despesa (TD72)",
            fmt_br(td72_total),
            delta=f"Média: R$ {fmt_br(td72_total/12)}/mês"
        )
    
    with col_m3:
        margem = ((mfb_total / td71_total * 100) if td71_total != 0 else 0)
        st.metric(
            "📊 Margem Financeira",
            f"{margem:.1f}%",
            delta=f"Total: R$ {fmt_br(mfb_total)}"
        )
    
    with col_m4:
        st.metric(
            "📅 Período",
            "12 Meses",
            delta=f"{datetime.now().year}"
        )
    
    st.divider()
    
    # ===== GRÁFICOS =====
    col_grf1, col_grf2 = st.columns(2, gap="large")
    
    with col_grf1:
        st.markdown("#### 📊 Evolução Mensal - Receita vs Despesa")
        
        dados_grafico = pd.DataFrame({
            "Mês": MESES_ABR_LIST,
            "Receita (TD71)": dre_dados.get("TD71", {}).get("valores", [0]*12),
            "Despesa (TD72)": dre_dados.get("TD72", {}).get("valores", [0]*12),
        })
        
        st.line_chart(dados_grafico.set_index("Mês"), use_container_width=True)
    
    with col_grf2:
        st.markdown("#### 💹 Margens - MFB e MFBE")
        
        dados_margens = pd.DataFrame({
            "Mês": MESES_ABR_LIST,
            "MFB": dre_dados.get("MFB", {}).get("valores", [0]*12),
            "MFBE": dre_dados.get("MFBE", {}).get("valores", [0]*12),
        })
        
        st.line_chart(dados_margens.set_index("Mês"), use_container_width=True)
    
    st.divider()
    
    # ===== COMPOSIÇÃO DE RECEITA =====
    st.markdown("#### 💰 Composição da Receita (Total Anual)")
    
    componentes = {
        "Receita Financeira": sum(dre_dados.get("TD71", {}).get("valores", [0]*12)),
        "Receita Oportunidade": sum(dre_dados.get("TD90", {}).get("valores", [0]*12)),
        "Variação Cambial": sum(dre_dados.get("TD70", {}).get("valores", [0]*12)),
    }
    
    # Remover valores zero e negativos
    componentes = {k: v for k, v in componentes.items() if v > 0}
    
    if componentes:
        df_comp = pd.DataFrame(list(componentes.items()), columns=["Componente", "Valor"])
        st.bar_chart(df_comp.set_index("Componente"), use_container_width=True)
    else:
        st.info("Nenhuma receita registrada")
    
    st.divider()
    
    # ===== TABELA DE RESUMO =====
    st.markdown("#### 📋 Resumo Detalhado (Totais Anuais)")
    
    resumo_dados = []
    for linha in ESTRUTURA_DRE:
        codigo = linha.codigo
        valores = dre_dados.get(codigo, {}).get("valores", [0]*12)
        total = sum(valores)
        media = total / 12 if len(valores) > 0 else 0
        tipo = dre_dados.get(codigo, {}).get("tipo", "")
        
        # Mostrar todas as linhas
        resumo_dados.append({
            "Código": f"**{codigo}**" if tipo == "totalizador" else codigo,
            "Descrição": dre_dados.get(codigo, {}).get("descricao", ""),
            "Total Anual": fmt_br(total),
            "Média Mensal": fmt_br(media),
            "Tipo": "📊 Totalizador" if tipo == "totalizador" else "📝 Variável",
        })
    
    df_resumo = pd.DataFrame(resumo_dados)
    
    st.dataframe(
        df_resumo, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Código": st.column_config.TextColumn(width=80),
            "Descrição": st.column_config.TextColumn(width=250),
            "Total Anual": st.column_config.TextColumn(width=120),
            "Média Mensal": st.column_config.TextColumn(width=120),
            "Tipo": st.column_config.TextColumn(width=120),
        }
    )
    
    st.divider()
    
    # ===== EXPORTAÇÃO =====
    st.markdown("#### 💾 Exportar Dados")
    
    col_exp1, col_exp2 = st.columns(2, gap="large")
    
    with col_exp1:
        if st.button("📥 Exportar para JSON", use_container_width=True, key="exp_json"):
            json_data = {
                "data_criacao": datetime.now().isoformat(),
                "filtros": st.session_state.dre_filtros,
                "dre": {}
            }
            
            for linha in ESTRUTURA_DRE:
                json_data["dre"][linha.codigo] = {
                    "descricao": linha.descricao,
                    "tipo": linha.tipo,
                    "valores": dre_dados.get(linha.codigo, {}).get("valores", [0]*12),
                    "formula": dre_dados.get(linha.codigo, {}).get("formula")
                }
            
            st.download_button(
                "⬇️ Download JSON",
                data=json.dumps(json_data, indent=2, ensure_ascii=False),
                file_name=f"dre_gerencial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    with col_exp2:
        if st.button("📥 Exportar para CSV", use_container_width=True, key="exp_csv"):
            csv_lines = ["Código,Descrição,Tipo," + ",".join(MESES_ABR_LIST)]
            
            for linha in ESTRUTURA_DRE:
                valores = dre_dados.get(linha.codigo, {}).get("valores", [0]*12)
                tipo_label = "Totalizador" if linha.tipo == "totalizador" else "Variável"
                csv_lines.append(
                    f"{linha.codigo},{linha.descricao},{tipo_label}," + 
                    ",".join(str(int(v)) for v in valores)
                )
            
            st.download_button(
                "⬇️ Download CSV",
                data="\n".join(csv_lines),
                file_name=f"dre_gerencial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
