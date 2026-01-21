"""
Rotas para manipulação de dados
"""

from flask import Blueprint, request, jsonify
from app.services.data_service import DataService
import os

bp = Blueprint('data', __name__, url_prefix='/api/data')

# Instância do serviço de dados (singleton para MVP)
data_service = DataService()


@bp.route('/upload', methods=['POST'])
def upload_dados():
    """
    Endpoint para upload de dados
    
    Espera arquivo multipart/form-data com chave 'arquivo'
    """
    try:
        if 'arquivo' not in request.files:
            return jsonify({'sucesso': False, 'mensagem': 'Nenhum arquivo enviado'}), 400
        
        arquivo = request.files['arquivo']
        
        if arquivo.filename == '':
            return jsonify({'sucesso': False, 'mensagem': 'Arquivo vazio'}), 400
        
        # Salvar arquivo temporariamente
        arquivo_path = f'/tmp/{arquivo.filename}'
        arquivo.save(arquivo_path)
        
        # Converter para JSON
        resultado = data_service.converter_excel_para_json(arquivo_path)
        
        if resultado['sucesso']:
            # Armazenar dados
            data_service.armazenar_dados(resultado['dados'])
            
            # Remover arquivo temporário
            if os.path.exists(arquivo_path):
                os.remove(arquivo_path)
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


@bp.route('/dados', methods=['GET'])
def obter_dados():
    """
    Endpoint para obter dados
    
    Query params opcionais: categoria, mes, ano
    """
    try:
        filtros = {
            'categoria': request.args.get('categoria'),
            'mes': request.args.get('mes'),
            'ano': request.args.get('ano')
        }
        
        # Remover filtros None
        filtros = {k: v for k, v in filtros.items() if v is not None}
        
        dados = data_service.obter_dados(filtros)
        
        return jsonify({
            'sucesso': True,
            'total': len(dados),
            'dados': dados
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


@bp.route('/simulacao', methods=['POST'])
def criar_simulacao():
    """
    Endpoint para criar simulação
    
    Body JSON:
    {
        "usuario_id": "user_1",
        "nome": "Simulação Teste",
        "dados_ajustados": [...]
    }
    """
    try:
        payload = request.get_json()
        
        simulacao = data_service.criar_simulacao(
            usuario_id=payload.get('usuario_id'),
            nome=payload.get('nome'),
            dados_ajustados=payload.get('dados_ajustados', [])
        )
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Simulação criada com sucesso',
            'simulacao': simulacao
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


@bp.route('/simulacoes/<usuario_id>', methods=['GET'])
def obter_simulacoes(usuario_id):
    """
    Endpoint para obter simulações de um usuário
    """
    try:
        simulacoes = data_service.obter_simulacoes_usuario(usuario_id)
        
        return jsonify({
            'sucesso': True,
            'total': len(simulacoes),
            'simulacoes': simulacoes
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


@bp.route('/status', methods=['GET'])
def status_backend():
    """
    Endpoint de status do backend
    """
    return jsonify({
        'status': 'online',
        'versao': '1.0.0',
        'dados_armazenados': len(data_service.dados_armazenados),
        'simulacoes_totais': len(data_service.simulacoes)
    })
