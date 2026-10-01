import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .database import init_db
from .routes import router


project_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app():
    flask_app = Flask(
        __name__,
        template_folder=os.path.join(project_directory, "templates"),
        static_folder=os.path.join(project_directory, "static"),
        static_url_path="/static",
    )
    flask_app.secret_key = os.environ.get("FLASK_SECRET_KEY", "local-development-secret")
    flask_app.wsgi_app = ProxyFix(
        flask_app.wsgi_app,
        x_for=int(os.environ.get("TRUSTED_PROXY_COUNT", "0")),
    )
    flask_app.register_blueprint(router)
    init_db()
    return flask_app
