from openai import AsyncOpenAI
from ollama import AsyncClient

import json
import subprocess
import asyncio

from loguru import logger
from argus.summarizearticle import summarize_article
from argus.factcheck import FactCheck
from argus.timers import with_timing
from argus.config import DEV_CONFIG
from argus.webhooks import _process_webhook as process_webhook
from argus.llamarouter import LlamaRouter

from rich.progress import Progress

OLLAMA_BASE_URL = "http://localhost:11434"
LLAMACPP_PORT = 8081
LLAMACPP_BASE_URL = f"http://localhost:{LLAMACPP_PORT}"
LLAMACPP_CTX = 1024 * 16
NUM_RUNS = 3
USE_LONG_PROMPTS = False

async def main():
    asyncio.selector_events

if __name__ == "__main__":
    asyncio.run(main())
