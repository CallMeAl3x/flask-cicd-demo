"""
Flask CI/CD Demo Application
=============================

A simple task management REST API built with Flask, designed to demonstrate
a complete CI/CD pipeline with GitHub Actions.

The application uses the **Application Factory** pattern, allowing multiple
instances with different configurations (production, staging, testing).
"""

from flask import Flask


def create_app(config_name: str = "production") -> Flask:
    """Create and configure the Flask application.

    Uses the factory pattern to instantiate the app with
    environment-specific settings.

    :param config_name: The configuration to use. One of
        ``"production"``, ``"staging"``, or ``"testing"``.
    :returns: A configured Flask application instance.

    Example::

        from app import create_app

        # Production
        app = create_app("production")

        # Testing
        app = create_app("testing")
        client = app.test_client()
    """
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
