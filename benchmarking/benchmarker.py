# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "google-genai",
#     "numpy",
#     "ollama",
#     "pandas",
#     "pydantic",
#     "python-dotenv",
#     "rich",
#     "tenacity",
# ]
# ///

import os
from time import sleep

from dotenv import load_dotenv
import ollama
import json
from rich.progress import track
from rich import print
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from google import genai
from google.genai import types
from pydantic import BaseModel
from platform import node
from tenacity import retry, wait_exponential

load_dotenv()

# needs to benchmark the following:
# - summary
# - evaluation of summary

@dataclass
class Summarizer:
    model: str
    prompt: str

    @retry(wait=wait_exponential(1, 60))
    def evaluate(self, article_text: str, keep_alive=0):
        ollama.pull(self.model)
        
        try:
            response = ollama.generate(
                model=self.model,
                prompt=f"{self.prompt}\nArticle text: {article_text}",
                think=True,
                keep_alive=keep_alive
            )

        #if model doesn't support thinking, fall back to normal response
        except:
            response = ollama.generate(
                model=self.model,
                prompt=f"{self.prompt}\nArticle text: {article_text}",
                think=False,
                keep_alive=keep_alive
            )

        # we'll finish by unloading the model from memory
        # just in case :3

        with open(f"logs/summary_{self.model}_{response.created_at}.json", "w") as f:
            json.dump({
                "model": response.model,
                "created_at": response.created_at,
                "total_duration": response.total_duration,
                "load_duration": response.load_duration,
                "prompt_eval_count": response.prompt_eval_count,
                "prompt_eval_duration": response.prompt_eval_duration,
                "eval_count": response.eval_count,
                "eval_duration": response.eval_duration,
                "prompt": self.prompt,
                "article_text": article_text,
                "response": response.response,
                "thinking": response.thinking,
                "node": node()
            }, f, indent=4)
        return response


@dataclass
class Evaluator:
    model: str
    prompt: str

    @retry(wait=wait_exponential(1, 60))
    def evaluate(self, article_text: str, summary: str, summary_model: str):
        # use gemini
        with genai.Client(api_key=os.environ.get("GEMINI_API_KEY")) as client:
            response = client.models.generate_content(
                model=self.model,
                contents=f"{self.prompt}\nArticle: {article_text}\nSummary: {summary}\nEvaluate the summary.",
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": EvalOut.model_json_schema()
                }
            )

        response_text = json.loads(response.text)

        with open(f"logs/evaluation_{self.model}_{summary_model}_{datetime.now().isoformat()}.json", "w") as f:
            json.dump({
                'accuracy': response_text['accuracy'],
                'completeness': response_text['completeness'],
                'reasoning': response_text['reasoning'],
                'model': summary_model,
                'evalModel': self.model
            }, f, indent = 4)
        return response


@dataclass
class EvalOut(BaseModel):
    accuracy: int
    completeness: int
    reasoning: str


summarizer_prompt = '''You are a tool designed to summarize articles. You will be given the full text of an article, and your task is to return 4 things:
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

evaluator_prompt = '''You are a tool designed to rate the accuracy and completeness of article summaries. In this prompt you will be given the full text of an article, a summary of the article, and a list of key factual claims from that article. Your task is to judge the completeness and accuracy of the article and return 3 values:
An accuracy score (“accuracy”) for the summary between 0 and 100 evaluating how accurate the summary and key points are to the original text of the article,
A completeness score (“completeness”) for the summary between 0 and 100 evaluating how complete the summary and key points are and if they left out any important details,
A few sentences justification for the values you chose for accuracy and completeness (“reasoning”).

Output your answer in the provided json schema.
'''

summarizer_models = ["qwen3.5:2b", "qwen3.5:9b", "qwen3.5:27b", "glm-4.7-flash:q4_K_M", "deepseek-r1:14b", "gemma3:4b", "gemma3:12b", "gpt-oss:20b", "magistral:24b", "nemotron-3-nano:4b"]

def benchmark_article(article_file: Path):
    article_text = article_file.read_text()

    for model in track(summarizer_models, description="Benchmarking summarization models..."):
        summarizer = Summarizer(model=model, prompt=summarizer_prompt)
        summary_response = summarizer.evaluate(article_text)
        summary = summary_response.response

        if summary is None:
            print(f"[!] Model {model} did not return a summary.")
            continue

        evaluator = Evaluator(model="gemini-3.1-flash-lite-preview", prompt=evaluator_prompt)
        evaluator.evaluate(article_text, summary, model)
        sleep(5) # give a little break between articles

def benchmark_articles():
    for article_file in Path(".").glob("article*.md"):
        benchmark_article(article_file)

def benchmark_model(model_name: str):
    summarizer = Summarizer(model=model_name, prompt=summarizer_prompt)

    for article_file in track(list(Path(".").glob("article*.md")), description=f"Benchmarking {model_name}"):
        article_text = article_file.read_text()
        summary_response = summarizer.evaluate(article_text, keep_alive=60*5)
        summary = summary_response.response

        if summary is None:
            print(f"[!] Model {model_name} did not return a summary.")
            continue

        evaluator = Evaluator(model="gemini-3.1-flash-lite-preview", prompt=evaluator_prompt)
        try:
            evaluator.evaluate(article_text, summary, model_name)
        except:
            print("-skipping evaluation!-")

def benchmark_models():
    for model in track(summarizer_models, description="Benchmarking summarization models..."):
        benchmark_model(model)
        unload_model(model)

def unload_model(model_name: str):
    ollama.generate(model_name, keep_alive=0)
    sleep(10)

def main():
    for _ in track(range(1), description="Running benchmarks..."):
        benchmark_models()

if __name__ == "__main__":
    main()
