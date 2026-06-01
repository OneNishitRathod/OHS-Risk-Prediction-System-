"""
app/__init__.py — Application factory
"""
from flask import Flask
from config import Config


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    from app.routes import main
    app.register_blueprint(main)

    return app
