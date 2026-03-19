import ollama
import json
from tenacity import retry, retry_if_exception_type, stop_after_attempt

default_prompt = '''
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
'''

reformat_prompt = '''
You are a tool designed to reformat the output of a summarization model. You will be given a string that is supposed to be in JSON format, but may have formatting issues such as extra backticks, missing or extra quotation marks, or other common formatting errors. Your task is to parse the string and return a properly formatted JSON object that matches the expected schema.
JSON schema: {
    "description": str,
    "articleSummary": str,
    "points": list[str],
    "biasSummary": str
}
Return the properly formatted JSON object. Do not include any explanatory text, only return the JSON.
'''


def summarize_article(article_text: str, model: str = "gemma3:12b", think: bool = False, prompt: str = default_prompt, keep_alive=360): 

    r = ollama.generate(model=model, prompt=f"{prompt}\nArticle text: {article_text}", think=think, keep_alive=keep_alive).response

    response = fix_json_formatting(r)

    return response


@retry(retry=retry_if_exception_type(json.decoder.JSONDecodeError), stop=stop_after_attempt(3))
def fix_json_formatting(s: str) -> str:
    
    reformatted_response = json.loads(ollama.generate(model='nemotron-3-nano:4b', think=True, prompt=f"{reformat_prompt}\nString to reformat: {s}").response)

    return reformatted_response