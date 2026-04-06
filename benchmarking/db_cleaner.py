import asyncio

import chromadb
import json
from pydantic import HttpUrl

from argus.llamarouter import LlamaRouter
from argus.config import ModelRoute

client = chromadb.HttpClient("localhost")
articles = client.get_or_create_collection("articles")
fact_checks = client.get_or_create_collection("fact_checks")

def clean_checks(col: chromadb.Collection) -> None:
    for id in col.get(ids=None)["ids"]:
        try:
            item = json.loads(col.get(ids=[id])['documents'][0])
            if item["finished"] == True:
                if "accuracy_explanation" in item and "completeness_explanation" in item and "political_bias" in item and "sensationalism" in item and "emotional_language" in item:
                    if item["accuracy_explanation"] in ['', 'Accuracy reasoning not found'] or item["completeness_explanation"] in ['', 'Completeness reasoning not found'] or item["political_bias"] in ['', 'Political bias explanation not found'] or item["sensationalism"] in ['', 'Sensationalism explanation not found'] or item["emotional_language"] in ['', 'Emotional language explanation not found']:
                        print(f"Deleting {id} because it is marked finished but has empty explanations")
                        col.delete(ids=[id])
                else:
                    print(f"Deleting {id} because it is marked finished but is missing some explanations")
                    col.delete(ids=[id])
        except Exception as e:
            print(f"Error processing item with id {id}: {e}")
            print(f"Deleting {id} because it is malformed")
            col.delete(ids=[id])


async def clean_articles(col: chromadb.Collection, router: LlamaRouter) -> None:
    for id in col.get(ids=None)["ids"]:
        try:

            item = json.loads(col.get(ids=[id])['documents'][0])

            if item["summary"] in ['', 'Summary not found']:
                print(f"Deleting {id} because it has an empty summary")
                col.delete(ids=[id])

            else:

                if not await is_valid_summary(item["summary"], router):
                    print(f"Deleting {id} because it has a summary that fails the check_summary function")
                    col.delete(ids=[id])

                else:
                    print(f"Summary for {id} passed the check_summary function")
    
        except Exception as e:
            print(f"Error processing item with id {id}: {e}")
            print(f"Deleting {id} because it is malformed")
            col.delete(ids=[id])
    

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
            

async def main():
    clean_checks(fact_checks)

    routes = [
        ModelRoute(url=HttpUrl("http://luna:8080"), model_name="nemotron-3-nano:4b"),
        ModelRoute(url=HttpUrl("http://localhost:8080"), model_name="nemotron-3-nano:4b"),
    ]

    router = LlamaRouter(routes)

    semaphore = asyncio.Semaphore(2)
    ids = articles.get(ids=None)["ids"]
    await asyncio.gather(*(check_summary(id, router, semaphore) for id in ids))


if __name__ == "__main__":
    asyncio.run(main())