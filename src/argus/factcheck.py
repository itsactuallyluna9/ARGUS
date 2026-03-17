import chromadb
import datetime

class FactCheck:
    def __init__(self, url: str, article_collection: chromadb.Collection):
        self.url = url
        self.article_collection = article_collection

        self.article_text = 'Empty for now!'
        self.summary = 'Empty for now!'
        self.bias_rating = 'Empty for now!'
        self.key_points = []
        self.related_summaries = []
        self.evidence_summaries = []

        self.accuracy_score = 0
        self.completeness_score = 0
        self.explanation = 'Empty for now!'

        self.main()

    def text_from_url(self, url: str) -> str:
        # Placeholder for actual implementation
        return "Raw article text extracted from the URL."
    
    def summarize_article(self, article_text: str) -> tuple[str, str, list]:
        # Placeholder for actual implementation
        response = model.summarize(article_text)
        #returns json with index sentence, key points, summary, bias rating
        description = response['description']
        summary = response['articleSummary']
        key_points = response['points']
        bias_rating = response['biasSummary']

        try:
            self.article_collection.add(ids=[self.url], documents=[summary], metadatas=[{"url": self.url, "summary": summary, "bias": bias_rating, "points": key_points, "article_text": article_text, "timestamp": datetime.now().isoformat()}])
        except:
            pass
        
        return summary, bias_rating, key_points
    
    def urls_from_summary(self, summary: str) -> list[str]:
        # Placeholder for actual implementation
        return ["https://related.article1.com", "https://related.article2.com"]
    
    def find_related_articles(self, summary: str) -> list[tuple[str, str]]:
        # returns list of tuples of (related article summary, related article url)
        
        urls = self.urls_from_summary(summary)
        summaries = []

        for url in urls:
            if not self.article_collection.get(ids=[url]):
                curr_summary, bias_rating, key_points = self.summarize_article(self.text_from_url(url))
                summaries.append((curr_summary, url))

        for result in self.article_collection.query(query_texts=[summary], n_results=5)['documents'][0]:
            summaries.append((result, self.article_collection.get(ids=[result])['metadatas'][0]['url']))

        return summaries
    
    def find_evidence(self, key_points: list[str]) -> list[tuple[str, str]]:
        # returns list of tuples of (evidence summary, evidence url)
        evidence = []
        for point in key_points:
            #placeholder for actual implementation
            evidence.append((f"Evidence summary for key point: {point}", f"https://evidence.url/for/{point}"))
        return evidence

    def main(self):
        
        # url |> scrape |> clean -> raw article text
        self.article_text = self.text_from_url(self.url)
        # raw article text |> summarizer |> -> summary, key points |> chromadb (if not present)
        self.summary, self.bias_rating, self.key_points = self.summarize_article(self.article_text)
        # summary |> search web for related articles |> summarizer |> chromadb
        # summary |> find related articles in chromadb -> related article summaries
        self.related_summaries = self.find_related_articles(self.summary)
        # key claims |> search web for evidence -> evidence
        self.evidence_summaries = self.find_evidence(self.key_points)
        # evidence + article summary + related article summaries + bias rating |> fact check model -> accuracy, completeness scores + explanation
        self.fact_check(self.summary, self.bias_rating, self.related_summaries, self.evidence_summaries)