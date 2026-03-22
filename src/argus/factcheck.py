from typing import Any
import chromadb
from datetime import datetime
from tenacity import retry, stop_after_attempt
from flask import jsonify
import uuid

from argus.summarizearticle import summarize_article
from argus.scraper import get_page
from argus.findsources import find_related_article_urls
from argus.evaluatequality import evaluate_accuracy, evaluate_completeness


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
        self.related_summaries = []

        self.accuracy_score = 0
        self.completeness_score = 0
        self.accuracy_explanation = "Empty for now!"
        self.completeness_explanation = "Empty for now!"
        self.sources = []

        self.finished = False

        self.main()

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "id": self.id,
            "article_text": self.article_text,
            "summary": self.summary,
            "bias_rating": self.bias_rating,
            "key_points": self.key_points,
            "related_summaries": self.related_summaries,
            "accuracy_score": self.accuracy_score,
            "completeness_score": self.completeness_score,
            "accuracy_explanation": self.accuracy_explanation,
            "completeness_explanation": self.completeness_explanation,
            "sources": self.sources,
            "finished": self.finished,
        }

    def main(self):
        print(f"Beginning fact check for {self.url}")

        # url |> scrape |> clean -> raw article text
        self.article_text = get_page(self.url)

        # raw article text |> summarizer |> -> summary, key points |> chromadb (if not present)
        self.summary, self.bias_rating, self.key_points = self.summarize_article(
            self.article_text
        )
        print(
            f"\n\n\nSummary for {self.url}:\n{self.summary}\nBias rating: {self.bias_rating}\nKey points: {self.key_points}\n\n\n"
        )

        # summary |> search web for related articles |> summarizer |> chromadb
        # summary |> find related articles in chromadb -> related article summaries
        self.related_summaries = self.find_related_articles(self.summary)

        print("Related articles found, now researching article accuracy...")

        # evidence + article text + related article summaries + bias rating |> fact check model -> accuracy, completeness scores + explanation
        self.fact_check(
            self.article_text, self.bias_rating, self.key_points, self.related_summaries
        )

        self.finished = True

        print(
            f"\n\n\nFact check results for {self.url}:\nAccuracy: {self.accuracy_score}\nExplanation: {self.accuracy_explanation}\nCompleteness: {self.completeness_score}\nExplanation: {self.completeness_explanation}\n\n\n"
        )

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
        related_summaries: list[tuple[str, str]],
    ) -> dict[str, Any]:
        self.completeness_score, self.completeness_explanation = evaluate_completeness(
            article_text=article_text,
            bias_rating=bias_rating,
            related_summaries=related_summaries,
        )

        self.accuracy_score, self.accuracy_explanation, self.sources = (
            evaluate_accuracy(
                article_text=article_text,
                bias_rating=bias_rating,
                related_summaries=related_summaries,
                article_collection=self.article_collection,
            )
        )

        return self.to_dict()


if __name__ == "__main__":
    chroma_client = chromadb.HttpClient(host="localhost", port=8000)
    article_collection = chroma_client.get_or_create_collection(name="articles")

    url = input("Enter an article URL to fact check: ")

    f = FactCheck(url, article_collection)
