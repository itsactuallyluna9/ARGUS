from typing import Any

import chromadb
from datetime import datetime
from tenacity import retry, stop_after_attempt

from flask import jsonify
from argus.summarizearticle import summarize_article
from argus.scraper import get_page
from argus.findsources import find_related_article_urls, find_evidence_urls



class FactCheck:


    def __init__(self, url: str, article_collection: chromadb.Collection, summarizer_model: str = "gemma3:12b", think: bool = False):

        self.url = url
        self.article_collection = article_collection
        self.model = summarizer_model
        self.think = think

        self.article_text = 'Empty for now!'
        self.summary = 'Empty for now!'
        self.bias_rating = 'Empty for now!'
        self.key_points = []
        self.related_summaries = []
        self.evidence_summaries = []

        self.accuracy_score = 0
        self.completeness_score = 0
        self.explanation = 'Empty for now!'

        self.finished = False

        self.main()

    
    def to_dict(self) -> dict[str, Any]:
        
        return {
            "url": self.url,
            "article_text": self.article_text,
            "summary": self.summary,
            "bias_rating": self.bias_rating,
            "key_points": self.key_points,
            "related_summaries": self.related_summaries,
            "evidence_summaries": self.evidence_summaries,
            "accuracy_score": self.accuracy_score,
            "completeness_score": self.completeness_score,
            "explanation": self.explanation,
            "finished": self.finished
         }
    

    def main(self):
        
        # url |> scrape |> clean -> raw article text
        self.article_text = get_page(self.url)

        # raw article text |> summarizer |> -> summary, key points |> chromadb (if not present)
        self.summary, self.bias_rating, self.key_points = self.summarize_article(self.article_text)
        print(f"Summary for {self.url}:\n{self.summary}\n\nBias rating: {self.bias_rating}\n\nKey points:\n{self.key_points}")

        # summary |> search web for related articles |> summarizer |> chromadb
        # summary |> find related articles in chromadb -> related article summaries
        self.related_summaries = self.find_related_articles(self.summary)
        print(f"Related summaries for {self.url}:\n{self.related_summaries}")

        # key claims |> search web for evidence -> evidence
        self.evidence_summaries = self.find_evidence(self.key_points)
        print(f"Evidence summaries for {self.url}:\n{self.evidence_summaries}")

        # evidence + article summary + related article summaries + bias rating |> fact check model -> accuracy, completeness scores + explanation
        self.fact_check(self.summary, self.bias_rating, self.related_summaries, self.evidence_summaries)

        self.finished = True

        print(f"Fact check results for {self.url}:\nAccuracy: {self.accuracy_score}\nCompleteness: {self.completeness_score}\nExplanation: {self.explanation}")    

    
    def related_article_summaries(self):

        self.article_text = get_page(self.url)
        self.summary, self.bias_rating, self.key_points = self.summarize_article(self.article_text)

        urls = find_related_article_urls(self.summary)

        for url in urls:
            curr_summary, _, _ = self.summarize_article(get_page(url))
            self.related_summaries.append((curr_summary, url))

        return jsonify({
            "summary": self.summary,
            "bias_rating": self.bias_rating,
            "key_points": self.key_points,
            "related_summaries": self.related_summaries
        })


    @retry(stop = stop_after_attempt(3))
    def summarize_article(self, article_text: str) -> tuple[str, str, list]:

        #returns json with index sentence, key points, summary, bias rating
        response = summarize_article(article_text, model=self.model, think=self.think)

        description = response['description'] # type: ignore
        summary = response['articleSummary'] # type: ignore
        key_points = response['points'] # type: ignore
        bias_rating = response['biasSummary'] # type: ignore

        try:
            self.article_collection.add(
                ids=[self.url], 
                documents=[summary], 
                metadatas=[{
                    "url": self.url, 
                    "description": description, 
                    "summary": summary, 
                    "bias": bias_rating, 
                    "points": key_points, 
                    "article_text": article_text, 
                    "timestamp": datetime.now().isoformat()
                }]
            )
        except:
            pass
        
        return summary, bias_rating, key_points # type: ignore
    
    
    def find_related_articles(self, summary: str) -> list[tuple[str, str]]:
        # returns list of tuples of (related article summary, related article url)
        
        urls = find_related_article_urls(summary)
        summaries = []

        for url in urls:
            if not self.article_collection.get(ids=[url]):
                curr_summary, _, _ = self.summarize_article(get_page(url))
                summaries.append((curr_summary, url))

        related_from_db = self.article_collection.query(query_texts=[summary], n_results=7)

        print(related_from_db)

        for i in range(len(related_from_db['ids'])):
            summaries.append((related_from_db['documents'][i], related_from_db['ids'][i])) # type: ignore

        return summaries
    
    
    def find_evidence(self, key_points: list[str]) -> list[tuple[str, str]]:
        # returns list of tuples of (evidence summary, evidence url)
        evidence_urls = find_evidence_urls(key_points)
        evidence = []

        for urls in evidence_urls:
            for url in urls:

                print(f"Summarizing evidence source: {url}")

                curr_summary, _, _ = self.summarize_article(get_page(url))
                evidence.append((curr_summary, url))

        return evidence
    

    #PLACEHOLDER IMPLEMENTATION
    def fact_check(self, summary: str, bias_rating: str, related_summaries: list[tuple[str, str]], evidence_summaries: list[tuple[str, str]]) -> dict[str, Any]:
        # Placeholder for actual implementation
        self.accuracy_score = 80
        self.completeness_score = 70
        self.explanation = "The summary is mostly accurate but misses some key points. The bias rating is fair given the content of the article. The related articles and evidence support most of the claims made in the summary."
        return self.to_dict()
    


if __name__ == "__main__":

    # chroma_client = chromadb.Client()
    chroma_client = chromadb.HttpClient(host="localhost", port=8000)
    article_collection = chroma_client.get_or_create_collection(name="articles")

    f = FactCheck("https://www.nbcnews.com/politics/donald-trump/pearl-harbor-joke-iran-operation-meeting-japan-prime-minister-war-rcna264325?utm_source=firefox-newtab-en-us", article_collection)