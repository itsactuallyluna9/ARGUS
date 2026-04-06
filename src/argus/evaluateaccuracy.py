import asyncio
import os
import chromadb
from datetime import datetime
from ddgs import DDGS
import json
from loguru import logger
from pydantic import HttpUrl

from argus.baseagent import Agent
from argus.fixjsonformatting import Accuracy_Schema, fix_json_formatting
from argus.scraper import get_page
from argus.summarizearticle import summarize_article
from argus.llamarouter import LlamaRouter
from argus.config import ModelRoute



default_prompt = """
You are an accuracy checker for news articles. You will be given the full text of an article, a bias rating, and a list of key points from the article. 
Your task is to evaluate how factually accurate the article is based on the information provided and any additional information you can gather using the tools at your disposal. You should return an accuracy score between 0 and 100 evaluating how factually accurate the article is based on the evidence gathered, and a few sentences justification for the value you chose for accuracy. Additionally, return a list of the source URLs that were used to make your decision. This should include all of the sources that you considered, both those from the related articles and from your own research, but should exclude sources on irrelevant topics.

You have access to several tools to help you with this task:
1. A notes tool where you can write out the steps you plan to take to evaluate the article's accuracy. You can read these notes with a read_notes function and write to them with a write_notes function. You should use this tool extremely frequently to keep track of your progress and ensure that you are being thorough in your evaluation.
2. A search_db_tool that takes a query and returns a list of relevant articles and their URLs from a database of articles. You should use this tool to find more information about the topic of the article and to gather evidence for or against the key points in the article.
3. A search_internet_tool that takes a query and returns a list of relevant articles and their URLs from an internet search. You should prefer using the search_db_tool to find sources that are already in the database, but you can use the search_internet_tool to find additional sources if needed.
4. A page_summary_tool that takes a URL and returns a summary of the article at that URL. You should use this tool to quickly gather information from sources that you find with the search_db_tool and search_internet_tool without having to read through the full text of each article.
5. A page_text_tool that takes a URL and returns the full text of the article at that URL, but only for articles that have already been summarized and added to the database. You should use this tool to get more detailed information from sources that you find with the search_db_tool and search_internet_tool if the summary provided by the page_summary_tool does not give you enough information to evaluate the accuracy of the article.

When evaluating the accuracy of the article, you should follow the steps below:
1. Read through the article text and the bias rating and key points to get a general understanding of the article and its context.
2. Use the notes tool to write out a plan for how you will evaluate the article's accuracy. This plan should include the specific claims or key points in the article that you will investigate, the tools you will use to investigate each claim, and the order in which you will investigate them.
3. Follow the plan you have laid out, using the tools at your disposal to gather evidence for or against the claims in the article. Be thorough in investigating your claims, but dont spend too long on any one part in particular. Be sure to keep detailed notes of the evidence you gather and how it relates to each claim.
4. If/when you find a discrepancy between the claims in the article and the evidence you have gathered, check the original article again to make sure you did not misinterpret the claim. 

When you feel that you have gathered enough evidence to make a judgment about the article's accuracy, use the notes tool to write out your final reasoning for the accuracy score you will give the article. Then, return a JSON object with the following format:
JSON schema: {
    "accuracy": int,
    "reasoning": str,
    "sources": list[str]
}
"""



class AccuracyAgent(Agent):


    def __init__(self, article_text: str, article_metadata: dict, bias_rating: str, key_points: list[str], router: LlamaRouter, article_collection: chromadb.Collection, evaluation_model: str = "glm-4.7-flash", think: bool = True, use_long_prompt: bool = True, max_tool_calls: int = 15):
        
        super().__init__(
            agent_name="Accuracy Agent",
            router=router,
            article_collection=article_collection,
            article_text=article_text,
            article_metadata=article_metadata,
            bias_rating=bias_rating,
            key_points=key_points,
            analysis_model=evaluation_model,
            think=think,
            use_long_prompt=use_long_prompt,
            max_tool_calls=max_tool_calls,
            fallback_prompt=default_prompt,
            prompt_file_name="accuracyprompt.md"
        )

        self.schema = json.dumps(Accuracy_Schema.model_json_schema())
        self.tools = [self.read_notes, self.write_notes, self.search_db_tool, self.search_internet_tool, self.page_summary_tool, self.page_text_tool]

    
    async def evaluate_accuracy(self):

        response = await super().evaluate(self.schema, self.tools)

        if "properties" in response:
            response = response["properties"]

        accuracy_score = int(response.get("accuracy", 0))
        accuracy_explanation = response.get("reasoning", "Accuracy reasoning not found")
        sources = response.get("sources", [])

        self.agent_metadata["finished"] = datetime.now().isoformat()

        logger.info(f"Accuracy evaluation completed.\nScore: {accuracy_score}\nExplanation: {accuracy_explanation}\nSources: {sources}")

        self.accuracy_score = accuracy_score
        self.accuracy_explanation = accuracy_explanation
        self.accuracy_sources = sources
    


if __name__ == "__main__":
    logger.info("starting")
    article_metadata, article_text = asyncio.run(get_page("https://www.usatoday.com/story/travel/2026/03/23/check-tsa-wait-times-government-shutdown-airports/89282748007/?utm_source=firefox-newtab-en-us"))

    routes = [
        ModelRoute(url=HttpUrl("http://cs-cluster-1:8080"), model_name="glm-4.7-flash"),
        ModelRoute(url=HttpUrl("http://localhost:8080"), model_name="nemotron-3-nano:4b"),
    ]

    summary = asyncio.run(summarize_article(article_text, LlamaRouter(routes), use_long_prompt=False))
    logger.info(summary)
    bias_rating = ""
    key_points = []
    related_summaries = []

    collection = chromadb.HttpClient().get_or_create_collection(name="articles")

    accuracy_agent = AccuracyAgent(
        article_text,
        article_metadata,
        summary["bias"],
        summary["points"],
        router=LlamaRouter(routes),
        article_collection=collection,
        evaluation_model="glm-4.7-flash",
        think=True,
        use_long_prompt=False,
        max_tool_calls=15
    )
    asyncio.run(accuracy_agent.evaluate_accuracy())

    logger.info(f"Accuracy score: {accuracy_agent.accuracy_score}")
    logger.info(f"Accuracy explanation: {accuracy_agent.accuracy_explanation}")
    logger.info(f"Sources used for accuracy evaluation: {accuracy_agent.accuracy_sources}")