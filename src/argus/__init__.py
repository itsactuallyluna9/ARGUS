import asyncio
import threading
from datetime import datetime
from pathlib import Path
import json
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from simpleeval import simple_eval
from pygooglenews import GoogleNews

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import chromadb

from argus.config import Config, load_config
from argus.llamarouter import LlamaRouter
from argus.factcheck import FactCheck, check_url
from argus.compiledata import ArgusData
from argus.log_config import setup_logging
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
CONFIG_PATH = PROJECT_ROOT / "config.toml"

config = load_config(CONFIG_PATH)
setup_logging(config)

app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="/")
CORS(app, resources={r"/api/*": {"origins": "*"}})

router = LlamaRouter(
    ips=[str(route.url.host) for route in config.model_routes],
    ports=[int(route.url.port or 8080) for route in config.model_routes],
    models=[route.model_name for route in config.model_routes],
    api_keys=[route.api_key for route in config.model_routes],
    temperatures=[route.temperature for route in config.model_routes],
    max_tokens_list=[route.max_tokens for route in config.model_routes],
)

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
active_fact_checks_lock = threading.Lock()
completed_fact_check_ids: set[str] = set()
cached_data = ArgusData()
cached_data.fetch_data(articles, past_checks)


def _add_active_fact_check(check: FactCheck) -> None:
    with active_fact_checks_lock:
        active_fact_checks.append(check)


def _remove_active_fact_check(uuid: str) -> FactCheck | None:
    with active_fact_checks_lock:
        for index, fact_check in enumerate(active_fact_checks):
            if fact_check.id == uuid:
                return active_fact_checks.pop(index)

    return None


def _get_active_fact_check(uuid: str) -> FactCheck | None:
    with active_fact_checks_lock:
        for fact_check in active_fact_checks:
            if fact_check.id == uuid:
                return fact_check

    return None


def _finalize_fact_check(check: FactCheck, future: object | None = None) -> None:
    if future is not None:
        try:
            future.result()  # type: ignore[attr-defined]
        except Exception as exc:
            check.fact_check_metadata["check_error"] = str(exc)
            check.finished = True

    if not check.finished:
        return

    with active_fact_checks_lock:
        if check.id in completed_fact_check_ids:
            return

        completed_fact_check_ids.add(check.id)
        if check in active_fact_checks:
            active_fact_checks.remove(check)

    try:
        past_checks.add(ids=[check.id], documents=[json.dumps(check.to_dict())])
    except Exception as exc:
        check.fact_check_metadata["check_error"] = str(exc)
        check.finished = True
        with active_fact_checks_lock:
            completed_fact_check_ids.discard(check.id)
            if check not in active_fact_checks:
                active_fact_checks.append(check)


@app.post("/api/create")
async def api_create():
    data = request.get_json()
    url = data.get("url")

    if not await check_url(url, router):
        logger.info("URL is not valid or cannot be scraped.")
        return jsonify({"message": f"URL {url} is not valid or cannot be scraped."}), 400

    found = False
    check: FactCheck = None  # type: ignore

    with active_fact_checks_lock:
        active_checks = list(active_fact_checks)

    for fact_check in active_checks:
        if fact_check.url == url:
            found = True
            check = fact_check
            break

    if not found:
        check = FactCheck(url, articles, router, config, evaluator_model="glm-4.7-flash") 
        _add_active_fact_check(check)
        future = asyncio.run_coroutine_threadsafe(check.main(), _bg_loop)
        future.add_done_callback(lambda future, check=check: _finalize_fact_check(check, future))

    return jsonify(check.to_dict()), 202

@app.get("/api/createrandom")
async def api_create_random():
    with active_fact_checks_lock:
        if active_fact_checks:
            return jsonify({"message": "A fact check is already in progress. Please wait for it to finish before starting a new one."}), 409

    results = GoogleNews().top_news()

    url = random.choice(results["entries"])["link"]

    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # go to url
        # wait for redirects to happen
        # print final url
        try:
            await page.goto(url, wait_until="networkidle") # type: ignore
            url = page.url

        except:
            # fallback: load a random article from the database
            total = articles.count()
            if total > 0:
                url = articles.get(limit=1, offset=random.randint(0, total - 1))["ids"][0]
                # TODO: consider checking if we have a fact check for this article already

            # return jsonify({"message": f"Failed to load URL."}), 400
        
        finally:
            await browser.close()

    check = FactCheck(url, articles, router, config, evaluator_model="glm-4.7-flash") # type: ignore
    _add_active_fact_check(check)
    future = asyncio.run_coroutine_threadsafe(check.main(), _bg_loop)
    future.add_done_callback(lambda future, check=check: _finalize_fact_check(check, future))

    return jsonify(check.to_dict()), 202



@app.post("/api/retry")
def api_retry_check():
    data = request.get_json()
    uuid = data.get("uuid")
    url = None

    fact_check = _remove_active_fact_check(uuid)
    if fact_check is not None:
        url = fact_check.url
        if not fact_check.finished:
            # what do we do here..?
            pass

    past_check = past_checks.get(ids=[uuid])
    if past_check["ids"]:
        fact_check = json.loads(past_checks.get(ids=[uuid])["documents"][0]) # type: ignore
        url = fact_check["article_metadata"]["url"]
        past_checks.delete(ids=[uuid])

    if url is None:
        logger.info(f"No fact check found for UUID {uuid}.")
        return jsonify({"message": f"No fact check found for UUID {uuid}."}), 404

    check = FactCheck(url, articles, router, config) # type: ignore
    _add_active_fact_check(check)
    future = asyncio.run_coroutine_threadsafe(check.main(), _bg_loop)
    future.add_done_callback(lambda future, check=check: _finalize_fact_check(check, future))
    return jsonify(check.to_dict()), 202


@app.post("/api/status")
async def api_status():
    data = request.get_json()
    uuid = data.get("uuid")

    fact_check = _get_active_fact_check(uuid)
    if fact_check is not None:
        if fact_check.finished:
            _finalize_fact_check(fact_check)
            return jsonify(fact_check.to_dict()), 200

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


@app.get("/api/debug/statistics")
def api_debug_statistics():
    with active_fact_checks_lock:
        active_fact_checks_count = len(active_fact_checks)

    return jsonify(
        {
            "factChecks": past_checks.count(),
            "activeFactChecks": active_fact_checks_count,
            "articlesInDatabase": articles.count(),
        }
    ), 200


@app.get("/api/debug/active_checks")
def api_debug_active_checks():
    with active_fact_checks_lock:
        active_check_ids = [check.id for check in active_fact_checks]

    return jsonify(active_check_ids), 200


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
            response = await summarize_article(article_text, router, model="nemotron-3-nano:4b", think=False, use_long_prompt=use_long_prompts)
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
            check = FactCheck(url, articles, router, config)
            _add_active_fact_check(check)

            try:
                await check.main(use_long_prompts=use_long_prompts)
            except Exception as exc:
                check.fact_check_metadata["check_error"] = str(exc)
                check.finished = True
            finally:
                _finalize_fact_check(check)


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


@app.get("/r/<path:path>")
def serve_r_scripts(path: str):
    return send_from_directory(PROJECT_ROOT / "r", path, mimetype="text/plain")


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
    host = str(getattr(config.host, "ip", config.host))
    app.run(host=host, port=config.port, debug=False)


if __name__ == "__main__":
    main()
