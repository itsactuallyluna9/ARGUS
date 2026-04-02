import asyncio
import threading
from datetime import datetime
from pathlib import Path
import json
import shutil
import subprocess
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from simpleeval import simple_eval
from pygooglenews import GoogleNews

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import chromadb
import requests

from argus.llamarouter import LlamaRouter
from argus.factcheck import FactCheck, check_url
from argus.compiledata import ArgusData

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="/")
CORS(app, resources={r"/api/*": {"origins": "*"}})

#router = LlamaRouter(["cs-cluster-1", "localhost", "luna"], [8080, 8080, 8080], ["GLM-4.7-Flash-UD-Q4_K_XL", "GLM-4.7-Flash-UD-Q4_K_XL", "nemotron-3-nano:4b"])
router = LlamaRouter(["cs-cluster-1", "localhost"], [8080, 8080], ["glm-4.7-flash", "nemotron-3-nano:4b"])

# Persistent event loop for background async tasks.
# Flask's WSGI server tears down its per-request event loop when a handler
# returns, which cancels any tasks created with asyncio.create_task().
_bg_loop = asyncio.new_event_loop()
_bg_thread = threading.Thread(target=_bg_loop.run_forever, daemon=True, name="argus-bg-loop")
_bg_thread.start()

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
async def api_create():
    data = request.get_json()
    url = data.get("url")

    if not await check_url(url, router):
        print("URL is not valid or cannot be scraped.")
        return jsonify({"message": f"URL {url} is not valid or cannot be scraped."}), 400

    found = False
    check: FactCheck = None  # type: ignore

    for fact_check in active_fact_checks:
        if fact_check.url == url:
            found = True
            check = fact_check
            break

    if not found:
        check = FactCheck(url, articles, router)
        asyncio.run_coroutine_threadsafe(check.main(), _bg_loop)
        active_fact_checks.append(check)

    return jsonify(check.to_dict()), 202

@app.get("/api/createrandom")
def api_create_random():
    
    if len(active_fact_checks) > 0:
       return jsonify({"message": "A fact check is already in progress. Please wait for it to finish before starting a new one."}), 409
    
    results = GoogleNews().top_news()

    url = random.choice(results["entries"])["link"]

    with Stealth().use_sync(sync_playwright()) as p:
        with p.chromium.launch(headless=True) as browser:
            page = browser.new_page()

            # go to url
            # wait for redirects to happen
            # print final url
            try:
                page.goto(url, wait_until="networkidle") # type: ignore
                url = page.url
            except:
                # fallback: load a random article from the database
                total = articles.count()
                if total > 0:
                    url = articles.get(limit=1, offset=random.randint(0, total - 1))["ids"][0]
                    # TODO: consider checking if we have a fact check for this article already

                # return jsonify({"message": f"Failed to load URL."}), 400

    check = FactCheck(url, articles, router) # type: ignore
    asyncio.run_coroutine_threadsafe(check.main(), _bg_loop)
    active_fact_checks.append(check)

    return jsonify(check.to_dict()), 202


@app.post("/api/retry")
def api_retry_check():
    data = request.get_json()
    uuid = data.get("uuid")
    url = None

    for fact_check in filter(lambda check: check.id == uuid, active_fact_checks):
        if not fact_check.finished:
            # what do we do here..?
            pass
        url = fact_check.url
        active_fact_checks.remove(fact_check)

    past_check = past_checks.get(ids=[uuid])
    if past_check["ids"]:
        fact_check = json.loads(past_checks.get(ids=[uuid])["documents"][0]) # type: ignore
        url = fact_check["article_metadata"]["url"]
        past_checks.delete(ids=[uuid])

    check = FactCheck(url, articles, router) # type: ignore
    asyncio.run_coroutine_threadsafe(check.main(), _bg_loop)
    active_fact_checks.append(check)
    return jsonify(check.to_dict()), 202


@app.post("/api/status")
async def api_status():
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

    return jsonify({"message": f"No fact check found for UUID {uuid}."}), 404


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

    if condition:
        
        try:
            data = [item for item in data if simple_eval(condition, names={col: item[col] for col in item.keys()})] 
        except Exception as e:
            return jsonify({"message": f"Error applying condition: {str(e)}"}), 400
    
    if cols:

        try: 
            missing_cols = [col for col in cols if col not in data[0].keys()]
        except IndexError:
            return jsonify({"message": f"No data found in collection {collection} with condition {condition}."}), 404
        
        if missing_cols:
            return jsonify({"message": f"Columns {missing_cols} not found in collection {collection}."}), 404
        
        data = [{col: item[col] for col in cols} for item in data]

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
async def api_debug_import():
    data = request.get_json()
    urls = data.get("urls")
    summarize_only = data.get("summarizeOnly", False)

    url_checks = await asyncio.gather(*(check_url(url, router) for url in urls))
    valid_urls = [url for url, is_valid in zip(urls, url_checks) if is_valid]

    # we're gonna do this async in the background, so we can return immediately
    asyncio.run_coroutine_threadsafe(bulk_import_articles(valid_urls, summarize_only), _bg_loop)

    # invalid_urls = urls not in valid_urls
    invalid_urls = [url for url, is_valid in zip(urls, url_checks) if not is_valid]

    return jsonify(
        {
            "message": f"Import started for {len(valid_urls)} valid URLs.",
            "invalid_urls": invalid_urls,
        }
    ), 202


async def bulk_import_articles(urls, summarize_only, use_long_prompts=True):
    from argus.scraper import get_page
    from argus.summarizearticle import summarize_article

    for url in urls:
        if summarize_only:
            article_metadata, article_text = await get_page(url)
            response = await summarize_article(article_text, router, model="gemma3:12b", think=False, use_long_prompt=use_long_prompts)
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
            check = FactCheck(url, articles, router)
            active_fact_checks.append(check)

            await check.main(use_long_prompts=use_long_prompts)

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
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
