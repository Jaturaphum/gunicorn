import os
from flask import Flask
from router import router
import api

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "local-development-secret")

api.init_db()
app.register_blueprint(router)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)