from flask import Flask
from .node import Node

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret-key-change-me'

    app.node = Node()

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
