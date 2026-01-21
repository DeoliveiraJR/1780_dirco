"""
Backend Application Package
"""

from flask import Flask
from flask_cors import CORS

def create_app(config_name='development'):
    """
    Application factory pattern
    """
    app = Flask(__name__)
    
    # Configuração CORS
    CORS(app)
    
    # Configuração por ambiente
    if config_name == 'development':
        app.config['DEBUG'] = True
    else:
        app.config['DEBUG'] = False
    
    # Registrar blueprints
    from app.routes import data_routes
    app.register_blueprint(data_routes.bp)
    
    return app
