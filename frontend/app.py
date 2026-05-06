# frontend/app.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
from styles import CORES, CSS_CUSTOM, aplicar_tema
from pages import autenticacao, dashboard, simulador, perfil, upload, dre
from data_manager import init_data_state, get_dados_upload, adicionar_simulacao
from services.aggregations import _carregar_curvas_base

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
                if not produto or produto not in prods_disponiveis:
                    if prods_disponiveis:
                        produto = prods_disponiveis[0]
            
            # Detectar mudança de combo para sincronização em tempo real
            combo_atual = f"{cliente}::{categoria}::{produto}"
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
            
            if df_upload is not None and not df_upload.empty and categoria and produto:
                try:
                    analitica, _, _ = _carregar_curvas_base(df_upload, cliente, categoria, produto)
                    if analitica and len(analitica) >= 12:
                        # Usar valores ajustados se disponíveis E do combo atual, senão usar analítica
                        ajustada = st.session_state.get("ajustada", None)
                        last_combo = st.session_state.get("last_combo", "")
                        
                        # SÓ USAR AJUSTADA se for do mesmo combo
                        if ajustada and len(ajustada) == 12 and last_combo == combo_atual:
                            curva_exibir = ajustada
                        else:
                            curva_exibir = analitica
                        
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
            mult_rotacao = st.slider(
                "Multiplicador de Inclinação (MULT)", 
                min_value=-10.0, 
                max_value=50.0, 
                value=st.session_state.get("sim_rotacionar_curva", 1.0),
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
                key="sim_rotacionar_curva"
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
                    # Função para calcular curva rotacionada
                    def _calcular_curva_rotacionada_sidebar(mult_rot):
                        # Monta a curva analítica atual
                        df_upload = get_dados_upload()
                        cliente_atual = st.session_state.get("filtros", {}).get("cliente", "Todos")
                        categoria_atual = st.session_state.get("filtros", {}).get("categoria", "")
                        produto_atual = st.session_state.get("filtros", {}).get("produto", "")
                        
                        analitica, _, _ = _carregar_curvas_base(df_upload, cliente_atual, categoria_atual, produto_atual)
                        
                        if not analitica or len(analitica) < 12:
                            return None
                        
                        qtd = 12
                        primeiro = analitica[0] if analitica[0] else 0
                        ultimo = analitica[11] if analitica[11] else 0
                        incl = (ultimo - primeiro) / (qtd - 1) if qtd > 1 else 0
                        
                        # Calcula novo ajuste de inclinação (multiplicado pelo fator)
                        incl_novo = incl * mult_rot
                        
                        # Distribui a nova inclinação linearmente ao longo dos 12 meses
                        # Mantém o primeiro valor constante e varia o resto
                        curva_rot = []
                        for i in range(qtd):
                            fator = i / (qtd - 1)  # vai de 0 a 1 ao longo dos 12 meses
                            # Calcula o ajuste incremental baseado na nova inclinação
                            ajuste = fator * (incl_novo - incl)
                            valor = analitica[i] + ajuste
                            curva_rot.append(max(0, valor))
                        
                        return curva_rot
                    
                    # Aplica a rotação
                    curva_rot = _calcular_curva_rotacionada_sidebar(mult_rotacao)
                    if curva_rot:
                        st.session_state["ajustada"] = curva_rot
                        st.session_state["sim_rotacionar_curva"] = mult_rotacao
                        st.success(f"✅ Curva rotacionada com {mult_rotacao:+.2f}x inclinação!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao calcular rotação. Verifique os filtros.")

        st.markdown("---")
        
        # ============== LOGOUT ==============
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