"""
Sistema de Ícones Elegante para UAN Dashboard
Utiliza Font Awesome 6 via CDN com fallbacks

Uso:
    from utils_ext.icons import get_icon, render_icon_header
    
    # Renderizar ícone simples
    icon_html = get_icon("chart", size="lg", color="#06b6d4")
    st.markdown(icon_html, unsafe_allow_html=True)
    
    # Renderizar header com ícone
    render_icon_header("Meu Título", icon="chart", level=1, color="primary")
"""

import streamlit as st
from typing import Optional, Literal

# Mapa de ícones Font Awesome 6 (livre)
ICON_MAP = {
    # Financeiro e Números
    "chart": "fa-chart-line",
    "chart-bar": "fa-chart-bar",
    "chart-pie": "fa-chart-pie",
    "dollar": "fa-dollar-sign",
    "wallet": "fa-wallet",
    "coins": "fa-coins",
    "trend": "fa-arrow-trend-up",
    "trend-down": "fa-arrow-trend-down",
    
    # Dados e Análise
    "data": "fa-database",
    "table": "fa-table",
    "search": "fa-magnifying-glass",
    "filter": "fa-filter",
    "sort": "fa-arrow-up-arrow-down",
    "analysis": "fa-chart-area",
    "metrics": "fa-gauge-high",
    "insights": "fa-lightbulb",
    
    # Ações e Edição
    "edit": "fa-pen-to-square",
    "delete": "fa-trash",
    "add": "fa-plus",
    "save": "fa-floppy-disk",
    "export": "fa-download",
    "import": "fa-upload",
    "copy": "fa-copy",
    "settings": "fa-gear",
    "config": "fa-sliders",
    
    # Status e Feedback
    "success": "fa-circle-check",
    "error": "fa-circle-xmark",
    "warning": "fa-triangle-exclamation",
    "info": "fa-circle-info",
    "help": "fa-circle-question",
    
    # Navegação e UI
    "home": "fa-house",
    "back": "fa-arrow-left",
    "next": "fa-arrow-right",
    "menu": "fa-bars",
    "close": "fa-xmark",
    "expand": "fa-expand",
    "collapse": "fa-compress",
    
    # Usuário e Autenticação
    "user": "fa-user",
    "profile": "fa-user-circle",
    "logout": "fa-right-from-bracket",
    "login": "fa-right-to-bracket",
    "lock": "fa-lock",
    "unlock": "fa-unlock",
    
    # Temporalidade
    "calendar": "fa-calendar",
    "clock": "fa-clock",
    "history": "fa-history",
    "seasonal": "fa-calendar-days",
    "period": "fa-hourglass-end",
    
    # Documentos e Arquivos
    "document": "fa-file",
    "pdf": "fa-file-pdf",
    "excel": "fa-file-excel",
    "folder": "fa-folder",
    "archive": "fa-file-zipper",
    
    # Especiais (Projeto)
    "dre": "fa-receipt",
    "simulation": "fa-crystal-ball",
    "methodology": "fa-gears",
    "economics": "fa-money-bill-trend-up",
    "index": "fa-percent",
    "volume": "fa-water",
    "margin": "fa-arrows-left-right",
    "result": "fa-balance-scale",
    
    # Extras
    "star": "fa-star",
    "flag": "fa-flag",
    "bell": "fa-bell",
    "link": "fa-link",
}

FONT_AWESOME_CDN = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"


def inject_font_awesome():
    """Injeta Font Awesome CDN no HTML da página"""
    st.markdown(
        f'<link rel="stylesheet" href="{FONT_AWESOME_CDN}">',
        unsafe_allow_html=True
    )


def get_icon(
    icon_name: str,
    size: Literal["xs", "sm", "md", "lg", "xl", "2x", "3x"] = "md",
    color: Optional[str] = None,
    custom_class: str = ""
) -> str:
    """
    Retorna HTML com ícone Font Awesome
    
    Args:
        icon_name: Nome do ícone (chave no ICON_MAP)
        size: Tamanho do ícone (xs, sm, md, lg, xl, 2x, 3x)
        color: Cor (hex, rgb, ou nome CSS)
        custom_class: Classes CSS customizadas adicionais
    
    Returns:
        String HTML com ícone
    
    Exemplo:
        html = get_icon("chart", size="lg", color="#06b6d4")
        st.markdown(html, unsafe_allow_html=True)
    """
    fa_class = ICON_MAP.get(icon_name.lower(), "fa-question")
    
    # Mapping de tamanhos Font Awesome
    size_map = {
        "xs": "fa-xs",
        "sm": "fa-sm",
        "md": "",
        "lg": "fa-lg",
        "xl": "fa-xl",
        "2x": "fa-2x",
        "3x": "fa-3x",
    }
    
    size_class = size_map.get(size, "")
    color_style = f"color: {color};" if color else ""
    
    html = f"""
    <i class="fas {fa_class} {size_class} {custom_class}" 
       style="{color_style}"></i>
    """
    
    return html.strip()


