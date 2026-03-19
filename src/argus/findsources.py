from datetime import datetime
import ollama
import json
from ddgs import DDGS
from tenacity import retry, retry_if_exception_type, stop_after_attempt


related_sources_prompt = '''
You are a tool designed to write internet search queries to find articles related to a given article summary. You will be given a summary of an article and your task is to return a list of 5 search queries that could be used to find related articles on a search engine. The search queries should be designed to find articles that cover the same topic as the original article, but may have different perspectives or additional information.
Return these queries in a json array. Do not include any explanatory text, only return the json array.
'''

select_related_sources_prompt = '''
You are a tool designed to select the most relevant articles from a list of search results. You will be given a summary of an article and a list of search results, where each search result includes the title, URL, and a description. Your task is to select the 3 most relevant articles from the search results that are related to the original article summary. Relevance should be determined based on how closely the content of the search result matches the topic and content of the original article summary.
Return the URLs of the 3 most relevant articles in a json array. Do not include any explanatory text, only return the json array.
'''

evidence_point_prompt = '''
You are a tool designed to find evidence for a given key point. You will be given a key point and your task is to return a list of 3 search queries that could be used to find evidence for the key point on a search engine. The search queries should be designed to find articles that provide supporting or contradicting evidence for the key point.
Return these queries in a json array. Do not include any explanatory text, only return the json array.
'''

select_evidence_sources_prompt = '''
You are a tool designed to select the most relevant sources from a list of search results. You will be given a key point and a list of search results, where each search result includes the title, URL, and a description. Your task is to select the 3 most relevant sources from the search results that provide evidence for the key point. Relevance should be determined based on how closely the content of the search result matches the key point and whether it provides supporting or contradicting evidence.
Return the URLs of the 2 most relevant sources in a json array. Do not include any explanatory text, only return the json array.
'''


@retry(retry=retry_if_exception_type(json.decoder.JSONDecodeError), stop=stop_after_attempt(3))
def find_related_article_urls(summary: str) -> list[str]:

    search_terms = json.loads(ollama.generate(model="nemotron-3-nano:4b", think=True, prompt=f"{related_sources_prompt}\nCurrent date and time: {datetime.now().isoformat()}\nArticle summary: {summary}").response)
    print(f"Search terms: {search_terms}")

    results = []
    for query in search_terms:
        search_results = DDGS().text(query, max_results=5)

        for result in search_results:
            results.append(result)

    useful_urls = json.loads(ollama.generate(model="nemotron-3-nano:4b", think=True, prompt=f"{select_related_sources_prompt}\nArticle summary: {summary}\nSearch results: {results}").response)

    return useful_urls


@retry(retry=retry_if_exception_type(json.decoder.JSONDecodeError), stop=stop_after_attempt(3))
def find_evidence_urls(key_points: list[str]) -> list[list[str]]:

    evidence_urls = []

    for point in key_points:

        search_terms = json.loads(ollama.generate(model="nemotron-3-nano:4b", think=True, prompt=f"{evidence_point_prompt}\nCurrent date and time: {datetime.now().isoformat()}\nKey point: {point}").response)
        print(f"Search terms for point '{point}': {search_terms}")

        results = []
        for query in search_terms:
            search_results = DDGS().text(query, max_results=3)

            for result in search_results:
                results.append(result)

        useful_urls = json.loads(ollama.generate(model="nemotron-3-nano:4b", think=True, prompt=f"{select_evidence_sources_prompt}\nKey point: {point}\nSearch results: {results}").response)
        evidence_urls.append(useful_urls)

    return evidence_urls