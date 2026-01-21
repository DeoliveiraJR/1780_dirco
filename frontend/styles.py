# Arquivo de estilos e temas para o aplicativo

CORES = {
    "azul_profundo": "#0c3a66",
    "azul_claro": "#1e3a8a",
    "turquesa": "#06b6d4",
    "turquesa_escuro": "#0891b2",
    "rosa": "#ec4899",
    "rosa_escuro": "#db2777",
    "roxo": "#a855f7",
    "roxo_escuro": "#9333ea",
    "branco": "#ffffff",
    "cinza_claro": "#f8fafc",
    "cinza_medio": "#e2e8f0",
    "cinza_escuro": "#475569",
    "sucesso": "#10b981",
    "erro": "#ef4444",
    "aviso": "#f59e0b",
}

CSS_CUSTOM = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

/* Tema geral */
:root {
    --azul-profundo: #0c3a66;
    --azul-claro: #1e3a8a;
    --turquesa: #06b6d4;
    --turquesa-escuro: #0891b2;
    --rosa: #ec4899;
    --roxo: #a855f7;
    --branco: #ffffff;
    --cinza-claro: #f8fafc;
}

/* Background gradient */
body {
    background: linear-gradient(135deg, #0c3a66 0%, #1e3a8a 50%, #0891b2 100%);
    min-height: 100vh;
    color: #1f2937;
}

/* Sidebar */
.css-1d391kg {
    background: linear-gradient(180deg, #0c3a66 0%, #1e3a8a 100%) !important;
    border-right: 3px solid #06b6d4 !important;
}

.css-1d391kg [data-testid="stSidebarNav"] {
    background: transparent !important;
}

/* Cards com sombra elegante */
.element-container div [data-testid="stMetric"] {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border-radius: 12px;
    padding: 20px;
    border-left: 4px solid #06b6d4;
    box-shadow: 0 4px 20px rgba(6, 182, 212, 0.1);
}

/* Botões */
.stButton > button {
    background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(6, 182, 212, 0.5) !important;
}

/* Input fields */
.stTextInput input, .stPasswordInput input {
    border: 2px solid #e2e8f0 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    transition: all 0.3s ease !important;
}

.stTextInput input:focus, .stPasswordInput input:focus {
    border-color: #06b6d4 !important;
    box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1) !important;
}

/* Títulos */
h1, h2, h3 {
    color: #0c3a66 !important;
}

/* Links */
a {
    color: #06b6d4 !important;
    text-decoration: none !important;
}

a:hover {
    color: #0891b2 !important;
    text-decoration: underline !important;
}

/* Animações */
@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.5;
    }
}

.animate-fade-in-down {
    animation: fadeInDown 0.6s ease-out;
}

.animate-fade-in-up {
    animation: fadeInUp 0.6s ease-out;
}

.animate-slide-in-right {
    animation: slideInRight 0.6s ease-out;
}

.animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
"""

def aplicar_tema():
    """Aplica o tema customizado ao app"""
    import streamlit as st
    st.markdown(CSS_CUSTOM, unsafe_allow_html=True)
