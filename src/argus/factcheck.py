import json
from typing import Any
import chromadb
from datetime import datetime
import ollama
from tenacity import retry, stop_after_attempt
import uuid
from threading import Thread

from argus.fixjsonformatting import URLCheckSchema
from argus.summarizearticle import summarize_article
from argus.scraper import get_page
from argus.evaluateaccuracy import Accuracy_Agent
from argus.evaluatecompleteness import Completeness_Agent
from argus.evaluatebias import Bias_Agent
from argus.timers import with_timing


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
        self.fact_check_metadata = {}
        self.fact_check_metadata["check_submitted"] = datetime.now().isoformat()

        self.article_text = None
        self.summary = None
        self.bias_rating = None
        self.key_points = []
        self.article_metadata = {}

        self.accuracy_score = None
        self.completeness_score = None
        self.accuracy_explanation = None
        self.completeness_explanation = None
        self.sources = []

        self.political_bias = None
        self.sensationalism = None
        self.emotional_language = None
        self.political_score = None
        self.sensationalism_score = None
        self.emotional_language_score = None

        self.finished = False

        self.thread = Thread(target=self.main)
        self.thread.start()

        print(f"Initialized fact check for {self.url} with ID {self.id}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "id": self.id,
            "fact_check_metadata": self.fact_check_metadata,
            "article_text": self.article_text,
            "summary": self.summary,
            "bias_rating": self.bias_rating,
            "key_points": self.key_points,
            "article_metadata": self.article_metadata,
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

    def main(self, use_long_prompts: bool = True):
        
        self.fact_check_metadata["check_started"] = datetime.now().isoformat()

        # url |> scrape |> clean -> raw article text
        with with_timing(lambda t: self.fact_check_metadata.update({"scraper_duration": t.duration_s})):
            self.article_metadata, self.article_text = get_page(self.url)

        # raw article text |> summarizer |> -> summary, key points |> chromadb (if not present)
        with with_timing(lambda t: self.fact_check_metadata.update({"summary_duration": t.duration_s})):
            self.summary, self.bias_rating, self.key_points = self.summarize_article(self.article_text, use_long_prompt=use_long_prompts)

        print(f"\n\n\nSummary for {self.url}:\n{self.summary}\nBias rating: {self.bias_rating}\nKey points: {self.key_points}\n\n\n")

        print("\nResearching article accuracy, completeness, and bias...\nThis may take a few minutes...\n")

        # evidence + article text + related article summaries + bias rating |> fact check model -> accuracy, completeness scores + explanation
        with with_timing(lambda t: self.fact_check_metadata.update({"agents_duration": t.duration_s})):
            self.fact_check(self.article_text, self.bias_rating, self.key_points, use_long_prompts=use_long_prompts)

        print(f"\n\n\nFact check results for {self.url}:\n")
        print(f"\nAccuracy score: {self.accuracy_score}\nExplanation: {self.accuracy_explanation}\nSources: {self.sources}")
        print(f"\nCompleteness score: {self.completeness_score}\nExplanation: {self.completeness_explanation}")
        print(f"\nPolitical bias: {self.political_bias}\nPolitical bias score: {self.political_score}")
        print(f"\nSensationalism: {self.sensationalism}\nSensationalism score: {self.sensationalism_score}")
        print(f"\nEmotional language: {self.emotional_language}\nEmotional language score: {self.emotional_language_score}")

        self.finished = True
        check_finished = datetime.now()
        self.fact_check_metadata["check_finished"] = check_finished.isoformat()
        started = datetime.fromisoformat(self.fact_check_metadata["check_started"])
        submitted = datetime.fromisoformat(self.fact_check_metadata["check_submitted"])
        self.fact_check_metadata["check_duration_from_start"] = (check_finished - started).total_seconds()
        self.fact_check_metadata["check_duration_from_submitted"] = (check_finished - submitted).total_seconds()

    @retry(stop=stop_after_attempt(3))
    def summarize_article(self, article_text: str, use_long_prompt: bool = True) -> tuple[str, str, list]:
        # returns json with index sentence, key points, summary, bias rating
        response = summarize_article(article_text, model=self.model, think=self.think, use_long_prompt=use_long_prompt)

        description = response["description"]  # type: ignore
        summary = response["articleSummary"]  # type: ignore
        key_points = response["points"]  # type: ignore
        bias_rating = response["biasSummary"]  # type: ignore

        try:
            self.article_collection.add(
                ids=[self.url],
                documents=[summary],
                metadatas=[{"url": self.url, "description": description, "summary": summary, "bias": bias_rating, "points": key_points, "article_text": article_text, "timestamp": datetime.now().isoformat(), "metadata": json.dumps(self.article_metadata)}],
            )
        except:
            pass

        return summary, bias_rating, key_points  # type: ignore

    def fact_check(
        self,
        article_text: str,
        bias_rating: str,
        key_points: list[str],
        use_long_prompts: bool = True,
    ) -> dict[str, Any]:

        completeness_agent = Completeness_Agent(
            article_text=article_text,
            article_metadata=self.article_metadata,
            bias_rating=bias_rating,
            key_points=key_points,
            article_collection=self.article_collection,
            use_long_prompt=use_long_prompts,
        )

        accuracy_agent = Accuracy_Agent(
            article_text=article_text,
            article_metadata=self.article_metadata,
            bias_rating=bias_rating,
            key_points=key_points,
            article_collection=self.article_collection,
            use_long_prompt=use_long_prompts,
        )

        bias_agent = Bias_Agent(
            article_text=article_text,
            article_metadata=self.article_metadata,
            bias_rating=bias_rating,
            article_collection=self.article_collection,
            use_long_prompt=use_long_prompts,
        )

        self.fact_check_metadata["completeness_agent"] = completeness_agent.agent_metadata
        self.fact_check_metadata["accuracy_agent"] = accuracy_agent.agent_metadata
        self.fact_check_metadata["bias_agent"] = bias_agent.agent_metadata

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
        self.emotional_language_score = bias_agent.bias_rating["emotional_language_score"]

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
