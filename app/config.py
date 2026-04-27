"""
Configuration
=============

Environment-specific configuration classes for the Flask application.

Each class inherits from :class:`BaseConfig` and overrides the relevant
settings. The active configuration is selected via the ``config_name``
parameter in :func:`app.create_app`.

Environment variables
---------------------

- ``SECRET_KEY`` -- Secret key for session signing. **Must** be set in production.
"""

import os


class BaseConfig:
    """Base configuration shared by all environments.

    :cvar SECRET_KEY: Secret key read from the ``SECRET_KEY`` environment variable.
    :cvar DEBUG: Enables debug mode. Default ``False``.
    :cvar TESTING: Enables testing mode. Default ``False``.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    DEBUG = False
    TESTING = False


class ProductionConfig(BaseConfig):
    """Production configuration.

    Inherits all defaults from :class:`BaseConfig`.
    Debug and testing modes are disabled.
    """


class StagingConfig(BaseConfig):
    """Staging (pre-production) configuration.

    Same as production but with :attr:`DEBUG` enabled for troubleshooting.
    """

    DEBUG = True


class TestingConfig(BaseConfig):
    """Testing configuration used by pytest.

    Enables :attr:`TESTING` so Flask returns exceptions instead of
    error pages, making assertions easier.
    """

    TESTING = True
