import chromadb
from datetime import datetime
from argus.summarizearticle import summarize_article
from argus.scraper import get_page

class FactCheck:


    def __init__(self, url: str, article_collection: chromadb.Collection, summarizer_model: str = "gpt-oss:20b", think: bool = True):

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

        self.main()
    

    def main(self):
        
        # url |> scrape |> clean -> raw article text
        self.article_text = get_page(self.url)

        # raw article text |> summarizer |> -> summary, key points |> chromadb (if not present)
        self.summary, self.bias_rating, self.key_points = self.summarize_article(self.article_text)

        print(f"Summary for {self.url}:\n{self.summary}\n\nBias rating: {self.bias_rating}\n\nKey points:\n{self.key_points}")

        # summary |> search web for related articles |> summarizer |> chromadb
        # summary |> find related articles in chromadb -> related article summaries
        self.related_summaries = self.find_related_articles(self.summary)

        # key claims |> search web for evidence -> evidence
        self.evidence_summaries = self.find_evidence(self.key_points)

        # evidence + article summary + related article summaries + bias rating |> fact check model -> accuracy, completeness scores + explanation
        self.accuracy_score, self.completeness_score, self.explanation = self.fact_check(self.summary, self.bias_rating, self.related_summaries, self.evidence_summaries)

        print(f"Fact check results for {self.url}:\nAccuracy: {self.accuracy_score}\nCompleteness: {self.completeness_score}\nExplanation: {self.explanation}")    

        
    def summarize_article(self, article_text: str) -> tuple[str, str, list]:

        #returns json with index sentence, key points, summary, bias rating
        response = summarize_article(article_text, model=self.model, think=self.think)

        description = response['description']
        summary = response['articleSummary']
        key_points = response['points']
        bias_rating = response['biasSummary']

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
        
        return summary, bias_rating, key_points
    
    
    #PLACEHOLDER IMPLEMENTATION
    def urls_from_summary(self, summary: str) -> list[str]:
        # Placeholder for actual implementation
        return ["https://related.article1.com", "https://related.article2.com"]
    
    
    def find_related_articles(self, summary: str) -> list[tuple[str, str]]:
        # returns list of tuples of (related article summary, related article url)
        
        urls = self.urls_from_summary(summary)
        summaries = []

        for url in urls:
            if not self.article_collection.get(ids=[url]):
                curr_summary, _, _ = self.summarize_article(get_page(url))
                summaries.append((curr_summary, url))

        for result in self.article_collection.query(query_texts=[summary], n_results=5)['documents'][0]:
            summaries.append((result, self.article_collection.get(ids=[result])['metadatas'][0]['url']))

        return summaries
    
    
    #PLACEHOLDER IMPLEMENTATION
    def find_evidence(self, key_points: list[str]) -> list[tuple[str, str]]:
        # returns list of tuples of (evidence summary, evidence url)
        evidence = []
        for point in key_points:
            #placeholder for actual implementation
            evidence.append((f"Evidence summary for key point: {point}", f"https://evidence.url/for/{point}"))
        return evidence
    

    #PLACEHOLDER IMPLEMENTATION
    def fact_check(self, summary: str, bias_rating: str, related_summaries: list[tuple[str, str]], evidence_summaries: list[tuple[str, str]]) -> tuple[int, int, str]:
        # Placeholder for actual implementation
        accuracy_score = 80
        completeness_score = 70
        explanation = "The summary is mostly accurate but misses some key points. The bias rating is fair given the content of the article. The related articles and evidence support most of the claims made in the summary."
        return accuracy_score, completeness_score, explanation
    
if __name__ == "__main__":

    chroma_client = chromadb.Client()
    article_collection = chroma_client.get_or_create_collection(name="articles")

    f = FactCheck("https://www.freecodecamp.org/news/python-datetime-now-how-to-get-todays-date-and-time/", article_collection)