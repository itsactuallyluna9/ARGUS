import chromadb
import pandas as pd
import numpy as np
import json
from datetime import datetime


class ArgusData(pd.DataFrame):
    """A custom DataFrame for ARGUS data, with additional methods for processing and analysis."""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.datetime = None

    def fetch_data(self, article_collection: chromadb.Collection, fact_check_collection: chromadb.Collection):
        """Fetch data from the ChromaDB collection and populate the DataFrame."""

        self.articles = article_collection
        self.fact_checks = fact_check_collection

        article_data = self.articles.get()
        fact_check_data = self.fact_checks.get()

        article_urls = article_data["ids"]
        article_docs = article_data["documents"]
        article_metas = article_data["metadatas"]

        fact_check_docs = fact_check_data["documents"]

        try:
            self.article_df = pd.DataFrame(
                {
                    "url": article_urls,
                    "summary": article_docs,
                    "description": [meta["description"] for meta in article_metas],  # type: ignore
                    "article_text": [meta["article_text"] for meta in article_metas],  # type: ignore
                    "bias": [meta["bias"] for meta in article_metas],  # type: ignore
                    "points": [meta["points"] for meta in article_metas],  # type: ignore
                    "timestamp": [meta["timestamp"] for meta in article_metas],  # type: ignore
                }
            )
        except:
            self.article_df = pd.DataFrame()

        try:
            self.fact_check_df = pd.DataFrame(
                {
                    "url": [json.loads(doc)["url"] for doc in fact_check_docs],  # type: ignore
                    "id": [json.loads(doc)["id"] for doc in fact_check_docs],  # type: ignore
                    "article_text": [json.loads(doc)["article_text"] for doc in fact_check_docs], # type: ignore
                    "summary": [json.loads(doc)["summary"] for doc in fact_check_docs], # type: ignore
                    "bias_rating": [json.loads(doc)["bias_rating"] for doc in fact_check_docs], # type: ignore
                    "accuracy_score": [json.loads(doc)["accuracy_score"] for doc in fact_check_docs], # type: ignore
                    "accuracy_explanation": [json.loads(doc)["accuracy_explanation"] for doc in fact_check_docs], # type: ignore
                    "sources": [json.loads(doc)["sources"] for doc in fact_check_docs], # type: ignore
                    "completeness_score": [json.loads(doc)["completeness_score"] for doc in fact_check_docs], # type: ignore
                    "completeness_explanation": [json.loads(doc)["completeness_explanation"] for doc in fact_check_docs], # type: ignore
                    "political_bias": [json.loads(doc)["political_bias"] for doc in fact_check_docs], # type: ignore
                    "sensationalism": [json.loads(doc)["sensationalism"] for doc in fact_check_docs], # type: ignore
                    "emotional_language": [json.loads(doc)["emotional_language"] for doc in fact_check_docs], # type: ignore
                    "political_score": [json.loads(doc)["political_score"] for doc in fact_check_docs], # type: ignore
                    "sensationalism_score": [json.loads(doc)["sensationalism_score"] for doc in fact_check_docs], # type: ignore
                    "emotional_language_score": [json.loads(doc)["emotional_language_score"] for doc in fact_check_docs], # type: ignore
                    "finished": [json.loads(doc)["finished"] for doc in fact_check_docs], # type: ignore
                    "fact_check_metadata": [json.loads(doc)["fact_check_metadata"] for doc in fact_check_docs], # type: ignore
                    "key_points": [json.loads(doc)["key_points"] for doc in fact_check_docs], # type: ignore
                    "article_metadata": [json.loads(doc)["article_metadata"] for doc in fact_check_docs], # type: ignore
                }
            )
        
        except:
            self.fact_check_df = pd.DataFrame()

        self.timestamp = datetime.now().isoformat()


    def dict(self):
        """Convert the DataFrame to a dictionary format suitable for JSON serialization."""

        articles = []

        for i in range(len(self.article_df)):
            try:

                article_dict = {
                    "url": self.article_df["url"][i],
                    "timestamp": self.article_df["timestamp"][i],
                    "summary": self.article_df["summary"][i],
                    "description": self.article_df["description"][i],
                    "article_text": self.article_df["article_text"][i],
                    "bias": self.article_df["bias"][i],
                }

                points = self.article_df["points"][i]
                for j in range(len(points)):
                    article_dict[f"point{j}"] = points[j]

                articles.append(article_dict)

            except:
                pass

        fact_checks = []

        for i in range(len(self.fact_check_df)):
            try:

                fact_check_dict = {
                    "url": self.fact_check_df["url"][i],
                    "uuid": self.fact_check_df["id"][i],
                    "article_text": self.fact_check_df["article_text"][i],
                    "summary": self.fact_check_df["summary"][i],
                    "bias_rating": self.fact_check_df["bias_rating"][i],
                    "accuracy_score": int(self.fact_check_df["accuracy_score"][i]),
                    "accuracy_explanation": self.fact_check_df["accuracy_explanation"][i],
                    "sources": self.fact_check_df["sources"][i],
                    "completeness_score": int(self.fact_check_df["completeness_score"][i]),
                    "completeness_explanation": self.fact_check_df["completeness_explanation"][i],
                    "political_bias": self.fact_check_df["political_bias"][i],
                    "sensationalism": self.fact_check_df["sensationalism"][i],
                    "emotional_language": self.fact_check_df["emotional_language"][i],
                    "political_score": int(self.fact_check_df["political_score"][i]),
                    "sensationalism_score": int(self.fact_check_df["sensationalism_score"][i]),
                    "emotional_language_score": int(self.fact_check_df["emotional_language_score"][i]),
                    "finished": self.fact_check_df["finished"][i]
                }

                for column in self.fact_check_df["fact_check_metadata"][i].keys():
                    fact_check_dict[column] = self.fact_check_df["fact_check_metadata"][i][column]

                points = self.fact_check_df["key_points"][i]
                for j in range(len(points)):
                    fact_check_dict[f"point{j}"] = points[j]

                for column in self.fact_check_df["article_metadata"][i].keys():
                    
                    if type(self.fact_check_df["article_metadata"][i][column]) == np.int64:
                        fact_check_dict[column] = int(self.fact_check_df["article_metadata"][i][column])
                    
                    fact_check_dict[column] = self.fact_check_df["article_metadata"][i][column]

                print(fact_check_dict)

                fact_checks.append(fact_check_dict)

            except:
                pass

        return {
            "articles": articles,
            "fact_checks": fact_checks,
            "timestamp": self.timestamp
        }
    


if __name__ == "__main__":
    chroma_client = chromadb.HttpClient(host="localhost", port=8000)

    article_collection = chroma_client.get_or_create_collection(name="articles")
    fact_check_collection = chroma_client.get_or_create_collection(name="fact_checks")

    argus_data = ArgusData()
    argus_data.fetch_data(article_collection, fact_check_collection)

    data = argus_data.dict()

    print(data["fact_checks"])