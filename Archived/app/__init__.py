from flask import Flask
from .node import Node


def create_app(cache=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret-key-change-me'

    app.node = Node(cache)

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
