"""Flask CI/CD Demo application."""

from flask import Flask


def create_app(config_name: str = "production") -> Flask:
    app = Flask(__name__)

    configs = {
        "production": "app.config.ProductionConfig",
        "staging": "app.config.StagingConfig",
        "testing": "app.config.TestingConfig",
    }

    app.config.from_object(configs.get(config_name, configs["production"]))

    from app.routes import api

    app.register_blueprint(api)

    return app
