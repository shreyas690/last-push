from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from app.core.config import Config
from app.core.database import Database

socketio = SocketIO(cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app)
    jwt.init_app(app)
    
    # Initialize Database
    Database.initialize()
    
    # Auto-create Single System Admin
    from app.models.user import UserModel
    from werkzeug.security import generate_password_hash
    if not UserModel.find_by_username("admin"):
        UserModel.create_user("admin", generate_password_hash("admin@123"), role="Admin", email="admin@morsecom.com")
        
    # Initialize SocketIO
    socketio.init_app(app)
    
    # Register blueprints
    from app.api.auth import auth_bp
    from app.api.dashboard import dashboard_bp
    from app.api.admin import admin_bp
    from app.api.ai import ai_bp
    from app.api.security_tests_api import security_tests_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(security_tests_bp, url_prefix='/api/security-tests')

    # Register socket events
    from app.sockets import events

    @app.route('/health', methods=['GET'])
    def health_check():
        return {'status': 'ok', 'message': 'Secure Morse Comm API is running'}

    return app
