import os
import time

import pymysql
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

# Allowed frontend origins (comma-separated). Default: React in Docker (3000) and Vite dev (5173)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
CORS(app, origins=CORS_ORIGINS)

# DB settings come from environment variables (same image works locally and with RDS later)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "appuser"),
    "password": os.getenv("DB_PASSWORD", "apppass"),
    "database": os.getenv("DB_NAME", "appdb"),
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}


def get_conn():
    return pymysql.connect(**DB_CONFIG)


def init_db(retries=10, delay=3):
    for attempt in range(1, retries + 1):
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute(
                    """CREATE TABLE IF NOT EXISTS items (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )"""
                )
            print("Database ready", flush=True)
            return
        except pymysql.MySQLError as e:
            print(f"DB not ready (attempt {attempt}/{retries}): {e}", flush=True)
            time.sleep(delay)
    raise RuntimeError("Could not connect to database")


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/items")
def list_items():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name, created_at FROM items ORDER BY id DESC")
        rows = cur.fetchall()
    for r in rows:
        r["created_at"] = r["created_at"].isoformat()
    return jsonify(rows)


@app.post("/items")
def add_item():
    name = (request.get_json(silent=True) or {}).get("name", "").strip()
    if not name:
        return jsonify(error="name is required"), 400
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO items (name) VALUES (%s)", (name,))
        new_id = cur.lastrowid
    return jsonify(id=new_id, name=name), 201


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
