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
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Inter:wght@400;500;600;700;800&display=swap');

/* CSS Variables - Design System */
:root {
    /* Cores Primárias */
    --color-primary: #0c3a66;
    --color-primary-light: #1e3a8a;
    --color-primary-dark: #051e34;
    
    /* Cores Accent */
    --color-accent: #06b6d4;
    --color-accent-dark: #0891b2;
    --color-accent-light: #ecf5fc;
    
    /* Status */
    --color-success: #10b981;
    --color-error: #ef4444;
    --color-warning: #f59e0b;
    --color-info: #3b82f6;
    
    /* Neutros */
    --color-white: #ffffff;
    --color-gray-50: #f9fafb;
    --color-gray-100: #f3f4f6;
    --color-gray-200: #e5e7eb;
    --color-gray-300: #d1d5db;
    --color-gray-400: #9ca3af;
    --color-gray-500: #6b7280;
    --color-gray-600: #4b5563;
    --color-gray-700: #374151;
    --color-gray-800: #1f2937;
    --color-gray-900: #111827;
    
    /* Tipografia */
    --font-header: 'Plus Jakarta Sans', sans-serif;
    --font-body: 'Inter', sans-serif;
    --font-size-xs: 0.75rem;
    --font-size-sm: 0.875rem;
    --font-size-md: 1rem;
    --font-size-lg: 1.125rem;
    --font-size-xl: 1.25rem;
    --font-size-2xl: 1.5rem;
    --font-size-3xl: 1.875rem;
    --font-size-4xl: 2.25rem;
    
    /* Espaçamento */
    --spacing-xs: 4px;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;
    --spacing-2xl: 48px;
    
    /* Border Radius */
    --radius-sm: 6px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --radius-full: 9999px;
    
    /* Sombras */
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.1);
    --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1);
    
    /* Transições */
    --transition-fast: 0.15s ease-in-out;
    --transition-base: 0.3s ease-in-out;
    --transition-slow: 0.5s ease-in-out;
}

/* Reset e Base */
* {
    box-sizing: border-box;
}

html, body {
    background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 50%, var(--color-accent-dark) 100%);
    min-height: 100vh;
    color: var(--color-gray-800);
    font-family: var(--font-body);
}

/* Tipografia Base */
body {
    font-size: var(--font-size-md);
    line-height: 1.6;
    letter-spacing: 0.3px;
}

h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-header);
    font-weight: 700;
    color: var(--color-primary);
    margin-bottom: var(--spacing-md);
}

h1 {
    font-size: var(--font-size-4xl);
    font-weight: 800;
    letter-spacing: -0.5px;
}

h2 {
    font-size: var(--font-size-3xl);
    letter-spacing: -0.25px;
}

h3 {
    font-size: var(--font-size-2xl);
}

h4 {
    font-size: var(--font-size-xl);
}

p {
    color: var(--color-gray-700);
    line-height: 1.75;
}

/* Links */
a {
    color: var(--color-accent);
    text-decoration: none;
    transition: color var(--transition-base);
    font-weight: 500;
}

a:hover {
    color: var(--color-accent-dark);
    text-decoration: underline;
}

/* Sidebar Streamlit */
.css-1d391kg {
    background: linear-gradient(180deg, var(--color-primary) 0%, var(--color-primary-light) 100%) !important;
    border-right: 3px solid var(--color-accent) !important;
}

.css-1d391kg [data-testid="stSidebarNav"] {
    background: transparent !important;
}

/* Sidebar Title - UAN DASHBOARD */
[data-testid="stSidebar"] .css-uf99v8 {
    color: var(--color-accent) !important;
}

/* Botões - Garantir texto branco */
.stButton > button {
    background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-dark) 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    padding: 12px 24px !important;
    font-family: var(--font-body) !important;
    font-weight: 700 !important;
    font-size: var(--font-size-sm) !important;
    transition: all var(--transition-base) !important;
    box-shadow: 0 4px 12px rgba(6, 182, 212, 0.3) !important;
    cursor: pointer !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(6, 182, 212, 0.5) !important;
    background: linear-gradient(135deg, var(--color-accent-dark) 0%, #0571a0 100%) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
    box-shadow: 0 4px 12px rgba(6, 182, 212, 0.3) !important;
}

