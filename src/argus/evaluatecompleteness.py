import asyncio
import json
import os
import chromadb
from datetime import datetime
from ddgs import DDGS
from loguru import logger
from pydantic import HttpUrl

from argus.baseagent import Agent
from argus.fixjsonformatting import Completeness_Schema, fix_json_formatting
from argus.scraper import get_page
from argus.summarizearticle import summarize_article
from argus.llamarouter import LlamaRouter
from argus.config import ModelRoute



default_prompt = """
    You are a completeness checker for news articles. You will be given the full text of an article, a bias rating, and a list of key points.
    Your task is to evaluate how complete the reporting of the article is compared to the information in other articles on the same topic. You should return a completeness score between 0 and 100 evaluating how complete the article's reporting is based on the information in the other articles and if they left out any important details, a few sentences justification for the value you chose for completeness, and a list of source urls that you used to inform your evaluation.

    You have access to several tools to help you with this task:
    1. A notes tool where you can write out the steps you plan to take to evaluate the article's accuracy. You can read these notes with a read_notes function and write to them with a write_notes function. You should use this tool extremely frequently to keep track of your progress and ensure that you are being thorough in your evaluation.
    2. A search_db_tool that takes a query and returns a list of relevant articles and their URLs from a database of articles. You should use this tool to find more information about the topic of the article and to gather evidence for or against the key points in the article.
    3. A search_internet_tool that takes a query and returns a list of relevant articles and their URLs from an internet search. You should prefer using the search_db_tool to find sources that are already in the database, but you can use the search_internet_tool to find additional sources if needed.
    4. A page_summary_tool that takes a URL and returns a summary of the article at that URL. You should use this tool to quickly gather information from sources that you find with the search_db_tool and search_internet_tool without having to read through the full text of each article.
    5. A page_text_tool that takes a URL and returns the full text of the article at that URL, but only for articles that have already been summarized and added to the database. You should use this tool to get more detailed information from sources that you find with the search_db_tool and search_internet_tool if the summary provided by the page_summary_tool does not give you enough information to evaluate the accuracy of the article.

    Use all of the tools at your disposal to gather information from related articles and evaluate the completeness of the reporting in the article. Be sure to keep detailed notes of your process and reasoning, and use those notes to inform your final evaluation of the article's completeness.
    When evaluating the completeness of the article, consider how the information in the article compares to the information in the related articles. Are there important details that are included in the related articles but not in the article you are evaluating? Are there key points that are mentioned in the related articles but not in the article you are evaluating? Use the information from the related articles to inform your evaluation of the completeness of the reporting in the article.

    When you feel that you have gathered enough information to accurately assess the article's completeness, return a completeness score between 0 and 100 evaluating how complete the article's reporting is based on the information in the other articles and if they left out any important details, and a few sentences justification for the value you chose for completeness.
    Output your answer in the provided json schema.
    JSON schema: {
        "completeness": int,
        "reasoning": str,
        "sources": list[str]
    }
    """



class CompletenessAgent(Agent):


    def __init__(self, article_text: str, article_metadata: dict, bias_rating: str, key_points: list[str], router: LlamaRouter, article_collection: chromadb.Collection, evaluation_model: str = "glm-4.7-flash", think: bool = True, use_long_prompt: bool = True, max_tool_calls: int = 15):
        
        super().__init__(
            agent_name="Completeness Agent",
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
            prompt_file_name="completenessprompt.md"
        )

        self.schema = json.dumps(Completeness_Schema.model_json_schema())
        self.tools = [self.read_notes, self.write_notes, self.search_db_tool, self.search_internet_tool, self.page_summary_tool, self.page_text_tool]

    
    async def evaluate_completeness(self):

        response = await super().evaluate(self.schema, self.tools)

        if "properties" in response:
            response = response["properties"]

        completeness_score = int(response.get("completeness", 0))
        completeness_explanation = response.get("reasoning", "Completeness reasoning not found")
        sources = response.get("sources", [])

        self.agent_metadata["finished"] = datetime.now().isoformat()

        logger.info(f"Completeness evaluation completed.\nScore: {completeness_score}\nExplanation: {completeness_explanation}\nSources: {sources}")

        self.completeness_score = completeness_score
        self.completeness_explanation = completeness_explanation
        self.completeness_sources = sources
    

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

    completeness_agent = CompletenessAgent(
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
    asyncio.run(completeness_agent.evaluate_completeness())

    logger.info(f"Completeness score: {completeness_agent.completeness_score}")
    logger.info(f"Completeness explanation: {completeness_agent.completeness_explanation}")
    logger.info(f"Sources used for completeness evaluation: {completeness_agent.completeness_sources}")