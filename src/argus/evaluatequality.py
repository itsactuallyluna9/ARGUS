import json
import ollama
from tenacity import retry, stop_after_attempt, retry_if_exception_type

default_prompt = '''
You are a tool designed to evaluate the factuality and quality of an article summary.
You will be given the text of an article, a bias rating for the article, a list of summaries of related articles (including their URLs), and a list of article summaries evidencing key points from the article.
Your task is to evaluate the how factually accurate the article is, and how complete the reporting of the article is compared to the related articles' summaries.
You should return an accuracy score between 0 and 100 evaluating how factually accurate the article is based on the evidence provided, a completeness score between 0 and 100 evaluating how complete the article's reporting is and if they left out any important details, and a few sentences justification for the values you chose for accuracy and completeness.
Output your answer in the provided json schema.
JSON schema: {
    "accuracy": int,
    "completeness": int,
    "reasoning": str
}
'''

reformat_prompt = '''
You are a tool designed to reformat the output of a summarization model. You will be given a string that is supposed to be in JSON format, but may have formatting issues such as extra backticks, missing or extra quotation marks, or other common formatting errors. Your task is to parse the string and return a properly formatted JSON object that matches the expected schema.
JSON schema: {
    "accuracy": int,
    "completeness": int,
    "reasoning": str
}
Return the properly formatted JSON object. Do not include any explanatory text, only return the JSON.
'''



def evaluate_article(article_text: str, bias_rating: str, related_summaries: list[tuple[str, str]], evidence_summaries: list[list[tuple[str, str]]], evaluation_model: str = 'gpt-oss:20b', think: bool = True, prompt: str = default_prompt) -> tuple[int, int, str]:

    response = ollama.generate(model=evaluation_model, think=think, prompt=f"{prompt}\nArticle text: {article_text}\nBias rating: {bias_rating}\nRelated summaries and URLs: {related_summaries}\nEvidence summaries and URLs: {evidence_summaries}")

    evaluation = fix_json_formatting(response.response)

    accuracy_score = int(evaluation['accuracy']) # type: ignore
    completeness_score = int(evaluation['completeness']) # type: ignore
    explanation = evaluation['reasoning'] # type: ignore

    return accuracy_score, completeness_score, explanation


@retry(retry=retry_if_exception_type(json.decoder.JSONDecodeError), stop=stop_after_attempt(3))
def fix_json_formatting(s: str) -> str:
    
    reformatted_response = json.loads(ollama.generate(model='nemotron-3-nano:4b', think=True, prompt=f"{reformat_prompt}\nString to reformat: {s}").response)

    return reformatted_response