.stButton > button > p, 
.stButton > button > span {
    color: #ffffff !important;
}

/* FORÇA EXTREMA: Garantir texto branco em TODOS os elementos do botão */
.stButton > button * {
    color: #ffffff !important;
}

.stButton > button:not(:disabled):not(.disabled) {
    color: #ffffff !important;
}

.stButton > button:hover,
.stButton > button:active {
    color: #ffffff !important;
}

/* Sidebar - UAN DASHBOARD em turquesa */
[data-testid="stSidebar"] h1 {
    color: #06b6d4 !important;
}

[data-testid="stSidebar"] .css-uf99v8 {
    color: #06b6d4 !important;
}

/* Input Fields */
.stTextInput input, 
.stPasswordInput input,
.stNumberInput input,
.stSelectbox select {
    border: 2px solid var(--color-gray-200) !important;
    border-radius: var(--radius-md) !important;
    padding: 12px 16px !important;
    font-family: var(--font-body) !important;
    font-size: var(--font-size-sm) !important;
    transition: all var(--transition-base) !important;
}

.stTextInput input:focus, 
.stPasswordInput input:focus,
.stNumberInput input:focus {
    border-color: var(--color-accent) !important;
    box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1) !important;
    outline: none !important;
}

/* Métrics Cards */
.element-container div [data-testid="stMetric"] {
    background: linear-gradient(135deg, var(--color-white) 0%, var(--color-gray-50) 100%) !important;
    border-radius: var(--radius-lg) !important;
    padding: 20px !important;
    border-left: 4px solid var(--color-accent) !important;
    box-shadow: var(--shadow-md) !important;
    transition: all var(--transition-base) !important;
}

.element-container div [data-testid="stMetric"]:hover {
    box-shadow: var(--shadow-lg) !important;
    transform: translateY(-2px) !important;
}

/* Expandables/Expanders */
.streamlit-expanderHeader {
    background-color: var(--color-gray-100) !important;
    border-radius: var(--radius-md) !important;
    padding: 12px 16px !important;
    font-weight: 600 !important;
    color: var(--color-primary) !important;
    transition: all var(--transition-base) !important;
}

.streamlit-expanderHeader:hover {
    background-color: var(--color-gray-200) !important;
}

/* Data Editor */
[data-testid="stDataFrame"] {
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
}

/* Divider */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--color-gray-300), transparent);
    margin: var(--spacing-lg) 0;
}

/* Tabelas */
table {
    border-collapse: collapse;
    width: 100%;
    font-size: var(--font-size-sm);
}

table th {
    background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
    color: var(--color-white);
    font-weight: 600;
    padding: var(--spacing-md);
    text-align: left;
    border: 1px solid var(--color-primary-dark);
}

table td {
    padding: var(--spacing-md);
    border: 1px solid var(--color-gray-200);
    background: var(--color-white);
}

table tbody tr:hover {
    background: var(--color-gray-50);
    transition: background var(--transition-base);
}

table tbody tr:nth-child(odd) {
    background: var(--color-gray-50);
}

/* Status Badges */
.badge-success {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
}

.badge-error {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: white;
}

.badge-warning {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
}

.badge-info {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: white;
}

/* Info/Success/Warning/Error */
.element-container [data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
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
        opacity: 0.7;
    }
}

@keyframes shimmer {
    0% {
        background-position: -1000px 0;
    }
    100% {
        background-position: 1000px 0;
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

.animate-shimmer {
    animation: shimmer 2s infinite;
    background: linear-gradient(90deg, var(--color-gray-200) 0%, var(--color-white) 50%, var(--color-gray-200) 100%);
    background-size: 1000px 100%;
}

/* Responsividade */
@media (max-width: 768px) {
    h1 {
        font-size: var(--font-size-3xl);
    }
    
    h2 {
        font-size: var(--font-size-2xl);
    }
    
    h3 {
        font-size: var(--font-size-xl);
    }
    
    .stButton > button {
        padding: 10px 20px !important;
    }
}
</style>
"""

def aplicar_tema():
    """Aplica o tema customizado ao app"""
    import streamlit as st
    st.markdown(CSS_CUSTOM, unsafe_allow_html=True)
