# frontend/app.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
from styles import CORES, CSS_CUSTOM, aplicar_tema
from pages import autenticacao, dashboard, simulador, perfil, upload, dre
from data_manager import (
    init_data_state,
    get_dados_upload,
    get_simulacoes_usuario,
    restaurar_simulacao,
    deletar_simulacao,
)
from services.aggregations import _carregar_curvas_base, _carregar_curvas_por_ano

# Inicializar data state logo no início
init_data_state()

st.set_page_config(
    page_title="UAN Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

aplicar_tema()

# ============= CARREGAMENTO DA LOGO =============
from PIL import Image

logo_path = os.path.join(os.path.dirname(__file__), "images", "logo.png")
logo_image = None
if os.path.exists(logo_path):
    try:
        logo_image = Image.open(logo_path)
    except:
        logo_image = None
# ================================================

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = None

def _norm(s: str) -> str:
    import unicodedata
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.strip().lower()

def _recarregar_opcoes(df, cliente_escolhido):
    """Retorna (categorias, map_cat_prod, df_sub) com base no cliente."""
    dff = df.copy()
    # Garante CLI_N para bases mais antigas
    if "CLI_N" not in dff.columns:
        if "TIPO_CLIENTE" in dff.columns:
            dff["CLI_N"] = dff["TIPO_CLIENTE"].astype(str).apply(_norm)
        elif "TP_CLIENTE" in dff.columns:
            dff["CLI_N"] = dff["TP_CLIENTE"].astype(str).apply(_norm)
        else:
            dff["CLI_N"] = ""

    if cliente_escolhido and cliente_escolhido != "Todos":
        dff = dff[dff["CLI_N"] == _norm(cliente_escolhido)]

    categorias = sorted(dff["CATEGORIA"].dropna().astype(str).unique())
    map_cat_prod = (
        dff.groupby("CATEGORIA")["PRODUTO"]
           .apply(lambda s: sorted(s.dropna().astype(str).unique().tolist()))
           .to_dict()
    )
    return categorias, map_cat_prod, dff

if not st.session_state.autenticado:
    autenticacao.renderizar()
else:
    # ============== INICIALIZAR SESSION STATE ==============
    # Garantir que as chaves necessárias existem
    if "filtros" not in st.session_state:
        st.session_state["filtros"] = {
            "cliente": "Todos",
            "categoria": "",
            "produto": "",
            "nome": "Simulação 2026"
        }
    if "sim_nome" not in st.session_state:
        st.session_state["sim_nome"] = "Simulação 2026"
    
    with st.sidebar:
        # Ocultar navegação padrão (preserva botão de colapsar sidebar)
        st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {display: none;}
            section[data-testid="stSidebar"] > div {padding-top: 2rem;}
        </style>
        """, unsafe_allow_html=True)
        
        # ============== HEADER COM BARRA AZUL GRADIENTE ==============
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0c3a66 0%, #06b6d4 100%); 
                    padding: 20px 10px; 
                    border-radius: 24px; 
                    margin-bottom: 40px;
                    text-align: center;
                    box-shadow: 0 16px 16px rgba(0,0,0,0.15);">
        """, unsafe_allow_html=True)
        
        # Logo centralizada
        if logo_image:
            col_logo = st.columns([0.15, 0.24, 0.15])
            with col_logo[1]:
                # use_container_width para respeitar a coluna
                # st.image(logo_image, use_container_width=True)
                st.image(logo_image)
        else:
            st.markdown('<div style="font-size: 52px; margin: 0;">🏢</div>', unsafe_allow_html=True)
        
        st.markdown("""
            <h1 style="margin: 8px 0 0px 0; color: white; font-size: 32px; 
                       font-weight: 800; letter-spacing: 2px; text-align: center;">
                🌐UAN DASHBOARD
            </h1>
            <p style="margin: 0px; color: #0c3a66; font-size: 14px; 
                      font-weight: 500; text-align: center;">
                🏦 Sistema de Arquitetura de projeções - Dirco
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if not logo_image:
            st.caption("💡 Adicione logo.png em /frontend/images/")
        
        st.markdown('<div style="height: 32px;"></div>', unsafe_allow_html=True)
        
        # ============== USUÁRIO ==============
        usuario_label = (st.session_state.usuario or 'usuario@bb.com.br').split('@')[0].capitalize()
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); 
                    padding: 16px; border-radius: 8px; border-left: 4px solid #06b6d4;
                    margin-bottom: 8px; display: flex; align-items: center; gap: 16px;">
            <div style="width: 52px; height: 52px; 
                        background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); 
                        border-radius: 50%; display: flex; align-items: center;
                        justify-content: center; font-size: 32px; flex-shrink: 0;
                        box-shadow: 0 4px 6px rgba(6, 182, 212, 0.3);">
                👤
            </div>
            <div>
                <p style="margin: 0; font-size: 10px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">USUÁRIO@bb.com.br</p>
                <p style="margin: 4px 0 0 0; font-size: 15px; color: #0c3a66; font-weight: 700;">
                    {usuario_label}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ============== MENU DE NAVEGAÇÃO ==============
        st.markdown("<p style='font-size: 11px; font-weight: 600; color: #94a3b8; margin: 0 0 10px 0;'>📍 NAVEGAÇÃO</p>", unsafe_allow_html=True)
        
        opcoes_menu = [
            ("📊", "Dashboard", "Dashboard"),
            ("🎯", "Simulador", "Simulador"),
            ("📃", "DRE", "DRE Gerencial"),
            ("👤", "Perfil", "Perfil"),
            
            ("📤", "Upload", "Upload de Dados")
        ]
        opcoes_display = {f"{i} {l}": v for (i,l,v) in opcoes_menu}
        pagina = st.radio(
            "Menu Principal",
            list(opcoes_display.values()),
            format_func=lambda x: [k for k, v in opcoes_display.items() if v == x][0],
            label_visibility="collapsed",
            key="nav_radio"
        )
        
        st.markdown("---")
        
        # ============== PARÂMETROS DA SIMULAÇÃO ==============
        with st.expander("⚙️ Parâmetros da Simulação", expanded=True):
            # Função auxiliar para formatar valores em R$ (milhões)
            def fmt_reais(valor):
                """Formata valor em R$ com separador de milhares brasileiro."""
                if valor == 0:
                    return "R$ 0"
                if abs(valor) >= 1_000_000_000:
                    return f"R$ {valor/1_000_000_000:,.2f} bi".replace(",", "X").replace(".", ",").replace("X", ".")
                elif abs(valor) >= 1_000_000:
                    return f"R$ {valor/1_000_000:,.2f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
                else:
                    return f"R$ {valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            # ===== CÁLCULO EM TEMPO REAL DOS PARÂMETROS =====
            # Ler dados e filtros - SEMPRE ATUALIZAR para evitar delay
            df_upload = get_dados_upload()
            
            # Ler filtros atuais (SEMPRE dos widgets do simulador, que são a fonte de verdade)
            filtros_atuais = st.session_state.get("filtros", {})
            cliente = filtros_atuais.get("cliente", "Todos")
            categoria = filtros_atuais.get("categoria", "")
            produto = filtros_atuais.get("produto", "")
            produto_todos = produto == "TODOS"
            
            # Validar e auto-detectar categoria/produto se necessário
            if df_upload is not None and not df_upload.empty:
                # Buscar categorias disponíveis
                cats_disponiveis = []
                if "CATEGORIA" in df_upload.columns:
                    cats_disponiveis = sorted(df_upload["CATEGORIA"].dropna().astype(str).unique())
                
                # Se categoria vazia ou não existe, usar primeira disponível
                if not categoria or categoria not in cats_disponiveis:
                    if cats_disponiveis:
                        categoria = cats_disponiveis[0]
                
                # Buscar produtos da categoria atual
                prods_disponiveis = []
                if categoria and "CATEGORIA" in df_upload.columns and "PRODUTO" in df_upload.columns:
                    prods_disponiveis = sorted(
                        df_upload[df_upload["CATEGORIA"].astype(str) == categoria]["PRODUTO"]
                        .dropna().astype(str).unique()
                    )
                
                # Se produto vazio ou não existe NA CATEGORIA ATUAL, usar primeiro disponível
                if (not produto_todos) and (not produto or produto not in prods_disponiveis):
                    if prods_disponiveis:
                        produto = prods_disponiveis[0]
            
            # Normaliza produto para cálculo (TODOS = agregado da categoria)
            produto_calc = "" if produto_todos else produto
            
            # Detectar mudança de combo para sincronização em tempo real
            combo_atual = f"{cliente}::{categoria}::{produto_calc}"
            combo_anterior = st.session_state.get("_ultimo_combo_sidebar", "")
            
            if combo_atual != combo_anterior:
                # Combo mudou, força atualização dos parâmetros
                st.session_state["_ultimo_combo_sidebar"] = combo_atual
                # Garante que session_state geral também tem o combo atualizado
                st.session_state["_sidebar_sync"] = True
            
            # Calcular curva analítica com base nos filtros ATUAIS
            qtd_meses = 12
            primeiro_pjtd = 0
            ultimo_pjtd = 0
            inclinacao = 0
            incremento_perc = 0.0
            
            if df_upload is not None and not df_upload.empty and categoria:
                try:
                    from datetime import datetime

                    ano_atual = datetime.now().year
                    ano_proximo = ano_atual + 1

                    ana_ano_atual, _, _ = _carregar_curvas_por_ano(
                        df_upload,
                        cliente,
                        categoria,
                        produto_calc,
                        ano_atual,
                    )
                    ana_ano_proximo, _, _ = _carregar_curvas_por_ano(
                        df_upload,
                        cliente,
                        categoria,
                        produto_calc,
                        ano_proximo,
                    )

                    analitica_24 = (ana_ano_atual[:] + ana_ano_proximo[:])[:24]
                    if not analitica_24 or len(analitica_24) < 12:
                        analitica_base, _, _ = _carregar_curvas_base(
                            df_upload,
                            cliente,
                            categoria,
                            produto_calc,
                        )
                        analitica_24 = (analitica_base[:] + analitica_base[:])[:24]

                    if analitica_24 and len(analitica_24) >= 12:
                        # Usar valores ajustados se disponíveis E do combo atual, senão usar analítica
                        ajustada = st.session_state.get("ajustada", None)
                        last_combo = st.session_state.get("last_combo", "")
                        
                        # SÓ USAR AJUSTADA se for do mesmo combo
                        if ajustada and len(ajustada) >= 12 and last_combo == combo_atual:
                            curva_exibir = ajustada[:12]
                        else:
                            curva_exibir = analitica_24[:12]
                        
                        primeiro_pjtd = curva_exibir[0] if curva_exibir[0] else 0
                        ultimo_pjtd = curva_exibir[11] if curva_exibir[11] else 0
                        # Inclinação = (último - primeiro) / (qtd_meses - 1)
                        if qtd_meses > 1:
                            inclinacao = (ultimo_pjtd - primeiro_pjtd) / (qtd_meses - 1)
                        
                        # Incremento (%) = AVERAGE das variações percentuais absolutas mensais
                        # Fórmula: P%[mês] = ABS(Valor[mês] - Valor[mês-1]) / Valor[mês]
                        variacoes = []
                        for i in range(1, 12):  # Mês 2 a 12 (índices 1 a 11)
                            valor_atual = curva_exibir[i]
                            valor_anterior = curva_exibir[i - 1]
                            if valor_atual and valor_atual != 0:
                                var_perc = abs(valor_atual - valor_anterior) / valor_atual
                                variacoes.append(var_perc)
                        
                        if variacoes:
                            incremento_perc = sum(variacoes) / len(variacoes)
                except Exception:
                    pass
            
            # Atualizar session_state para uso em outras partes
            st.session_state["sim_qtd_meses"] = qtd_meses
            st.session_state["sim_primeiro_pjtd"] = primeiro_pjtd
            st.session_state["sim_ultimo_pjtd"] = ultimo_pjtd
            st.session_state["sim_inclinacao"] = inclinacao
            st.session_state["sim_incremento_perc"] = incremento_perc
            
            # Estilos CSS para campos informativos
            st.markdown("""
            <style>
                .param-info-card {
                    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
                    border-radius: 8px;
                    padding: 10px 12px;
                    margin-bottom: 8px;
                    border-left: 3px solid #06b6d4;
                }
                .param-label {
                    font-size: 11px;
                    color: #64748b;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin: 0;
                }
                .param-value {
                    font-size: 14px;
                    color: #0c3a66;
                    font-weight: 700;
                    margin: 4px 0 0 0;
                }
            </style>
            """, unsafe_allow_html=True)
            
            # --- CAMPOS INFORMATIVOS ---
            st.markdown(f"""
            <div class="param-info-card">
                <p class="param-label">📅 Qtd. Meses</p>
                <p class="param-value">{qtd_meses}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="param-info-card">
                <p class="param-label">📈 Primeiro mês pjtd.</p>
                <p class="param-value">{fmt_reais(primeiro_pjtd)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="param-info-card">
                <p class="param-label">📉 Último mês pjtd.</p>
                <p class="param-value">{fmt_reais(ultimo_pjtd)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="param-info-card">
                <p class="param-label">📐 Inclinação</p>
                <p class="param-value">{fmt_reais(inclinacao)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="param-info-card">
                <p class="param-label">📊 Incremento (%)</p>
                <p class="param-value">{incremento_perc:.2%}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
            
            # --- SEÇÃO DE ROTAÇÃO DE CURVA ---
            st.markdown("<p style='font-size: 11px; font-weight: 600; color: #94a3b8; margin: 0 0 8px 0;'>🔄 ROTACIONAR CURVA</p>", unsafe_allow_html=True)
            
            # Slider para multiplicador de inclinação com range EXTREMAMENTE AUMENTADO para impacto visual máximo
            # Carrega o último valor aplicado (persistido em chave privada)
            valor_inicial_slider = st.session_state.get("_sim_rotacionar_curva_aplicado", 1.0)
            mult_rotacao = st.slider(
                "Multiplicador de Inclinação (MULT)", 
                min_value=-10.0, 
                max_value=50.0, 
                value=valor_inicial_slider,
                step=1.0,
                help="""
                Controla o multiplicador da inclinação da curva:
                • -10.0x a -1.0x: Inverte/reduz significativamente a tendência
                • 0.0x: Curva totalmente plana (sem inclinação)
                • 1.0x: Inclinação original (sem mudança)
                • 10.0x: 10x a inclinação original
                • 25.0x: 25x a inclinação original
                • 50.0x: 50x a inclinação original (impacto máximo)
                """,
                key="sim_rotacionar_mult"
            )
            
            # Exibir indicador visual do multiplicador
            mult_color = "#10b981" if mult_rotacao >= 1.0 else "#ef4444"
            mult_icon = "📈" if mult_rotacao >= 1.0 else "📉"
            
            col_display, col_button = st.columns([1.5, 1])
            with col_display:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {'#f0fdf4' if mult_rotacao >= 1.0 else '#fef2f2'} 0%, #f8fafc 100%); 
                            border-left: 4px solid {mult_color};
                            border-radius: 8px; padding: 12px;
                            margin-bottom: 8px;">
                    <p style="margin: 0; font-size: 10px; color: #64748b; font-weight: 600; text-transform: uppercase;">
                        {mult_icon} VALOR ATUAL
                    </p>
                    <p style="margin: 4px 0 0 0; font-size: 18px; color: {mult_color}; font-weight: 700;">
                        {mult_rotacao:+.2f}x
                    </p>
                    <p style="margin: 4px 0 0 0; font-size: 9px; color: #78716c;">
                        Variação: {(mult_rotacao - 1.0) * 100:+.0f}%
                    </p>
                    <div style="margin-top: 8px; display: flex; gap: 4px; justify-content: space-around;">
                        <button onclick="document.querySelector('[data-testid=stSlider]').style.opacity='0.8'" style="background: #ef4444; color: white; border: none; border-radius: 4px; padding: 4px 8px; font-size: 10px; font-weight: 600; cursor: pointer;">⬇️ -10</button>
                        <button onclick="document.querySelector('[data-testid=stSlider]').style.opacity='0.8'" style="background: #f97316; color: white; border: none; border-radius: 4px; padding: 4px 8px; font-size: 10px; font-weight: 600; cursor: pointer;">⬇️ -5</button>
                        <button onclick="document.querySelector('[data-testid=stSlider]').style.opacity='0.8'" style="background: #10b981; color: white; border: none; border-radius: 4px; padding: 4px 8px; font-size: 10px; font-weight: 600; cursor: pointer;">⬆️ +5</button>
                        <button onclick="document.querySelector('[data-testid=stSlider]').style.opacity='0.8'" style="background: #06b6d4; color: white; border: none; border-radius: 4px; padding: 4px 8px; font-size: 10px; font-weight: 600; cursor: pointer;">⬆️ +10</button>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_button:
                if st.button("✅ Aplicar", use_container_width=True, key="btn_aplicar_rotacao", help="Aplica a rotação à curva ajustada"):
                    # Função para calcular curva rotacionada (SEMPRE 24 MESES: 2026 + 2027)
                    def _calcular_curva_rotacionada_sidebar(mult_rot):
                        # Monta a curva analítica atual
                        df_upload = get_dados_upload()
                        cliente_atual = st.session_state.get("filtros", {}).get("cliente", "Todos")
                        categoria_atual = st.session_state.get("filtros", {}).get("categoria", "")
                        produto_raw = st.session_state.get("filtros", {}).get("produto", "")
                        produto_atual = "" if produto_raw == "TODOS" else produto_raw

                        if df_upload is None or df_upload.empty or not categoria_atual:
                            return None

                        from datetime import datetime
                        ano_atual = datetime.now().year
                        ano_proximo = ano_atual + 1

                        ana_ano_atual, _, _ = _carregar_curvas_por_ano(
                            df_upload,
                            cliente_atual,
                            categoria_atual,
                            produto_atual,
                            ano_atual,
                        )
                        ana_ano_proximo, _, _ = _carregar_curvas_por_ano(
                            df_upload,
                            cliente_atual,
                            categoria_atual,
                            produto_atual,
                            ano_proximo,
                        )

                        analitica = (ana_ano_atual[:] + ana_ano_proximo[:])[:24]
                        if len(analitica) < 12:
                            return None
                        
                        # ==================== CALCULA PARA OS 12 PRIMEIROS MESES ====================
                        qtd = 12
                        primeiro = analitica[0] if analitica[0] else 0
                        ultimo = analitica[11] if analitica[11] else 0
                        incl = (ultimo - primeiro) / (qtd - 1) if qtd > 1 else 0
                        
                        # Calcula novo ajuste de inclinação (multiplicado pelo fator)
                        incl_novo = incl * mult_rot
                        
                        # Distribui a nova inclinação linearmente ao longo dos 12 meses
                        curva_rot_12m = []
                        for i in range(qtd):
                            fator = i / (qtd - 1)  # vai de 0 a 1 ao longo dos 12 meses
                            ajuste = fator * (incl_novo - incl)
                            valor = analitica[i] + ajuste
                            curva_rot_12m.append(max(0, valor))
                        
                        # ==================== EXPANDE PARA 24 MESES ====================
                        # O simulador SEMPRE usa 24 meses (ano atual + próximo ano)
                        curva_rot_24m = curva_rot_12m[:]
                        
                        if len(analitica) >= 24:
                            # Temos dados de 2027, aplica mesma rotação
                            primeiro_2027 = analitica[12] if analitica[12] else 0
                            ultimo_2027 = analitica[23] if analitica[23] else 0
                            incl_2027 = (ultimo_2027 - primeiro_2027) / (qtd - 1) if qtd > 1 else 0
                            incl_novo_2027 = incl_2027 * mult_rot
                            
                            for i in range(qtd):
                                fator = i / (qtd - 1)
                                ajuste = fator * (incl_novo_2027 - incl_2027)
                                valor = analitica[12 + i] + ajuste
                                curva_rot_24m.append(max(0, valor))
                        else:
                            # Sem dados de 2027, replica os 12 primeiros (mesma curva rotacionada)
                            curva_rot_24m.extend(curva_rot_12m[:])
                        
                        return curva_rot_24m if len(curva_rot_24m) == 24 else None
                    
                    # Aplica a rotação
                    curva_rot = _calcular_curva_rotacionada_sidebar(mult_rotacao)
                    if curva_rot:
                        produto_combo = "" if st.session_state.get("filtros", {}).get("produto", "") == "TODOS" else st.session_state.get("filtros", {}).get("produto", "")
                        combo_rot = f"{st.session_state.get('filtros', {}).get('cliente', 'Todos')}::{st.session_state.get('filtros', {}).get('categoria', '')}::{produto_combo}"

                        st.session_state["ajustada"] = curva_rot  # Agora com 24 elementos
                        st.session_state["last_combo"] = combo_rot
                        # Persistir em chave privada (não conflita com widget key)
                        st.session_state["_sim_rotacionar_curva_aplicado"] = mult_rotacao
                        # Também salvar em chave pública para uso no simulador
                        st.session_state["sim_rotacionar_curva"] = mult_rotacao
                        st.success(f"✅ Curva rotacionada com {mult_rotacao:+.2f}x inclinação! (24 meses)")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao calcular rotação. Verifique os filtros.")

        st.markdown("---")
        
        # ============== FILTROS DA SIMULAÇÃO ==============
        with st.expander("🎯 Filtros da Simulação", expanded=True):
            # Função auxiliar para recarregar opções
            def _recarregar_opcoes_sidebar(df, cliente_escolhido):
                """Retorna (categorias, map_cat_prod) com base no cliente."""
                dff = df.copy() if df is not None else pd.DataFrame()
                
                # Normalizar CLI_N
                if "CLI_N" not in dff.columns:
                    if "TIPO_CLIENTE" in dff.columns:
                        dff["CLI_N"] = dff["TIPO_CLIENTE"].astype(str).apply(_norm)
                    elif "TP_CLIENTE" in dff.columns:
                        dff["CLI_N"] = dff["TP_CLIENTE"].astype(str).apply(_norm)
                    else:
                        dff["CLI_N"] = ""
                
                if cliente_escolhido and cliente_escolhido != "Todos":
                    dff = dff[dff["CLI_N"] == _norm(cliente_escolhido)]
                
                categorias = sorted(dff["CATEGORIA"].dropna().astype(str).unique()) if "CATEGORIA" in dff.columns else []
                map_cat_prod = {}
                if "CATEGORIA" in dff.columns and "PRODUTO" in dff.columns:
                    map_cat_prod = (
                        dff.groupby("CATEGORIA")["PRODUTO"]
                           .apply(lambda s: sorted(s.dropna().astype(str).unique().tolist()))
                           .to_dict()
                    )
                return categorias, map_cat_prod
            
            # Callbacks para sincronização
            def _on_cliente_sidebar_change():
                filtros = st.session_state.get("filtros", {})
                filtros["cliente"] = st.session_state.get("sb_sim_cliente", "Todos")
                filtros["categoria"] = ""
                filtros["produto"] = ""
                st.session_state["filtros"] = filtros
            
            def _on_categoria_sidebar_change():
                filtros = st.session_state.get("filtros", {})
                filtros["categoria"] = st.session_state.get("sb_sim_categoria", "")
                filtros["produto"] = ""
                st.session_state["filtros"] = filtros
            
            def _on_produto_sidebar_change():
                filtros = st.session_state.get("filtros", {})
                filtros["produto"] = st.session_state.get("sb_sim_produto", "")
                st.session_state["filtros"] = filtros
            
            # Obter dados
            df_upload_sb = get_dados_upload()
            
            # Opções de clientes
            clientes_opcoes_sb = ["Todos"]
            if isinstance(df_upload_sb, pd.DataFrame) and not df_upload_sb.empty:
                if "TIPO_CLIENTE" in df_upload_sb.columns:
                    clientes_opcoes_sb += sorted([c for c in df_upload_sb["TIPO_CLIENTE"].dropna().astype(str).unique() if c.strip() != ""])
                elif "TP_CLIENTE" in df_upload_sb.columns:
                    clientes_opcoes_sb += sorted([c for c in df_upload_sb["TP_CLIENTE"].dropna().astype(str).unique() if c.strip() != ""])
            
            # --- Nome da Simulação ---
            st.markdown("<p style='font-size: 11px; font-weight: 600; color: #0c3a66; margin: 0 0 6px 0;'>📝 NOME DA SIMULAÇÃO</p>", unsafe_allow_html=True)
            sim_nome_sb = st.text_input(
                "Nome",
                value=st.session_state.get("sim_nome", "Simulação 2026"),
                key="sb_sim_nome",
                label_visibility="collapsed",
                placeholder="Ex: Cenário Otimista Q2"
            )
            if sim_nome_sb:
                st.session_state["sim_nome"] = sim_nome_sb
                filtros = st.session_state.get("filtros", {})
                filtros["nome"] = sim_nome_sb
                st.session_state["filtros"] = filtros
            
            st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
            
            # --- Cliente ---
            st.markdown("<p style='font-size: 11px; font-weight: 600; color: #0c3a66; margin: 0 0 6px 0;'>👤 CLIENTE</p>", unsafe_allow_html=True)
            cliente_mem_sb = st.session_state.get("filtros", {}).get("cliente", "Todos")
            idx_cliente_sb = clientes_opcoes_sb.index(cliente_mem_sb) if cliente_mem_sb in clientes_opcoes_sb else 0
            sim_cliente_sb = st.selectbox(
                "Cliente",
                clientes_opcoes_sb,
                index=idx_cliente_sb,
                key="sb_sim_cliente",
                on_change=_on_cliente_sidebar_change,
                label_visibility="collapsed"
            )
            
            st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
            
            # Recarrega categorias/produtos
            cats_sb, map_cat_prod_sb = _recarregar_opcoes_sidebar(df_upload_sb, sim_cliente_sb)
            
            # --- Categoria ---
            st.markdown("<p style='font-size: 11px; font-weight: 600; color: #0c3a66; margin: 0 0 6px 0;'>📁 CATEGORIA</p>", unsafe_allow_html=True)
            categoria_mem_sb = st.session_state.get("filtros", {}).get("categoria", "")
            idx_cat_sb = cats_sb.index(categoria_mem_sb) if categoria_mem_sb in cats_sb else (0 if cats_sb else None)
            sim_categoria_sb = st.selectbox(
                "Categoria",
                cats_sb,
                index=idx_cat_sb,
                key="sb_sim_categoria",
                on_change=_on_categoria_sidebar_change,
                label_visibility="collapsed"
            )
            
            st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
            
            # --- Produto (com opção TODOS) ---
            st.markdown("<p style='font-size: 11px; font-weight: 600; color: #0c3a66; margin: 0 0 6px 0;'>📦 PRODUTO</p>", unsafe_allow_html=True)
            prds_sb = map_cat_prod_sb.get(sim_categoria_sb, [])
            prds_sb_com_todos = ["TODOS"] + prds_sb if prds_sb else ["TODOS"]
            produto_mem_sb = st.session_state.get("filtros", {}).get("produto", "TODOS")
            idx_prd_sb = prds_sb_com_todos.index(produto_mem_sb) if produto_mem_sb in prds_sb_com_todos else 0
            sim_produto_sb = st.selectbox(
                "Produto",
                prds_sb_com_todos,
                index=idx_prd_sb,
                key="sb_sim_produto",
                on_change=_on_produto_sidebar_change,
                label_visibility="collapsed"
            )
            
            # Atualizar filtro de produto se selecionou TODOS
            if sim_produto_sb == "TODOS":
                filtros = st.session_state.get("filtros", {})
                filtros["produto"] = "TODOS"
                st.session_state["filtros"] = filtros
            
            st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
            
            # --- Botão Salvar ---
            def _salvar_simulacao_sidebar():
                """Dispara o save no fluxo do simulador (com dados completos)."""
                nome_sim = st.session_state.get("sim_nome", "Sem Nome")
                categoria_sim = st.session_state.get("filtros", {}).get("categoria", "")
                
                if not categoria_sim:
                    st.session_state["_save_feedback_msg"] = "⚠️ Selecione uma categoria antes de salvar."
                    return

                if pagina != "Simulador":
                    st.session_state["_save_feedback_msg"] = "⚠️ Abra a página Simulador para salvar a curva atual."
                    return

                filtros = st.session_state.get("filtros", {})
                filtros["nome"] = nome_sim
                st.session_state["filtros"] = filtros
                
                # Flag consumida no simulador para salvar com a curva ajustada atual.
                st.session_state["_trigger_save_simulador"] = True
                st.rerun()
            
            if st.button("💾 Salvar Simulação", use_container_width=True, type="primary", key="sb_btn_salvar"):
                _salvar_simulacao_sidebar()

            feedback_msg = st.session_state.pop("_save_feedback_msg", None)
            if feedback_msg:
                if feedback_msg.startswith("✅"):
                    st.success(feedback_msg)
                else:
                    st.warning(feedback_msg)

        st.markdown("---")
        
        # ============== HISTÓRICO DE SIMULAÇÕES ==============
        simulacoes_usuario_sb = get_simulacoes_usuario()
        
        with st.expander(f"📂 Histórico ({len(simulacoes_usuario_sb)})", expanded=False):
            if not simulacoes_usuario_sb:
                st.info("📋 Nenhuma simulação salva ainda.")
            else:
                # Container com altura máxima e scroll
                st.markdown("""
                <style>
                    .sim-history-container {
                        max-height: 400px;
                        overflow-y: auto;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                        padding: 8px;
                        background: #f8fafc;
                    }
                    .sim-history-item {
                        background: white;
                        border: 1px solid #e2e8f0;
                        border-radius: 6px;
                        padding: 8px;
                        margin-bottom: 6px;
                        font-size: 0.85rem;
                    }
                    .sim-history-item:hover {
                        background: #f1f5f9;
                        border-color: #06b6d4;
                    }
                    .sim-history-name {
                        font-weight: 600;
                        color: #0c3a66;
                        margin: 0 0 4px 0;
                    }
                    .sim-history-meta {
                        font-size: 0.75rem;
                        color: #64748b;
                        display: flex;
                        gap: 8px;
                        margin: 4px 0;
                        flex-wrap: wrap;
                    }
                    .sim-history-actions {
                        display: flex;
                        gap: 4px;
                        margin-top: 6px;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                items_por_pagina = 6
                total_items = len(simulacoes_usuario_sb)
                paginas = (total_items + items_por_pagina - 1) // items_por_pagina
                
                if "_sim_history_page" not in st.session_state:
                    st.session_state["_sim_history_page"] = 0
                
                pagina_atual = st.session_state["_sim_history_page"]
                inicio = pagina_atual * items_por_pagina
                fim = inicio + items_por_pagina
                
                items_paginados = simulacoes_usuario_sb[inicio:fim]
                
                for sim in items_paginados:
                    sim_id = sim.get("id")
                    nome = sim.get("nome", "Sem nome")
                    categoria = sim.get("categoria", "-")
                    produto = sim.get("produto", "-")
                    data_salvo = sim.get("data_salvo", "-")
                    
                    st.markdown(f"""
                    <div class="sim-history-item">
                        <p class="sim-history-name">📌 {nome}</p>
                        <div class="sim-history-meta">
                            <span>📁 {categoria}</span>
                            <span>📦 {produto[:20]}</span>
                            <span>📅 {data_salvo}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_rest, col_del = st.columns(2, gap="small")
                    with col_rest:
                        if st.button("🔄 Restaurar", key=f"sb_rest_{sim_id}", use_container_width=True, size="small"):
                            restaurar_simulacao(sim_id)
                            st.rerun()
                    with col_del:
                        if st.button("🗑️ Excluir", key=f"sb_del_{sim_id}", use_container_width=True, size="small"):
                            deletar_simulacao(sim_id)
                            st.rerun()
                    st.markdown('<div style="height: 2px;"></div>', unsafe_allow_html=True)
                
                # Paginação
                if paginas > 1:
                    st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
                    col_prev, col_info, col_next = st.columns([0.8, 1.4, 0.8])
                    
                    with col_prev:
                        if st.button("⬅️ Ant.", use_container_width=True, disabled=pagina_atual == 0, key="sb_hist_prev"):
                            st.session_state["_sim_history_page"] = pagina_atual - 1
                            st.rerun()
                    
                    with col_info:
                        st.markdown(f"<div style='text-align:center;padding:6px;font-size:0.85rem;color:#64748b;font-weight:600;'>{pagina_atual + 1}/{paginas}</div>", unsafe_allow_html=True)
                    
                    with col_next:
                        if st.button("Prox ➡️", use_container_width=True, disabled=pagina_atual >= paginas - 1, key="sb_hist_next"):
                            st.session_state["_sim_history_page"] = pagina_atual + 1
                            st.rerun()
        
        st.markdown("---")
        col_logout = st.columns([1])[0]
        with col_logout:
            if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                st.session_state.autenticado = False
                st.session_state.usuario = None
                st.rerun()
        
        st.markdown("---")
        
        # ============== FOOTER ==============
        st.markdown("""
        <div style="text-align: center; color: #95a5a6; font-size: 10px; margin-top: 20px;">
            <p style="margin: 5px 0;">UAN Dashboard v1.0.0</p>
            <p style="margin: 5px 0;">(c) 2026 Banco do Brasil (UAN)</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ============== RENDERIZAR PÁGINAS ==============
    if pagina == "Dashboard":
        dashboard.renderizar()
    elif pagina == "Simulador":
        simulador.renderizar()
    elif pagina == "DRE Gerencial":
        dre.renderizar()
    elif pagina == "Perfil":
        perfil.renderizar()
    elif pagina == "Upload de Dados":
        upload.renderizar()