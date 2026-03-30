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

        fact_check_docs = fact_check_data["documents"]

        try:
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
        except:
            self.article_df = pd.DataFrame()

        try:
            self.fact_check_df = pd.json_normalize(json.loads(fact_check_docs[0])) # type: ignore
            for i in range(1, len(fact_check_docs)): # type: ignore
                doc = fact_check_docs[i] # type: ignore
                json_doc = json.loads(doc)
                self.fact_check_df = pd.concat([self.fact_check_df, pd.json_normalize(json_doc)], ignore_index=True) # type: ignore

        except:
            self.fact_check_df = pd.DataFrame()

        self.timestamp = datetime.now().isoformat()


    def dict(self):
        """Convert the DataFrame to a dictionary format suitable for JSON serialization."""

        articles = []

        try:
            for i in range(len(self.article_df["url"])):

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

        try:
            for i in range(len(self.fact_check_df)):

                fact_check_dict = {
                    "url": self.fact_check_df["url"][i],
                    "uuid": self.fact_check_df["id"][i],
                    "article_text": self.fact_check_df["article_text"][i],
                    "summary": self.fact_check_df["summary"][i],
                    "bias_rating": self.fact_check_df["bias_rating"][i],
                    "accuracy_score": self.fact_check_df["accuracy_score"][i],
                    "accuracy_explanation": self.fact_check_df["accuracy_explanation"][i],
                    "sources": self.fact_check_df["sources"][i],
                    "completeness_score": self.fact_check_df["completeness_score"][i],
                    "completeness_explanation": self.fact_check_df["completeness_explanation"][i],
                    "political_bias": self.fact_check_df["political_bias"][i],
                    "sensationalism": self.fact_check_df["sensationalism"][i],
                    "emotional_language": self.fact_check_df["emotional_language"][i],
                    "political_score": self.fact_check_df["political_score"][i],
                    "sensationalism_score": self.fact_check_df["sensationalism_score"][i],
                    "emotional_language_score": self.fact_check_df["emotional_language_score"][i],
                    "finished": self.fact_check_df["finished"][i]
                }

                for column in self.fact_check_df["fact_check_metadata"][i].keys():
                    fact_check_dict[column] = json.loads(self.fact_check_df["fact_check_metadata"][i])[column]

                points = self.fact_check_df["key_points"][i]
                for j in range(len(points)):
                    fact_check_dict[f"point{j}"] = points[j]

                for column in self.fact_check_df["article_metadata"][i].keys():
                    fact_check_dict[column] = json.loads(self.fact_check_df["article_metadata"][i])[column]

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

    print(argus_data.dict())