from datetime import datetime
import ollama
import json
from ddgs import DDGS


related_sources_prompt = '''
You are a tool designed to write internet search queries to find articles related to a given article summary. You will be given a summary of an article and your task is to return a list of 5 search queries that could be used to find related articles on a search engine. The search queries should be designed to find articles that cover the same topic as the original article, but may have different perspectives or additional information.
Return these queries in a json array. Do not include any explanatory text, only return the json array.
'''

select_sources_prompt = '''
You are a tool designed to select the most relevant articles from a list of search results. You will be given a summary of an article and a list of search results, where each search result includes the title, URL, and a description. Your task is to select the 3 most relevant articles from the search results that are related to the original article summary. Relevance should be determined based on how closely the content of the search result matches the topic and content of the original article summary.
Return the URLs of the 3 most relevant articles in a json array. Do not include any explanatory text, only return the json array.
'''


def find_related_article_urls(summary: str) -> list[str]:

    search_terms = json.loads(ollama.generate(model="nemotron-3-nano:4b", think=True, prompt=f"{related_sources_prompt}\nCurrent date and time: {datetime.now().isoformat()}\nArticle summary: {summary}").response)
    print(f"Search terms: {search_terms}")

    results = []
    for query in search_terms:
        search_results = DDGS().text(query, max_results=5)

        for result in search_results:
            results.append(result)

    useful_urls = json.loads(ollama.generate(model="nemotron-3-nano:4b", think=True, prompt=f"{select_sources_prompt}\nArticle summary: {summary}\nSearch results: {results}").response)

    return useful_urls


def find_evidence_urls(key_points: list[str]) -> list[list[str]]:
    # Placeholder for actual implementation
    return [["https://example.com/evidence1", "https://example.com/evidence2"] for _ in key_points]

print(find_related_article_urls("This is a summary of an article about the economy. The article discusses recent trends in the stock market, the impact of inflation on consumer spending, and predictions for future economic growth."))
