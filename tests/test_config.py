from app import create_app


def test_production_config():
    app = create_app("production")
    assert not app.config["DEBUG"]
    assert not app.config["TESTING"]


def test_staging_config():
    app = create_app("staging")
    assert app.config["DEBUG"]


def test_testing_config():
    app = create_app("testing")
    assert app.config["TESTING"]
