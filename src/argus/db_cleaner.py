import asyncio

import chromadb
import json
from pydantic import HttpUrl

from argus.llamarouter import LlamaRouter
from argus.config import ModelRoute



async def check_fact_check(id, col: chromadb.Collection, router: LlamaRouter, semaphore: asyncio.Semaphore):

    async with semaphore:
        try:
            item = json.loads(col.get(ids=[id])['documents'][0])
            if item["finished"] == True:
                if not await is_valid_check(item, router):
                    print(f"Deleting {id} because it is marked finished but fails the check_fact_check function")
                    col.delete(ids=[id])
                else:
                    print(f"{id} is marked finished and passes the check_fact_check function")
        except Exception as e:
            print(f"Error processing item with id {id}: {e}")
            print(f"Deleting {id} because it is malformed")
            col.delete(ids=[id])


async def is_valid_check(item, router: LlamaRouter):
    
    prompt = f"""You are a helpful assistant for checking the quality of news article fact checks. 

    Here is the fact check to check:
    {json.dumps(item)}

    Please respond with "yes" if the presented fact check is complete and well-formed, and "no" if it is not. A complete and well-formed fact check should be marked as finished and should include a title, summary, key points, and non-empty explanations and scores for accuracy, completeness, political bias, sensationalism, and emotional language. Do NOT include any additional text, explanation, or markdown formatting, only respond with "yes" or "no".
    """

    response = await router.generate(
        prompt=prompt,
        model="nemotron-3-nano:4b",
        format="text",
    )

    content = (response.content or "").strip().lower() # type: ignore

    if content in ["yes", "no"]:
        return content == "yes"
    else:
        print(f"Unexpected response from check_fact_check model: {content}")
        return False


async def check_summary(id, router: LlamaRouter, semaphore: asyncio.Semaphore):
    
    async with semaphore:
        try:
            summary = articles.get(ids=[id])['documents'][0]
            if summary in ['', 'Summary not found']:
                print(f"Deleting {id} because it has an empty summary")
                articles.delete(ids=[id])
            else:
                print(f"Checking summary for {id}")
                if not await is_valid_summary(summary, router):
                    print(f"Deleting {id} because it has a summary that fails the check_summary function")
                    articles.delete(ids=[id])
                else:
                    print(f"Summary for {id} passed the check_summary function")

        except Exception as e:
            print(f"Error processing item with id {id}: {e}")
            print(f"Deleting {id} because it is malformed")
            articles.delete(ids=[id])          
    

async def is_valid_summary(summary, router: LlamaRouter):

    prompt = f"""You are a helpful assistant for checking the quality of news article summaries. 

    Here is the summary to check:
    {summary}

    Please respond with "yes" if the presented text is actually an article summary, and "no" if it is not. Do NOT include any additional text, explanation, or markdown formatting, only respond with "yes" or "no".
    """

    response = await router.generate(
        prompt=prompt,
        model="nemotron-3-nano:4b",
        format="text",
    )

    content = (response.content or "").strip().lower() # type: ignore

    if content in ["yes", "no"]:
        return content == "yes"
    else:
        print(f"Unexpected response from check_summary model: {content}")
        return False


async def main(router: LlamaRouter, fact_checks: chromadb.Collection, articles: chromadb.Collection, workers: int = 2):

    semaphore = asyncio.Semaphore(workers)

    fc_ids = fact_checks.get(ids=None)["ids"]
    await asyncio.gather(*(check_fact_check(id, fact_checks, router, semaphore) for id in fc_ids))

    ids = articles.get(ids=None)["ids"]
    await asyncio.gather(*(check_summary(id, router, semaphore) for id in ids))


if __name__ == "__main__":

    client = chromadb.HttpClient("localhost")
    articles = client.get_or_create_collection("articles")
    fact_checks = client.get_or_create_collection("fact_checks")

    routes = [
        ModelRoute(url=HttpUrl("http://luna:8080"), model_name="nemotron-3-nano:4b"),
        ModelRoute(url=HttpUrl("http://localhost:8080"), model_name="nemotron-3-nano:4b"),
    ]

    router = LlamaRouter(routes)

    asyncio.run(main(router, fact_checks, articles))