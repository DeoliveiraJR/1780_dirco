"""
Modelos de dados da aplicação
"""

from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class ProjecaoFinanceira:
    """Modelo de dados para projeção financeira"""
    data_completa: str
    mes: str
    ano: str
    categoria: str
    curva_realizado: str
    projetado_analitico: str
    projetado_mercado: str
    projetado_ajustado: str


@dataclass
class Simulacao:
    """Modelo para simulação de resultados"""
    id: str
    usuario_id: str
    nome: str
    descricao: str
    data_criacao: datetime
    dados_ajustados: List[dict]
    ativo: bool = True


@dataclass
class Usuario:
    """Modelo para usuário do sistema"""
    id: str
    nome: str
    email: str
    departamento: str
    role: str
    data_criacao: datetime
