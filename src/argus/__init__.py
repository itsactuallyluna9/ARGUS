from datetime import datetime
from pathlib import Path
import json
import shutil
import subprocess
import threading

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import chromadb
import requests

from argus.factcheck import FactCheck, check_url
from argus.compiledata import ArgusData

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="/")
CORS(app, resources={r"/api/*": {"origins": "*"}})

chromaclient = chromadb.HttpClient(host="localhost", port=8000)

articles = chromaclient.get_or_create_collection(name="articles")
past_checks = chromaclient.get_or_create_collection(name="fact_checks")

active_fact_checks = []
cached_data = ArgusData()
cached_data.fetch_data(articles, past_checks)


def get_gpu_metrics() -> dict[str, float | int | bool | None]:
    """Return GPU utilization and memory stats when nvidia-smi is available."""
    if shutil.which("nvidia-smi") is None:
        return {
            "gpu": None,
            "gpu_memory_used": None,
            "gpu_memory_total": None,
            "gpu_available": False,
        }

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (subprocess.SubprocessError, OSError):
        return {
            "gpu": None,
            "gpu_memory_used": None,
            "gpu_memory_total": None,
            "gpu_available": False,
        }

    utilization_values: list[float] = []
    memory_used_mib_values: list[int] = []
    memory_total_mib_values: list[int] = []

    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 3:
            continue

        try:
            utilization_values.append(float(parts[0]))
            memory_used_mib_values.append(int(parts[1]))
            memory_total_mib_values.append(int(parts[2]))
        except ValueError:
            continue

    if not utilization_values:
        return {
            "gpu": None,
            "gpu_memory_used": None,
            "gpu_memory_total": None,
            "gpu_available": False,
        }

    mib_to_bytes = 1024 * 1024

    return {
        "gpu": sum(utilization_values) / len(utilization_values),
        "gpu_memory_used": sum(memory_used_mib_values) * mib_to_bytes,
        "gpu_memory_total": sum(memory_total_mib_values) * mib_to_bytes,
        "gpu_available": True,
    }


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
                past_checks.add(ids=[fact_check.id], documents=[json.dumps(fact_check.to_dict())])

            return jsonify(fact_check.to_dict()), 202

    past_check = past_checks.get(ids=[uuid])  # type: ignore

    if past_check["ids"]:
        return jsonify(json.loads(past_checks.get(ids=[uuid])["documents"][0])), 200  # type: ignore

    return jsonify({"message": f"No active fact check found for UUID {uuid}."}), 404


@app.get("/api/data")
def api_data():
    # grab args from data loader panel to filter data as needed, forward as csv string, make sure to handle commas in text when relevant
    if (cached_data.timestamp and (datetime.now() - datetime.fromisoformat(cached_data.timestamp)).total_seconds() < 86400):  # if cached data is less than 24 hours old, return it
        return jsonify(cached_data.dict()), 200

    else:
        cached_data.fetch_data(articles, past_checks)
        return jsonify(cached_data.dict()), 200


@app.post("/api/data")
def api_data_filter():
    args = request.get_json()
    collection = args.get("collection") # collection name as string, either "articles" or "fact_checks"
    cols = json.loads(args.get("columns")) # list of column names to return, if empty return all columns
    condition = args.get("condition") # logical expression as string, rows included if eval(condition) is true, e.g. "accuracy_score > 3 and political_bias > -1"

    match collection:
        case "articles":
            data = cached_data.dict()["articles"]
        case "fact_checks":
            data = cached_data.dict()["fact_checks"]
        case _:
            return jsonify({"message": f"Collection {collection} not found."}), 404
    
    if cols:

        missing_cols = [col for col in cols if col not in data[0].keys()]
        if missing_cols:
            return jsonify({"message": f"Columns {missing_cols} not found in collection {collection}."}), 404
        
        data = [{col: item[col] for col in cols} for item in data]

    if condition:
        try:
            data = [item for item in data if eval(condition, {}, {col: item[col] for col in item.keys()})] 
        except Exception as e:
            return jsonify({"message": f"Error applying condition: {str(e)}"}), 400

    return jsonify(data), 200


@app.get("/api/debug/resources")
def api_debug_resources():
    import psutil

    gpu_metrics = get_gpu_metrics()
    return jsonify(
        {
            "cpu": psutil.cpu_percent(),
            "memory_used": psutil.virtual_memory().used,
            "memory_total": psutil.virtual_memory().total,
            **gpu_metrics,
        }
    )


@app.get("/api/debug/statistics")
def api_debug_statistics():
    return jsonify(
        {
            "factChecks": past_checks.count(),
            "activeFactChecks": len(active_fact_checks),
            "articlesInDatabase": articles.count(),
        }
    ), 200


@app.get("/api/debug/active_checks")
def api_debug_active_checks():
    return jsonify([check.id for check in active_fact_checks]), 200


@app.get("/api/debug/models")
def api_debug_loaded_models():
    res = requests.get("http://localhost:11434/api/ps")
    return res.content, res.status_code


@app.post("/api/debug/import")
def api_debug_import():
    data = request.get_json()
    urls = data.get("urls")
    summarize_only = data.get("summarizeOnly", False)

    valid_urls = [url for url in urls if check_url(url)]

    # we're gonna do this async in the background, so we can return immediately
    threading.Thread(target=bulk_import_articles, args=(valid_urls, summarize_only)).start()

    # invalid_urls = urls not in valid_urls
    invalid_urls = [url for url in urls if url not in valid_urls]

    return jsonify(
        {
            "message": f"Import started for {len(valid_urls)} valid URLs.",
            "invalid_urls": invalid_urls,
        }
    ), 202


def bulk_import_articles(urls, summarize_only):
    from argus.scraper import get_page
    from argus.summarizearticle import summarize_article

    for url in urls:
        if summarize_only:
            article_metadata, article_text = get_page(url)
            response = summarize_article(article_text, model="gemma3:12b", think=False)
            description = response["description"]  # type: ignore
            summary = response["articleSummary"]  # type: ignore
            key_points = response["points"]  # type: ignore
            bias_rating = response["biasSummary"]  # type: ignore

            try:
                articles.add(
                    ids=[url],
                    documents=[summary],
                    metadatas=[{"url": url, "description": description, "summary": summary, "bias": bias_rating, "points": key_points, "article_text": article_text, "timestamp": datetime.now().isoformat(), "metadata": json.dumps(article_metadata)}],
                )
            except:
                pass

        else:
            check = FactCheck(url, articles)
            active_fact_checks.append(check)
            check.thread.join()  # wait for the fact check to finish before starting the next one
            active_fact_checks.remove(check)
            past_checks.add(ids=[check.id], documents=[json.dumps(check.to_dict())])


@app.post("/api/debug/chroma")
def debug_chromadb():
    request_data = request.get_json()

    collection = chromaclient.get_collection(request_data["collection"])
    if len(request_data["query_texts"]) == 0:
        result = collection.get(
            limit=request_data["limit"],
            ids=(request_data["ids"] or None),
        )
    else:
        result = collection.query(
            query_texts=request_data["query_texts"],
            n_results=request_data["limit"],
            ids=(request_data["ids"] or None),
        )

    if request_data["method"] == "delete":
        collection.delete(ids=result["ids"]) # type: ignore
        return "{}", 204
    else:
        return jsonify(result)


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
