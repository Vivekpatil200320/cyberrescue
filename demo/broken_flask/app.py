import os
from flask import Flask

# Intentionally crashes on startup if DATABASE_URL isn't set — KeyError,
# not .get() with a default, so the failure is loud and immediate.
DATABASE_URL = os.environ["DATABASE_URL"]

app = Flask(__name__)


@app.route("/")
def health():
    return {"status": "ok", "db": DATABASE_URL}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
