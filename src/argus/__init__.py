from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import chromadb

from argus.factcheck import FactCheck, check_url

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="/")
CORS(app, resources={r"/api/*": {"origins": "*"}})

chromaclient = chromadb.HttpClient(host="localhost", port=8000)

articles = chromaclient.get_or_create_collection(name="articles")

active_fact_checks = []


@app.post("/api/create")
def api_create():
    data = request.get_json()
    url = data.get("url")

    if not check_url(url):
        return jsonify({"message": f"URL {url} is not valid or cannot be scraped."}), 400

    found = False
    check: FactCheck = None  # type: ignore

    for fact_check in active_fact_checks:
        if fact_check.url == url:
            found = True
            check = fact_check
            break

    if not found:
        check = FactCheck(url, articles)
        active_fact_checks.append(check)

    return jsonify(check.to_dict()), 202


@app.post("/api/status")
def api_status():    

    data = request.get_json()
    uuid = data.get("uuid")

    for fact_check in active_fact_checks:

        if fact_check.id == uuid:

            if fact_check.finished:

                active_fact_checks.remove(fact_check)
                
            return jsonify(fact_check.to_dict()), 202

    return jsonify({"message": f"No active fact check found for UUID {uuid}."}), 404


@app.get("/", defaults={"path": ""})
@app.get("/<path:path>")
def serve_frontend(path: str):
    if FRONTEND_DIST.exists():
        requested_file = FRONTEND_DIST / path

        if path and requested_file.is_file():
            return send_from_directory(FRONTEND_DIST, path)

        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return send_from_directory(FRONTEND_DIST, "index.html")

    return jsonify(
        {
            "message": "ARGUS backend is running. Build frontend assets to serve React from Flask.",
            "api": "/api/hello",
        }
    )


def main() -> None:
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    pass
    # main()
