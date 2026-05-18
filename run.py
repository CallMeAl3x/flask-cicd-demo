import os

from app import create_app

config = os.environ.get("FLASK_ENV", "production")
app = create_app(config)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
