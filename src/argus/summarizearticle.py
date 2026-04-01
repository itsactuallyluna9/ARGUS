import asyncio
import os
import ollama
import json

from argus.fixjsonformatting import SummarizeArticleSchema
from argus.llamarouter import LlamaRouter

default_prompt = """
You are a tool designed to summarize articles. You will be given the full text of an article, and your task is to return 4 things:
A 1 sentence description of the article for indexing purposes (“description”). This should completely describe the subject of the article without going into too much detail.
A 2-3 paragraph summary of the article (“articleSummary”). You should aim to cover the content of the article as accurately and completely as possible without editorializing or overexplaining.
A list of 2-3 key points in the article (“points”). These should focus on the factual claims made in the article. Do not comment on the accuracy of the points, only report the direct claims made or implied by the article.
A 2-3 sentence summary of any political and reporting bias apparent from the text of the article (“biasSummary”).

Output your response in the provided json schema.

JSON schema: {
    "description": str,
    "articleSummary": str,
    "points": list[str],
    "biasSummary": str
}
"""


async def summarize_article(article_text: str, router: LlamaRouter, model: str = "nemotron-3-nano:4b", think: bool = False, use_long_prompt: bool = True, keep_alive=360):

    if use_long_prompt:
        with open(os.path.join(os.getcwd(), "prompts", "summarizeprompt.md"), "r") as f:
            prompt = f.read()
    else:
        prompt = default_prompt

    r = await asyncio.gather(router.generate(
        model=model,
        prompt=f"{prompt}\nArticle text: {article_text}",
        think=think,
        format=json.dumps(SummarizeArticleSchema.model_json_schema()) # type: ignore
    ))
    response = json.loads(r[0].content) # type: ignore

    return response


if __name__ == "__main__":
    router = LlamaRouter(
        ips=["localhost"],
        ports=[8001],
        models=["glm-4.7-flash"]
    )

    url = "https://www.theguardian.com/tv-and-radio/2026/mar/24/power-the-downfall-of-huw-edwards-review-martin-clunes-is-sickening"

    article_text = "Huw Edwards, the BBC newsreader, has been accused of sexual misconduct by multiple"

    response = asyncio.run(summarize_article(article_text, router, model="glm-4.7-flash", think=False, use_long_prompt=False))

    print(response)