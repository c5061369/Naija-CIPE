import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "naijacipe-dev-secret-key-change-in-production")

    _host = os.environ.get("DB_HOST", "localhost")
    _port = os.environ.get("DB_PORT", "3306")
    _user = os.environ.get("DB_USER", "root")
    _pass = os.environ.get("DB_PASSWORD", "")
    _name = os.environ.get("DB_NAME", "naija_cipe")
    _default_url = f"mysql+pymysql://{_user}:{_pass}@{_host}:{_port}/{_name}"

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", _default_url)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_SSL_STRICT = True


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
