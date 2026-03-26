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

        self.article_df = pd.DataFrame(
            {
                "url": article_urls,
                "summary": article_docs,
                "description": [meta["description"] for meta in article_metas], # type: ignore
                "article_text": [meta["article_text"] for meta in article_metas], # type: ignore
                "bias": [meta["bias"] for meta in article_metas], # type: ignore
                "points": [meta["points"] for meta in article_metas], # type: ignore
                "timestamp": [meta["timestamp"] for meta in article_metas], # type: ignore
            }
        )

        self.fact_check_df = pd.DataFrame(
            {
                "id": fact_check_uuids,
                "url": [json.loads(doc)["url"] for doc in fact_check_docs], # type: ignore
                "article_text": [json.loads(doc)["article_text"] for doc in fact_check_docs], # type: ignore
                "summary": [json.loads(doc)["summary"] for doc in fact_check_docs], # type: ignore
                "bias_rating": [json.loads(doc)["bias_rating"] for doc in fact_check_docs], # type: ignore
                "key_points": [json.loads(doc)["key_points"] for doc in fact_check_docs], # type: ignore
                "accuracy_score": [json.loads(doc)["accuracy_score"] for doc in fact_check_docs], # type: ignore
                "completeness_score": [json.loads(doc)["completeness_score"] for doc in fact_check_docs], # type: ignore
                "accuracy_explanation": [json.loads(doc)["accuracy_explanation"] for doc in fact_check_docs], # type: ignore
                "completeness_explanation": [json.loads(doc)["completeness_explanation"] for doc in fact_check_docs], # type: ignore
                "sources": [json.loads(doc)["sources"] for doc in fact_check_docs], # type: ignore
                "political_bias": [json.loads(doc)["political_bias"] for doc in fact_check_docs], # type: ignore
                "sensationalism": [json.loads(doc)["sensationalism"] for doc in fact_check_docs], # type: ignore
                "emotional_language": [json.loads(doc)["emotional_language"] for doc in fact_check_docs], # type: ignore
                "political_score": [json.loads(doc)["political_score"] for doc in fact_check_docs], # type: ignore
                "sensationalism_score": [json.loads(doc)["sensationalism_score"] for doc in fact_check_docs], # type: ignore
                "emotional_language_score": [json.loads(doc)["emotional_language_score"] for doc in fact_check_docs],# type: ignore
                "finished": [json.loads(doc)["finished"] for doc in fact_check_docs] # type: ignore
            }
        )

        self.timestamp = datetime.now().isoformat()
        


if __name__ == "__main__":
    chroma_client = chromadb.HttpClient(host="localhost", port=8000)

    article_collection = chroma_client.get_or_create_collection(name="articles")
    fact_check_collection = chroma_client.get_or_create_collection(name="fact_checks")

    argus_data = ArgusData()
    argus_data.fetch_data(article_collection, fact_check_collection)