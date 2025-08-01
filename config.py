import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Cấu hình chính cho ứng dụng"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
    FIREBASE_SERVICE_ACCOUNT_PATH = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH', 'firebase-service-account.json')
    
    # Application Configuration
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '0.0.0.0')
    
    # Data Configuration
    DEFAULT_COLLECTION = os.environ.get('DEFAULT_COLLECTION', 'data')
    REALTIME_COLLECTION = os.environ.get('REALTIME_COLLECTION', 'realtime')
    MAX_RECORDS = int(os.environ.get('MAX_RECORDS', 100))
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Cấu hình cho môi trường development"""
    DEBUG = True

class ProductionConfig(Config):
    """Cấu hình cho môi trường production"""
    DEBUG = False

class TestingConfig(Config):
    """Cấu hình cho môi trường testing"""
    TESTING = True
    DEBUG = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 