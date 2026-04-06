import asyncio
import chromadb
from datetime import datetime
import os
import json
from loguru import logger
from pydantic import HttpUrl

from argus.fixjsonformatting import Bias_Schema, fix_json_formatting
from argus.llamarouter import LlamaRouter
from argus.baseagent import Agent
from argus.scraper import get_page
from argus.summarizearticle import summarize_article
from argus.config import ModelRoute



default_prompt = """
You are a bias evaluation agent. Your task is to evaluate the political bias, sensationalism, and emotional language of a news article. You will be given the full text of the article, as well as an initial bias rating. 
You will use this information to provide a final bias rating for the article, as well as an explanation for your rating. 
This bias evaluation is broken into 3 parts, the political bias, sensationalism, and emotional language. For each part, you will provide a rating on a scale of 1 to 100, with 1 being the least biased and 100 being the most biased. You will also provide an explanation for each rating.

You have access to several tools to help you with this task:
1. read_notes: This tool allows you to read the notes you have taken during the bias evaluation process.
2. write_notes: This tool allows you to write notes during the bias evaluation process. You can use this tool to keep track of your thoughts and observations as you evaluate the article.
3. search_db_tool: This tool allows you to search the article collection for relevant information. You can use this tool to find other articles that are similar to the one you are evaluating, or to find information about the source of the article.
4. page_text_tool: This tool allows you to retrieve the full text content of a webpage that has already been summarized given its URL. You can use this tool to get more information about the article you are evaluating, or to get the full text of any articles you find using the search_db_tool.

You should use these tools as needed to gather information and insights that will help you provide a thorough and accurate bias evaluation for the article. 
When you feel you have enough information to assess the bias in the article, provide an explanation of the political bias, sensationalism, and emotional language and your final bias rating for each.
Return your output in the following JSON schema:
{
    "political_bias_explanation": string,
    "sensationalism_explanation": string,
    "emotional_language_explanation": string,
    "political_score": int,
    "sensationalism_score": int,
    "emotional_language_score": int,
}
"""



class BiasAgent(Agent):


    def __init__(self, article_text: str, article_metadata: dict, bias_rating: str, router: LlamaRouter, article_collection: chromadb.Collection, key_points: list[str] = [], evaluation_model: str = "glm-4.7-flash", think: bool = True, use_long_prompt: bool = True, max_tool_calls: int = 15):
        
        super().__init__(
            agent_name="Bias Agent",
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
            prompt_file_name="biasprompt.md"
        )

        self.schema = json.dumps(Bias_Schema.model_json_schema())
        self.tools = [self.read_notes, self.write_notes, self.search_db_tool, self.page_text_tool]

    
    async def evaluate_bias(self):

        response = await super().evaluate(self.schema, self.tools)

        if "properties" in response:
            response = response["properties"]

        political_score = int(response.get("political_score", 0))
        sensationalism_score = int(response.get("sensationalism_score", 0))
        emotional_language_score = int(response.get("emotional_language_score", 0))
        political_bias_explanation = response.get("political_bias_explanation", "Political bias explanation not found")
        sensationalism_explanation = response.get("sensationalism_explanation", "Sensationalism explanation not found")
        emotional_language_explanation = response.get("emotional_language_explanation", "Emotional language explanation not found")

        self.agent_metadata["finished"] = datetime.now().isoformat()

        logger.info(f"Bias evaluation completed.\nPolitical Score: {political_score}\nSensationalism Score: {sensationalism_score}\nEmotional Language Score: {emotional_language_score}\nPolitical Bias Explanation: {political_bias_explanation}\nSensationalism Explanation: {sensationalism_explanation}\nEmotional Language Explanation: {emotional_language_explanation}")

        self.political_score = political_score
        self.sensationalism_score = sensationalism_score
        self.emotional_language_score = emotional_language_score
        self.political_bias_explanation = political_bias_explanation
        self.sensationalism_explanation = sensationalism_explanation
        self.emotional_language_explanation = emotional_language_explanation
    



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

    bias_agent = BiasAgent(
        article_text,
        article_metadata,
        summary["bias"],
        key_points=summary["points"],
        router=LlamaRouter(routes),
        article_collection=collection,
        evaluation_model="glm-4.7-flash",
        think=True,
        use_long_prompt=False,
        max_tool_calls=15
    )
    asyncio.run(bias_agent.evaluate_bias())

    logger.info(f"Political score: {bias_agent.political_score}")
    logger.info(f"Sensationalism score: {bias_agent.sensationalism_score}")
    logger.info(f"Emotional language score: {bias_agent.emotional_language_score}")
    logger.info(f"Political bias explanation: {bias_agent.political_bias_explanation}")
    logger.info(f"Sensationalism explanation: {bias_agent.sensationalism_explanation}")
    logger.info(f"Emotional language explanation: {bias_agent.emotional_language_explanation}")