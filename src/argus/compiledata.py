import chromadb
import pandas as pd
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

        fact_check_uuids = fact_check_data["ids"]
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
            self.fact_check_df = pd.json_normalize(json.loads(fact_check_docs[0]))  # type: ignore
            for i in range(1, len(fact_check_docs)):  # type: ignore
                doc = fact_check_docs[i]  # type: ignore
                json_doc = json.loads(doc)  # type: ignore
                self.fact_check_df = pd.concat([self.fact_check_df, pd.json_normalize(json_doc)], ignore_index=True)  # type: ignore

        except:
            self.fact_check_df = pd.DataFrame()

        self.timestamp = datetime.now().isoformat()


if __name__ == "__main__":
    chroma_client = chromadb.HttpClient(host="localhost", port=8000)

    article_collection = chroma_client.get_or_create_collection(name="articles")
    fact_check_collection = chroma_client.get_or_create_collection(name="fact_checks")

    argus_data = ArgusData()
    argus_data.fetch_data(article_collection, fact_check_collection)
