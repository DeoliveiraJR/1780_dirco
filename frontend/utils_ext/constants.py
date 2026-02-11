# frontend/utils_ext/constants.py
MESES_FULL = [
    "01 Janeiro","02 Fevereiro","03 Março","04 Abril","05 Maio","06 Junho",
    "07 Julho","08 Agosto","09 Setembro","10 Outubro","11 Novembro","12 Dezembro"
]
MESES_NUM = list(range(1, 13))
MESES_ABR = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
             7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
MESES_ABR_LIST = [MESES_ABR[i] for i in MESES_NUM]

# Paleta - Tons pasteurizados elegantes
COR_ANALITICA   = "#3b82f6"  # Azul médio (mais visível)
COR_MERCADO     = "#f59e0b"  # Âmbar/Laranja
COR_AJUSTADA    = "#10b981"  # Esmeralda/Verde água
COR_RLZD_BASE   = "#6b7280"  # Cinza neutro
COR_MERCADO_L   = "#fbbf24"  # Amarelo âmbar
COR_ANALITICA_L = "#60a5fa"  # Azul claro

# Paleta de cores por categoria - tons pastel elegantes
CAT_COLORS = {
    "CAPTAÇÕES":         "#5b8def",  # Azul pastel
    "OPERAÇÕES CRÉDITO": "#f6a355",  # Laranja pastel
    "CRÉDITO":           "#e57373",  # Vermelho pastel/coral
    "SERVIÇOS":          "#4db6ac",  # Teal pastel
    "OUTROS":            "#9575cd",  # Roxo pastel
}

# Ícones personalizados por categoria
CAT_ICONS = {
    "CAPTAÇÕES":         "📥",
    "OPERAÇÕES CRÉDITO": "💳",
    "CRÉDITO":           "💰",
    "SERVIÇOS":          "⚙️",
    "OUTROS":            "📦",
}