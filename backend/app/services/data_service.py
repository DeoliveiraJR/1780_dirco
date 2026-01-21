"""
Serviço para manipulação de dados financeiros
"""

import pandas as pd
import json
from typing import List, Dict, Optional
import os
from datetime import datetime


class DataService:
    """
    Serviço responsável por importação, processamento e armazenamento de dados
    """
    
    def __init__(self):
        """Inicializa o serviço de dados"""
        # Armazenamento em memória (mock backend)
        self.dados_armazenados = []
        self.simulacoes = []
        self.usuarios = []
        
    def converter_excel_para_json(self, arquivo_path: str) -> Dict:
        """
        Converte arquivo Excel para estrutura JSON
        
        Args:
            arquivo_path: Caminho do arquivo Excel
            
        Returns:
            Dicionário com dados processados
        """
        try:
            # Ler arquivo Excel
            df = pd.read_excel(arquivo_path, sheet_name='Projeções')
            
            # Converter para lista de dicionários
            dados_json = df.to_dict(orient='records')
            
            # Processar e validar dados
            dados_processados = self._validar_e_processar_dados(dados_json)
            
            return {
                'sucesso': True,
                'mensagem': f'Dados importados com sucesso. Total: {len(dados_processados)} registros',
                'dados': dados_processados,
                'metadata': {
                    'total_registros': len(dados_processados),
                    'data_importacao': datetime.now().isoformat(),
                    'categorias': list(set([d['CATEGORIA'] for d in dados_processados])),
                    'periodo': self._extrair_periodo(dados_processados)
                }
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro ao processar arquivo: {str(e)}',
                'dados': []
            }
    
    def _validar_e_processar_dados(self, dados: List[Dict]) -> List[Dict]:
        """
        Valida e processa dados brutos
        
        Args:
            dados: Lista de dicionários com dados brutos
            
        Returns:
            Lista de dados processados e validados
        """
        campos_obrigatorios = [
            'DATA_COMPLETA', 'MES', 'ANO', 'CATEGORIA',
            'CURVA_REALIZADO', 'PROJETADO_ANALITICO', 
            'PROJETADO_MERCADO', 'PROJETADO_AJUSTADO'
        ]
        
        dados_processados = []
        
        for registro in dados:
            # Validar campos obrigatórios
            if all(campo in registro for campo in campos_obrigatorios):
                # Processar valores monetários
                registro_processado = {
                    'DATA_COMPLETA': str(registro['DATA_COMPLETA']),
                    'MES': str(registro['MES']).lower(),
                    'ANO': str(registro['ANO']),
                    'CATEGORIA': str(registro['CATEGORIA']),
                    'CURVA_REALIZADO': self._converter_valor_monetario(registro['CURVA_REALIZADO']),
                    'PROJETADO_ANALITICO': self._converter_valor_monetario(registro['PROJETADO_ANALITICO']),
                    'PROJETADO_MERCADO': self._converter_valor_monetario(registro['PROJETADO_MERCADO']),
                    'PROJETADO_AJUSTADO': self._converter_valor_monetario(registro['PROJETADO_AJUSTADO']),
                }
                
                dados_processados.append(registro_processado)
        
        return dados_processados
    
    @staticmethod
    def _converter_valor_monetario(valor: str) -> float:
        """
        Converte valor em formato R$ para float
        
        Args:
            valor: String com valor monetário
            
        Returns:
            Valor em formato float
        """
        try:
            # Remove 'R$' e espaços
            valor_limpo = valor.replace('R$', '').strip()
            # Remove ponto de milhar e substitui vírgula por ponto
            valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
            return float(valor_limpo)
        except:
            return 0.0
    
    @staticmethod
    def _extrair_periodo(dados: List[Dict]) -> Dict:
        """
        Extrai período de dados
        
        Args:
            dados: Lista de dados
            
        Returns:
            Dicionário com período inicial e final
        """
        if not dados:
            return {'inicio': None, 'fim': None}
        
        anos = sorted(set([int(d['ANO']) for d in dados]))
        
        return {
            'inicio': f'{anos[0]}',
            'fim': f'{anos[-1] if len(anos) > 1 else anos[0]}'
        }
    
    def armazenar_dados(self, dados: List[Dict]) -> Dict:
        """
        Armazena dados processados
        
        Args:
            dados: Dados a serem armazenados
            
        Returns:
            Confirmação de armazenamento
        """
        self.dados_armazenados = dados
        
        return {
            'sucesso': True,
            'mensagem': f'{len(dados)} registros armazenados com sucesso',
            'total_armazenado': len(self.dados_armazenados)
        }
    
    def obter_dados(self, filtros: Optional[Dict] = None) -> List[Dict]:
        """
        Obtém dados armazenados com filtros opcionais
        
        Args:
            filtros: Dicionário com filtros (categoria, mes, ano)
            
        Returns:
            Lista de dados filtrados
        """
        dados = self.dados_armazenados
        
        if not filtros:
            return dados
        
        # Aplicar filtros
        if 'categoria' in filtros:
            dados = [d for d in dados if d['CATEGORIA'].lower() == filtros['categoria'].lower()]
        
        if 'mes' in filtros:
            dados = [d for d in dados if d['MES'].lower() == filtros['mes'].lower()]
        
        if 'ano' in filtros:
            dados = [d for d in dados if d['ANO'] == str(filtros['ano'])]
        
        return dados
    
    def criar_simulacao(self, usuario_id: str, nome: str, dados_ajustados: List[Dict]) -> Dict:
        """
        Cria uma nova simulação
        
        Args:
            usuario_id: ID do usuário
            nome: Nome da simulação
            dados_ajustados: Dados ajustados da simulação
            
        Returns:
            Dados da simulação criada
        """
        simulacao = {
            'id': f'sim_{len(self.simulacoes) + 1}',
            'usuario_id': usuario_id,
            'nome': nome,
            'data_criacao': datetime.now().isoformat(),
            'dados_ajustados': dados_ajustados,
            'ativo': True
        }
        
        self.simulacoes.append(simulacao)
        
        return simulacao
    
    def obter_simulacoes_usuario(self, usuario_id: str) -> List[Dict]:
        """
        Obtém todas as simulações de um usuário
        
        Args:
            usuario_id: ID do usuário
            
        Returns:
            Lista de simulações
        """
        return [s for s in self.simulacoes if s['usuario_id'] == usuario_id]