def render_icon_header(
    title: str,
    icon: str,
    level: Literal[1, 2, 3, 4] = 1,
    color: Literal["primary", "accent", "success", "error", "warning"] = "primary",
    subtitle: Optional[str] = None
) -> None:
    """
    Renderiza um header elegante com ícone
    
    Args:
        title: Texto do título
        icon: Nome do ícone
        level: Nível do heading (1-4)
        color: Cor temática (primary=#0c3a66, accent=#06b6d4, etc)
        subtitle: Subtítulo opcional
    
    Exemplo:
        render_icon_header("DRE Gerencial", icon="dre", level=1, color="primary")
    """
    color_map = {
        "primary": "#0c3a66",
        "accent": "#06b6d4",
        "success": "#10b981",
        "error": "#ef4444",
        "warning": "#f59e0b",
    }
    
    color_hex = color_map.get(color, "#0c3a66")
    fa_class = ICON_MAP.get(icon.lower(), "fa-question")
    heading_tag = f"h{level}"
    
    html = f"""
    <div style="margin-bottom: 20px;">
        <{heading_tag} style="
            color: {color_hex};
            margin: 0 0 8px 0;
            font-weight: 700;
            font-size: {'2.5em' if level == 1 else '2em' if level == 2 else '1.5em' if level == 3 else '1.25em'};
            display: flex;
            align-items: center;
            gap: 12px;
        ">
            <i class="fas {fa_class}" style="color: {color_hex};"></i>
            {title}
        </{heading_tag}>
        {'<p style="color: #666; margin: 0; font-size: 0.9em; margin-left: 28px;">' + subtitle + '</p>' if subtitle else ''}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def render_section_divider(text: Optional[str] = None, color: str = "#e2e8f0") -> None:
    """
    Renderiza um divisor de seção elegante
    
    Args:
        text: Texto opcional para o divisor
        color: Cor da linha
    
    Exemplo:
        render_section_divider("Seção 2")
    """
    if text:
        html = f"""
        <div style="
            display: flex;
            align-items: center;
            margin: 24px 0;
            gap: 12px;
        ">
            <div style="flex: 1; height: 1px; background-color: {color};"></div>
            <span style="
                color: #666;
                font-size: 0.85em;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            ">{text}</span>
            <div style="flex: 1; height: 1px; background-color: {color};"></div>
        </div>
        """
    else:
        html = f"""
        <div style="
            height: 1px;
            background-color: {color};
            margin: 24px 0;
        "></div>
        """
    
    st.markdown(html, unsafe_allow_html=True)


def render_badge(
    text: str,
    icon: Optional[str] = None,
    variant: Literal["primary", "accent", "success", "error", "warning"] = "primary"
) -> str:
    """
    Retorna HTML com badge elegante
    
    Args:
        text: Texto do badge
        icon: Nome do ícone opcional
        variant: Variante de cor
    
    Returns:
        String HTML
    
    Exemplo:
        html = render_badge("Em Progresso", icon="clock", variant="warning")
        st.markdown(html, unsafe_allow_html=True)
    """
    color_map = {
        "primary": ("#0c3a66", "#e0f2fe"),
        "accent": ("#06b6d4", "#ecf5fc"),
        "success": ("#10b981", "#f0fef4"),
        "error": ("#ef4444", "#fef2f2"),
        "warning": ("#f59e0b", "#fffbeb"),
    }
    
    color, bg_color = color_map.get(variant, ("#0c3a66", "#e0f2fe"))
    fa_class = ICON_MAP.get(icon.lower(), "") if icon else ""
    
    icon_html = f'<i class="fas {fa_class}" style="margin-right: 6px;"></i>' if icon else ""
    
    html = f"""
    <span style="
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: {bg_color};
        color: {color};
        padding: 6px 12px;
        border-radius: 16px;
        font-size: 0.85em;
        font-weight: 600;
        border: 1px solid {color};
    ">
        {icon_html}{text}
    </span>
    """
    
    return html


def render_stat_card(
    label: str,
    value: str,
    icon: str,
    subtitle: Optional[str] = None,
    change: Optional[str] = None,
    change_direction: Literal["up", "down", "neutral"] = "neutral"
) -> None:
    """
    Renderiza um card de estatística elegante
    
    Args:
        label: Rótulo da métrica
        value: Valor principal
        icon: Nome do ícone
        subtitle: Texto auxiliar
        change: Mudança percentual ou valor
        change_direction: Direção da mudança
    
    Exemplo:
        render_stat_card(
            "Margem Bruta",
            "R$ 1.2M",
            icon="chart",
            change="+5.2%",
            change_direction="up"
        )
    """
    fa_class = ICON_MAP.get(icon.lower(), "fa-question")
    
    change_color = "#10b981" if change_direction == "up" else "#ef4444" if change_direction == "down" else "#666"
    change_icon = "fa-arrow-trend-up" if change_direction == "up" else "fa-arrow-trend-down" if change_direction == "down" else "fa-minus"
    change_html = f"""
    <div style="color: {change_color}; font-weight: 600; margin-top: 8px;">
        <i class="fas {change_icon}" style="margin-right: 4px;"></i>{change}
    </div>
    """ if change else ""
    
    html = f"""
    <div style="
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
    " class="stat-card">
        <div style="display: flex; align-items: flex-start; justify-content: space-between;">
            <div style="flex: 1;">
                <p style="color: #666; font-size: 0.9em; margin: 0 0 8px 0; font-weight: 500;">
                    {label}
                </p>
                <p style="color: #0c3a66; font-size: 2em; margin: 0; font-weight: 700;">
                    {value}
                </p>
                {'<p style="color: #999; font-size: 0.85em; margin: 6px 0 0 0;">' + subtitle + '</p>' if subtitle else ''}
                {change_html}
            </div>
            <div style="
                width: 48px;
                height: 48px;
                background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
            ">
                <i class="fas {fa_class} fa-lg"></i>
            </div>
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def render_info_box(
    text: str,
    icon: str = "info",
    variant: Literal["info", "success", "warning", "error"] = "info"
) -> None:
    """
    Renderiza uma caixa de informação elegante
    
    Args:
        text: Texto da mensagem
        icon: Nome do ícone
        variant: Tipo de mensagem
    
    Exemplo:
        render_info_box("Dados atualizados com sucesso!", icon="success", variant="success")
    """
    color_map = {
        "info": ("#0c3a66", "#e0f2fe"),
        "success": ("#10b981", "#f0fef4"),
        "warning": ("#f59e0b", "#fffbeb"),
        "error": ("#ef4444", "#fef2f2"),
    }
    
    color, bg_color = color_map.get(variant, ("#0c3a66", "#e0f2fe"))
    fa_class = ICON_MAP.get(icon.lower(), "fa-circle-info")
    
    html = f"""
    <div style="
        background-color: {bg_color};
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
        display: flex;
        align-items: flex-start;
        gap: 12px;
    ">
        <i class="fas {fa_class}" style="
            color: {color};
            font-size: 1.2em;
            margin-top: 2px;
            flex-shrink: 0;
        "></i>
        <p style="
            color: {color};
            margin: 0;
            font-weight: 500;
            line-height: 1.5;
        ">
            {text}
        </p>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def render_page_header(
    title: str,
    icon_fa_class: str,
    subtitle: str = "",
    filters: dict = None
) -> None:
    """
    Renderiza header elegante padronizado para todas as páginas
    
    Args:
        title: Título principal
        icon_fa_class: Classe Font Awesome (ex: "fa-receipt", "fa-chart-bar")
        subtitle: Subtítulo opcional
        filters: Dict com filtros ativos {'cliente': '...', 'categoria': '...', 'produto': '...'}
    
    Exemplo:
        render_page_header(
            "Simulador de Projeções",
            "fa-wand-magic-sparkles",
            "Projete cenários e simule variações",
            filters={'cliente': 'Todos', 'categoria': 'ABC', 'produto': 'XYZ'}
        )
    """
    # Garantir Font Awesome carregado
    inject_font_awesome()
    
    # Construir HTML de filtros se fornecido
    filters_html = ""
    if filters:
        filter_items = []
        icons_map = {
            'cliente': '👤',
            'categoria': '📁',
            'produto': '📦'
        }
        for key, value in filters.items():
            if value:
                icon = icons_map.get(key, '●')
                filter_items.append(
                    f'<span style="background: rgba(255, 255, 255, 0.18); color: #ffffff; padding: 4px 10px; '
                    f'border-radius: 999px; font-size: 11px; font-weight: 600;">{icon} {value}</span>'
                )
        
        if filter_items:
            filters_html = f'<div style="margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px;">{"".join(filter_items)}</div>'
    
    html = f"""
    <style>
        .page-header-container {{
            background: linear-gradient(135deg, #0c3a66 0%, #06b6d4 100%);
            padding: 32px 24px;
            border-radius: 16px;
            margin-bottom: 32px;
            box-shadow: 0 8px 32px rgba(6, 182, 212, 0.25);
            border-left: 6px solid #ffffff;
        }}
        
        .page-header-title {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 2.8em;
            font-weight: 800;
            color: #ffffff;
            margin: 0 0 12px 0;
            letter-spacing: -0.5px;
            text-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        
        .page-header-subtitle {{
            color: rgba(255, 255, 255, 0.95);
            font-size: 1.05em;
            margin: 0;
            font-weight: 400;
            letter-spacing: 0.3px;
            line-height: 1.6;
        }}
        
        .page-header-icon {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 2.4em;
            color: #ffffff;
        }}
    </style>
    
    <div class="page-header-container">
        <div class="page-header-title">
            <i class="fas {icon_fa_class} page-header-icon"></i>
            {title}
        </div>
        {f'<p class="page-header-subtitle">{subtitle}</p>' if subtitle else ''}
        {filters_html}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


# Inicializar Font Awesome quando módulo é carregado
inject_font_awesome()
