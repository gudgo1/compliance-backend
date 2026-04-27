from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from extensions import db
from routes import register_routes


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    CORS(app, origins=app.config["CORS_ORIGINS"].split(","))
    register_routes(app)

    with app.app_context():
        db.create_all()

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
