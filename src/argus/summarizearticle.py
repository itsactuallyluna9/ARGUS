import ollama
import json

default_prompt = '''You are a tool designed to summarize articles. You will be given the full text of an article, and your task is to return 4 things:
A 1 sentence description of the article for indexing purposes (“description”). This should completely describe the subject of the article without going into too much detail.
A 2-3 paragraph summary of the article (“articleSummary”). You should aim to cover the content of the article as accurately and completely as possible without editorializing or overexplaining.
A list of 3-5 key points in the article (“points”). These should focus on the factual claims made in the article. Do not comment on the accuracy of the points, only report the direct claims made by the article.
A 2-3 sentence summary of any political and reporting bias apparent from the text of the article (“biasSummary”).

Output your response in the provided json schema.

JSON schema: {
    "description": str,
    "articleSummary": str,
    "points": list[str],
    "biasSummary": str
}
'''


def summarize_article(article_text: str, model: str = "gpt-oss:20b", prompt: str = default_prompt, keep_alive=360): 

    
    r = ollama.generate(model=model, prompt=f"{prompt}\nArticle text: {article_text}", think=True, keep_alive=keep_alive).response
    response = json.loads(r.strip('```json').strip('```'))

    return response