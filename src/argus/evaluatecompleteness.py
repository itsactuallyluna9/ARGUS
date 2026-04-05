import asyncio
import json
import os
import chromadb
from datetime import datetime
from ddgs import DDGS
from loguru import logger

from argus.fixjsonformatting import Completeness_Schema, fix_json_formatting
from argus.scraper import get_page
from argus.summarizearticle import summarize_article
from argus.llamarouter import LlamaRouter


class Completeness_Agent:


    def __init__(self, article_text: str, article_metadata: dict, bias_rating: str, key_points: list[str], router: LlamaRouter, article_collection: chromadb.Collection, evaluation_model: str = "glm-4.7-flash", think: bool = True, use_long_prompt: bool = True, max_tool_calls: int = 15):

        self.article_text = article_text
        self.title = article_metadata.get("title", "Title not found")
        self.source_name = article_metadata.get("site_name", "Source not found")
        self.date = article_metadata.get("date", "Date not found")

        self.bias_rating = bias_rating
        self.key_points = key_points

        self.router = router
        self.article_collection = article_collection

        self.evaluation_model = evaluation_model
        self.think = think
        self.agent_metadata = {}
        self.agent_metadata["scheduled"] = datetime.now().isoformat()

        self.use_long_prompt = use_long_prompt
        self.default_prompt = """
        You are a completeness checker for news articles. You will be given the full text of an article, a bias rating, and a list of key points.
        Your task is to evaluate how complete the reporting of the article is compared to the information in other articles on the same topic. You should return a completeness score between 0 and 100 evaluating how complete the article's reporting is based on the information in the other articles and if they left out any important details, and a few sentences justification for the value you chose for completeness.
        
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
            "reasoning": str
        }
        """

        self.max_tool_calls = max_tool_calls

        self.notes = ""

        self.completeness_score = 0
        self.completeness_explanation = ""

        if use_long_prompt:
            with open(os.path.join(os.getcwd(), "prompts", "completenessprompt.md"), "r") as f:
                self.prompt = f.read()
        else:
            self.prompt = self.default_prompt


    async def evaluate_completeness(self) -> tuple[int, str]:  # type: ignore
        self.agent_metadata["started"] = datetime.now().isoformat()
        self.agent_metadata["total_tool_calls"] = 0
        self.agent_metadata["tool_calls"] = {}

        available_tools = {
            "read_notes": self.read_notes,
            "write_notes": self.write_notes,
            "search_db_tool": self.search_db_tool,
            "search_internet_tool": self.search_internet_tool,
            "page_summary_tool": self.page_summary_tool,
            "page_text_tool": self.page_text_tool,
        }

        messages = [
            {
                "role": "user",
                "content": f"Instructions: {self.prompt}\nText of {self.title} from {self.source_name} on {self.date}: {self.article_text}\nBias rating: {self.bias_rating}\nKey points: {self.key_points}\nCurrent date:{datetime.now().strftime('%Y-%m-%d')}\nPlease keep the number of tool calls under {self.max_tool_calls} and be as efficient as possible with your tool calls.",
            }
        ]

        while True:
            logger.info("Sending message to completeness model...")
            response = await self.router.chat(
                model=self.evaluation_model,
                think=self.think,
                messages=messages,
                tools=[
                    self.read_notes,
                    self.write_notes,
                    self.search_db_tool,
                    self.search_internet_tool,
                    self.page_summary_tool,
                    self.page_text_tool,
                ],
                format=json.dumps(Completeness_Schema.model_json_schema())  # type: ignore
            )
            messages.append(response.model_dump())

            logger.info(f"Completeness model reasoning: {response.thinking}")
            logger.info(f"Completeness model response: {response.content}")

            if response.tool_calls and len(messages) < self.max_tool_calls*4:
                for call in response.tool_calls:
                    tool_name = call.function.name
                    tool_args = call.function.arguments

                    if tool_name in available_tools:
                        try:
                            tool_response = await available_tools[tool_name](**tool_args)
                        except Exception as e:
                            tool_response = f"Error calling {tool_name}: {e}"
                            logger.info(f"Tool call error: {tool_name}({tool_args}): {e}")
                        messages.append(
                            {
                                "role": "tool",
                                "content": f"Tool name: {tool_name}\nTool response: {tool_response}",
                            }
                        )
                        logger.info(f"Tool name: {tool_name}\nTool response: {tool_response}")
                        self.agent_metadata["total_tool_calls"] += 1
                        if tool_name in self.agent_metadata["tool_calls"]:
                            self.agent_metadata["tool_calls"][tool_name] += 1
                        else:
                            self.agent_metadata["tool_calls"][tool_name] = 1
                    else:
                        messages.append(
                            {
                                "role": "tool",
                                "content": f"Tool name: {tool_name}\nTool response: Tool not found.",
                            }
                        )
                        logger.info(f"Tool name: {tool_name}\nTool response: Tool not found.")

            else:

                done = False
                logger.info("No tool calls detected, finalizing accuracy evaluation...")

                try: 
                    response = json.loads(response.content.split("```json")[-1].strip("```json").strip("```")) #type: ignore
                    if "properties" in response:
                        response = response["properties"]

                except TypeError:
                    try:
                        response = json.loads(response.content)  # type: ignore
                        done = True
                    except json.JSONDecodeError as e:
                        logger.info(f"Error decoding JSON response: {e}")
                except json.JSONDecodeError as e:
                    #final attempt to decode
                    recent = "\n".join([f"{messages[0]['role']}: {messages[0]['content']}", *[f"{m['role']}: {m['content']}" for m in messages[-10:]]])
                    try:
                        response = await fix_json_formatting(recent, Completeness_Schema, self.router) # type: ignore
                        done = True
                    except Exception as e:
                        logger.info(f"Error fixing JSON formatting: {e}")
                except KeyError:
                    pass

                if not done:
                    messages.append(
                        {
                            "role": "system",
                            "content": "I need to finalize my response and ensure the response is in the correct JSON format according to the schema. The output should include a completeness score (0-100) and a reasoning for the score.",
                        }
                    )
                    response = await self.router.chat(model=self.evaluation_model, think=self.think, messages=messages, format=json.dumps(Completeness_Schema.model_json_schema())) # type: ignore
                
                break

        if not isinstance(response, dict):
            try: 
                response = json.loads(response.content.split("```json")[-1].strip("```json").strip("```")) #type: ignore
                if "properties" in response:
                    response = response["properties"]
            except json.JSONDecodeError as e:
                logger.info(f"Error decoding JSON response: {e}")
            except KeyError:
                pass

        self.completeness_score = int(response.get("completeness", 0))  # type: ignore
        self.completeness_explanation = response.get("reasoning", "Completeness reasoning not found")  # type: ignore

        self.agent_metadata["finished"] = datetime.now().isoformat()

        return self.completeness_score, self.completeness_explanation  # type: ignore


    async def read_notes(self) -> str:
        """Reads the notes for the completeness evaluation process."""
        return self.notes


    async def write_notes(self, new_notes: str) -> str:
        """Writes notes for the completeness evaluation process.

        Args:
            new_notes: The notes to append to the completeness evaluation notes.
        """
        self.notes = self.notes + "\n\n" + new_notes
        return "Notes updated."


    async def search_db_tool(self, query: str) -> list[tuple[str, str]]:
        """Searches the article collection database for relevant articles based on a query and returns a list of tuples containing the article title and URL.

        Args:
            query: The search query.
        """
        search_results = self.article_collection.query(query_texts=[query], n_results=5)
        results = []

        for i in range(len(search_results["ids"][0])):
            results.append(
                (
                    search_results["metadatas"][0][i]["description"],  # type: ignore
                    search_results["ids"][0][i],
                )
            )

        return results


    async def search_internet_tool(self, query: str) -> list[tuple[str, str]]:
        """Searches for articles related to the query and returns a list of tuples containing the article title and URL.

        Args:
            query: The search query.
        """

        try:
            search_results = DDGS().text(query, max_results=5)
            results = []

            for result in search_results:
                results.append((result["title"], result["href"]))

            return results
    
        except:
            logger.info(f"Error searching the internet for query: {query}")
            return []
        

    async def page_summary_tool(self, url: str) -> str:
        """Summarizes the content of a webpage given its URL.

        Args:
            url: The URL of the webpage to summarize.
        """

        if len(self.article_collection.get(ids=[url])["ids"]) == 0:
            logger.info(f"Article {url} not found in database, summarizing and adding to database...")

            try:
                article_metadata, article_text = await get_page(url)
                summary = await summarize_article(article_text, self.router, use_long_prompt=self.use_long_prompt)
            except:
                logger.info(f"Error summarizing article {url}.")
                return f"Error summarizing article {url}."

            try:
                self.article_collection.add(
                    ids=[url],
                    documents=[summary["summary"]],
                    metadatas=[{
                        "url": url, 
                        "description": summary["description"], 
                        "summary": summary["summary"], 
                        "bias": summary["bias"], 
                        "points": summary["points"], 
                        "article_text": article_text, 
                        "timestamp": datetime.now().isoformat(), 
                        "metadata": json.dumps(article_metadata)
                    }],
                )
                logger.info(f"Article {url} added to database.")

            except:
                logger.info(f"Error adding article {url} to database.")
                pass

            logger.info(f"\n\n\nSummary of article {url}: {summary['summary']}\n\n\n")

            return summary["summary"]  # type: ignore

        return self.article_collection.get(ids=[url])["documents"][0]  # type: ignore


    async def page_text_tool(self, url: str) -> str:
        """Retrieves the full text content of a webpage that has already been summarized given its URL.

        Args:
            url: The URL of the webpage to retrieve text from.
        """

        try:
            page = self.article_collection.get(ids=[url])  # type: ignore
            return page["metadatas"][0]["article_text"]  # type: ignore

        except:
            return f"Error: Article {url} not found in database. Please use the page_summary_tool to summarize the article and add it to the database before retrieving the full text."



# if __name__ == "__main__":
#     logger.info("starting")
#     article_metadata, article_text = asyncio.run(get_page("https://www.usatoday.com/story/travel/2026/03/23/check-tsa-wait-times-government-shutdown-airports/89282748007/?utm_source=firefox-newtab-en-us"))
#     logger.info(article_text)
#     bias_rating = ""
#     key_points = []
#     related_summaries = []

#     collection = chromadb.HttpClient().get_or_create_collection(name="articles")

#     completeness_agent = Completeness_Agent(
#         article_text,
#         article_metadata,
#         bias_rating,
#         key_points,
#         router=LlamaRouter(ips=["localhost"], ports=[8001], models=["glm-4.7-flash"]),
#         article_collection=collection,
#         evaluation_model="glm-4.7-flash",
#         think=True,
#         use_long_prompt=False
#     )
    
#     scores = asyncio.run(completeness_agent.evaluate_completeness())

#     logger.info(f"Completeness score: {completeness_agent.completeness_score}")
#     logger.info(f"Completeness explanation: {completeness_agent.completeness_explanation}")