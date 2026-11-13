# app/__init__.py
from flask import Flask
from app.routes import bp


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="",
        template_folder="static"
    )
    app.register_blueprint(bp)
    return app