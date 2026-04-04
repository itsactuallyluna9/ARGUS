import asyncio
import json
from itertools import repeat
from pathlib import Path
from typing import cast

from loguru import logger
from ollama import AsyncClient
from ollama import ResponseError as OllamaResponseError
from pydantic import HttpUrl

from argus.config import ModelRoute
from argus.llamarouter import LlamaRouter
from argus.summarizearticle import summarize_article
from argus.timers import with_timing

logger.add("benchmark.log", rotation="10 MB")


OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_OPENAI_BASE_URL = f"{OLLAMA_BASE_URL}/v1"
LLAMACPP_PORT = 8080
LLAMACPP_BASE_URL = f"http://localhost:{LLAMACPP_PORT}"
LLAMACPP_CTX = 1024 * 16
NUM_RUNS = 3
USE_LONG_PROMPTS = True

## Utilities ##


def article_iterator(articles: list[Path]):
    for article in articles:
        with open(article) as f:
            article_name = article.stem
            article_content = f.read()
            yield from repeat((article_content, article_name), NUM_RUNS)


async def gather_articles() -> list[Path]:
    articles = sorted(Path("benchmarking/articles").glob("*.md"))
    return articles


async def fetch_models() -> list[dict[str, str]]:
    with open("benchmarking/models.json") as f:
        data = json.load(f)
    return [data["metadata"][model] for model in data["to_benchmark"]]


## Ollama ##


async def wait_until_ollama_running():
    client = AsyncClient()
    logger.info("Waiting for Ollama...")
    while True:
        try:
            await client.ps()
            logger.info("Ollama active!")
            return
        except ConnectionError:
            await asyncio.sleep(1)


async def ollama_load(model: str) -> bool:
    ollama_needed_model = False
    client = AsyncClient()

    while True:
        try:
            logger.info("Loading {model} into Ollama", model=model)
            await client.chat(model, keep_alive=-1)
            return ollama_needed_model
        except OllamaResponseError:
            logger.warning("{model} not found - pulling", model=model)
            await client.pull(model)


async def ollama_unload(model: str):
    await AsyncClient().chat(model, keep_alive=0)


async def ollama_remove(model: str):
    await AsyncClient().delete(model)


## LllamaCPP ##

## Benchmarking ##


async def summarize_article_ollama(model: str, article: str, article_name: str):
    router = LlamaRouter(
        [ModelRoute(url=cast(HttpUrl, OLLAMA_OPENAI_BASE_URL), model_name=model)]
    )

    async with with_timing() as t:
        result = await summarize_article(article, router, model)
        logger.debug(result)
    logger.info(
        "{model} took {duration_s} seconds on {article_name}",
        model=model,
        article=article,
        duration_s=t.duration_s,
        article_name=article_name,
    )


async def factcheck_run_ollama(model: str, article: str, article_name: str):
    pass


async def benchmark_model(model: str, articles: list[Path]):
    ollama_needed_model = await ollama_load(model)

    for article, article_name in article_iterator(articles):
        await summarize_article_ollama(model, article, article_name)

    for article, article_name in article_iterator(articles):
        await factcheck_run_ollama(model, article, article_name)

    await ollama_unload(model)

    # TODO: LlamaCpp

    for article, article_name in article_iterator(articles):
        pass

    for article, article_name in article_iterator(articles):
        pass

    if ollama_needed_model:
        await ollama_remove(model)


async def main():
    await wait_until_ollama_running()

    articles = await gather_articles()
    models = await fetch_models()

    for model in models:
        await benchmark_model(model["name"], articles)


if __name__ == "__main__":
    asyncio.run(main())
