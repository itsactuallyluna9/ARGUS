import json
from typing import Any
from urllib import response
import chromadb
from datetime import datetime
import ollama
from tenacity import retry, stop_after_attempt
import uuid
from threading import Thread

from argus.fixjsonformatting import URLCheckSchema
from argus.summarizearticle import summarize_article
from argus.scraper import get_page
from argus.findsources import find_related_article_urls
from argus.evaluateaccuracy import Accuracy_Agent
from argus.evaluatecompleteness import Completeness_Agent
from argus.evaluatebias import Bias_Agent


class FactCheck:
    def __init__(
        self,
        url: str,
        article_collection: chromadb.Collection,
        summarizer_model: str = "gemma3:12b",
        think: bool = False,
    ):

        self.url = url
        self.id = uuid.uuid3(uuid.NAMESPACE_DNS, url).hex

        self.article_collection = article_collection
        self.model = summarizer_model
        self.think = think

        self.article_text = "Empty for now!"
        self.summary = "Empty for now!"
        self.bias_rating = "Empty for now!"
        self.key_points = []

        self.accuracy_score = 0
        self.completeness_score = 0
        self.accuracy_explanation = "Empty for now!"
        self.completeness_explanation = "Empty for now!"
        self.sources = []

        self.political_bias = "Empty for now!"
        self.sensationalism = "Empty for now!"
        self.emotional_language = "Empty for now!"
        self.political_score = 0
        self.sensationalism_score = 0
        self.emotional_language_score = 0

        self.finished = False

        self.thread = Thread(target=self.main)
        self.thread.start()

        print(f"Initialized fact check for {self.url} with ID {self.id}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "id": self.id,
            "article_text": self.article_text,
            "summary": self.summary,
            "bias_rating": self.bias_rating,
            "key_points": self.key_points,
            "accuracy_score": self.accuracy_score,
            "completeness_score": self.completeness_score,
            "accuracy_explanation": self.accuracy_explanation,
            "completeness_explanation": self.completeness_explanation,
            "sources": self.sources,
            "political_bias": self.political_bias,
            "sensationalism": self.sensationalism,
            "emotional_language": self.emotional_language,
            "political_score": self.political_score,
            "sensationalism_score": self.sensationalism_score,
            "emotional_language_score": self.emotional_language_score,
            "finished": self.finished,
        }

    def main(self):

        # url |> scrape |> clean -> raw article text
        self.article_text = get_page(self.url)

        # raw article text |> summarizer |> -> summary, key points |> chromadb (if not present)
        self.summary, self.bias_rating, self.key_points = self.summarize_article(
            self.article_text
        )

        print(
            f"\n\n\nSummary for {self.url}:\n{self.summary}\nBias rating: {self.bias_rating}\nKey points: {self.key_points}\n\n\n"
        )

        print(
            "\nResearching article accuracy, completeness, and bias...\nThis may take a few minutes...\n"
        )

        # evidence + article text + related article summaries + bias rating |> fact check model -> accuracy, completeness scores + explanation
        self.fact_check(self.article_text, self.bias_rating, self.key_points)

        print(f"\n\n\nFact check results for {self.url}:\n")
        print(
            f"\nAccuracy score: {self.accuracy_score}\nExplanation: {self.accuracy_explanation}\nSources: {self.sources}"
        )
        print(
            f"\nCompleteness score: {self.completeness_score}\nExplanation: {self.completeness_explanation}"
        )
        print(
            f"\nPolitical bias: {self.political_bias}\nPolitical bias score: {self.political_score}"
        )
        print(
            f"\nSensationalism: {self.sensationalism}\nSensationalism score: {self.sensationalism_score}"
        )
        print(
            f"\nEmotional language: {self.emotional_language}\nEmotional language score: {self.emotional_language_score}"
        )

        self.finished = True

    @retry(stop=stop_after_attempt(3))
    def summarize_article(self, article_text: str) -> tuple[str, str, list]:
        # returns json with index sentence, key points, summary, bias rating
        response = summarize_article(article_text, model=self.model, think=self.think)

        description = response["description"]  # type: ignore
        summary = response["articleSummary"]  # type: ignore
        key_points = response["points"]  # type: ignore
        bias_rating = response["biasSummary"]  # type: ignore

        try:
            self.article_collection.add(
                ids=[self.url],
                documents=[summary],
                metadatas=[
                    {
                        "url": self.url,
                        "description": description,
                        "summary": summary,
                        "bias": bias_rating,
                        "points": key_points,
                        "article_text": article_text,
                        "timestamp": datetime.now().isoformat(),
                    }
                ],
            )
        except:
            pass

        return summary, bias_rating, key_points  # type: ignore

    def find_related_articles(self, summary: str) -> list[tuple[str, str]]:
        # returns list of tuples of (related article summary, related article url)

        urls = find_related_article_urls(summary)
        summaries = []

        for url in urls:
            if len(self.article_collection.get(ids=[url])["ids"]) == 0:
                print(
                    f"Related article {url} not found in database, summarizing and adding to database..."
                )

                self.summarize_article(get_page(url))

        related = self.article_collection.query(query_texts=[summary], n_results=5)

        for i in range(len(related["ids"])):
            summaries.append((related["documents"][i], related["ids"][i]))  # type: ignore

        return summaries

    def fact_check(
        self,
        article_text: str,
        bias_rating: str,
        key_points: list[str],
    ) -> dict[str, Any]:

        completeness_agent = Completeness_Agent(
            article_text=article_text,
            bias_rating=bias_rating,
            key_points=key_points,
            article_collection=self.article_collection,
        )

        accuracy_agent = Accuracy_Agent(
            article_text=article_text,
            bias_rating=bias_rating,
            key_points=key_points,
            article_collection=self.article_collection,
        )

        bias_agent = Bias_Agent(
            article_text=article_text,
            bias_rating=bias_rating,
            article_collection=self.article_collection,
        )

        completeness_agent.thread.join()
        accuracy_agent.thread.join()
        bias_agent.thread.join()

        self.accuracy_score = accuracy_agent.accuracy_score
        self.accuracy_explanation = accuracy_agent.accuracy_explanation
        self.sources = accuracy_agent.sources

        self.completeness_score = completeness_agent.completeness_score
        self.completeness_explanation = completeness_agent.completeness_explanation

        self.political_bias = bias_agent.bias_rating["political_bias"]
        self.sensationalism = bias_agent.bias_rating["sensationalism"]
        self.emotional_language = bias_agent.bias_rating["emotional_language"]
        self.political_score = bias_agent.bias_rating["political_score"]
        self.sensationalism_score = bias_agent.bias_rating["sensationalism_score"]
        self.emotional_language_score = bias_agent.bias_rating[
            "emotional_language_score"
        ]

        return self.to_dict()


def check_url(url: str) -> bool:
    # check if url is valid and can be scraped
    try:
        text = get_page(url)

        response = ollama.generate(
            model="nemotron-3-nano:4b",
            prompt=f'You are a tool that verifies if text scraped from a URL is a valid page or if it is blocked. You will be given the text output of a web scraper, and your task is to decide if the text was successfully scraped or if there was an error. Return "True" if it is a valid page, "False" if it\'s a cookies message or some other error.\n\nScraper output from page {url}: {text}',
            format=URLCheckSchema.model_json_schema(),
        )

        return json.loads(response.response)["isValid"]  # type: ignore

    except:
        return False


if __name__ == "__main__":
    chromadb_client = chromadb.HttpClient(host="localhost", port=8000)
    url = "https://www.theguardian.com/tv-and-radio/2026/mar/24/power-the-downfall-of-huw-edwards-review-martin-clunes-is-sickening"

    check = FactCheck(url, chromadb_client.get_or_create_collection(name="articles"))

    check.thread.join()
