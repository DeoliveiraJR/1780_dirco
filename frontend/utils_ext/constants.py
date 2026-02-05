# frontend/utils_ext/constants.py
MESES_FULL = [
    "01 Janeiro","02 Fevereiro","03 Março","04 Abril","05 Maio","06 Junho",
    "07 Julho","08 Agosto","09 Setembro","10 Outubro","11 Novembro","12 Dezembro"
]
MESES_NUM = list(range(1, 13))
MESES_ABR = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
             7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
MESES_ABR_LIST = [MESES_ABR[i] for i in MESES_NUM]

# Paleta (mantida do seu simulador)
COR_ANALITICA   = "#1e3a8a"
COR_MERCADO     = "#f59e0b"
COR_AJUSTADA    = "#14b8a6"
COR_RLZD_BASE   = "#64748b"
COR_MERCADO_L   = "#f59e0b"
COR_ANALITICA_L = "#3b82f6"

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