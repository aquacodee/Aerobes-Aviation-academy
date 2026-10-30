import os
from flask import Flask, jsonify
from .extensions import db, migrate, jwt, limiter, cors, bcrypt
from .routes.public import public_bp
from .routes.auth import auth_bp
from .routes.admin import admin_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-me"),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "dev-jwt-change-me"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///aeronex.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_ACCESS_TOKEN_EXPIRES=3600,
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
        RATELIMIT_DEFAULT="300 per day;60 per hour",
    )
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(
        app, origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    )
    from . import models

    app.register_blueprint(public_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "AeroNex Academy API"})

    @app.errorhandler(404)
    def not_found(_):
        return (
            jsonify({"error": {"code": "not_found", "message": "Resource not found"}}),
            404,
        )

    @app.errorhandler(500)
    def server_error(_):
        return (
            jsonify(
                {
                    "error": {
                        "code": "server_error",
                        "message": "An unexpected error occurred",
                    }
                }
            ),
            500,
        )

    return app
