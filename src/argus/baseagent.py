from datetime import datetime
import json
import os
import chromadb
from ddgs.ddgs import DDGS
from loguru import logger

from argus.fixjsonformatting import fix_json_formatting
from argus.llamarouter import LlamaRouter
from argus.scraper import get_page
from argus.summarizearticle import summarize_article



class Agent:


    def __init__(
            self, 
            agent_name: str,
            router: LlamaRouter, 
            article_collection: chromadb.Collection, 
            article_text: str, 
            article_metadata: dict, 
            bias_rating: str,
            key_points: list[str],
            analysis_model: str, 
            think: bool = True, 
            summary_model: str = "",
            prompt_file_name: str = "", #filename in prompts folder, if empty / use_long_prompt is False, will use default prompt, else read from file
            fallback_prompt: str = "", 
            use_long_prompt: bool = True,
            max_tool_calls: int = 15
        ):

        self.agent_name = agent_name

        self.article_text = article_text
        self.title = article_metadata.get("title", "Title not found")
        self.source_name = article_metadata.get("site_name", "Source not found")
        self.date = article_metadata.get("date", "Date not found")

        self.bias_rating = bias_rating
        self.key_points = key_points

        self.router = router
        self.article_collection = article_collection

        self.analysis_model = analysis_model
        self.think = think

        self.summary_model = summary_model

        self.agent_metadata = {}
        self.agent_metadata["scheduled"] = datetime.now().isoformat()

        self.use_long_prompt = use_long_prompt
        self.default_prompt = fallback_prompt

        self.max_tool_calls = max_tool_calls

        self.notes = ""

        if use_long_prompt:
            with open(os.path.join(os.getcwd(), "prompts", prompt_file_name), "r") as f:
                self.prompt = f.read()
        else:
            self.prompt = self.default_prompt

    
    async def evaluate(self, schema: str, tools: list[function]) -> dict:

        logger.info(f"{self.agent_name}: Starting evaluation...")

        self.agent_metadata["started"] = datetime.now().isoformat()
        self.agent_metadata["total_tool_calls"] = 0
        self.agent_metadata["tool_calls"] = {}

        available_tools = {tool.__name__: tool for tool in tools}

        messages = [
            {"role": "system", "content": f"{self.prompt}\nNumber tool calls allowed: {self.max_tool_calls}\nAvailable tools: {', '.join(available_tools.keys())}"} if tools else {"role": "system", "content": self.prompt},
            {"role": "user", "content": f"Article title: {self.title}\nSource: {self.source_name}\nPublication date: {self.date}\nCurrent date: {datetime.now().isoformat()}\nBias rating: {self.bias_rating}\nKey points: {', '.join(self.key_points)}\nArticle text: {self.article_text}\n\nPlease provide your analysis in the following JSON format:\n{schema}"},
        ]

        done = False

        while not done:

            if self.agent_metadata["total_tool_calls"] >= self.max_tool_calls:
                logger.info(f"{self.agent_name}: Maximum tool calls ({self.max_tool_calls}) reached. Ending evaluation.\n")
                messages.append({"role": "system", "content": f"Maximum tool calls ({self.max_tool_calls}) reached.\nI need to finish my evaluation with the available information. My response should follow the following strict json schema: {schema}. I should return my evaluation in this format with no additional characters, explanation, or markdown formatting."})
                
                r = await self.router.chat(
                    model=self.analysis_model,
                    messages=messages,
                    think=self.think,
                    format=schema
                )

                done = True
                break

            r = await self.router.chat(
                model=self.analysis_model,
                messages=messages,
                think=self.think,
                format=schema,
                tools=tools
            )

            if r.tool_calls:
                for call in r.tool_calls:
                    tool_name = call.function.name
                    tool_args = call.function.arguments

                    if tool_name in available_tools:

                        try:
                            tool_response = await available_tools[tool_name](**tool_args) # type: ignore

                        except Exception as e:

                            tool_response = f"Error calling {tool_name}: {e}"
                            logger.info(f"{self.agent_name}: Tool call error: {tool_name}({tool_args}): {e}")

                        messages.append({
                            "role": "tool",
                            "content": f"Tool name: {tool_name}\nTool response: {tool_response}",
                        })

                        logger.info(f"{self.agent_name}: Tool name: {tool_name}\nTool response: {tool_response}")
                        self.agent_metadata["total_tool_calls"] += 1

                        if tool_name in self.agent_metadata["tool_calls"]:
                            self.agent_metadata["tool_calls"][tool_name] += 1
                        else:
                            self.agent_metadata["tool_calls"][tool_name] = 1

                    else:
                        messages.append({
                            "role": "tool",
                            "content": f"Tool name: {tool_name}\nTool response: Tool not found.",
                        })
                        logger.info(f"{self.agent_name}: Tool name: {tool_name}\nTool response: Tool not found.")

            else:

                logger.info(f"{self.agent_name}: No tool calls detected, finishing evaluation.")
                done = True
                break

        response = None
        content = (r.content or "").strip() # type: ignore

        if content:
            match content[0]:

                case "{":
                    try:
                        response = json.loads(content)
                    except json.JSONDecodeError as e:
                        logger.info(f"{self.agent_name}: JSON decoding error on final response: {content}\n{e}")

                case 'j':
                    if "json```" in content:
                        try:
                            response = json.loads(content.split("json```")[-1].strip("json```").strip("```"))
                        except json.JSONDecodeError as e:
                            logger.info(f"{self.agent_name}: JSON decoding error on final response: {content}\n{e}")

                case _:
                    logger.info(f"{self.agent_name}: Unexpected response format on final response: {content}")
                    
        else:
            logger.info(f"{self.agent_name}: Empty response content from model, falling back to fix_json_formatting.")

        if response is None:
            
            logger.info(f"{self.agent_name}: No valid JSON response received, attempting to fix formatting...")
            response = await fix_json_formatting("\n".join([f"{m['role']}: {m['content']}" for m in messages]), schema, self.router)

        if "properties" in response:
            response = response["properties"]

        self.agent_metadata["finished"] = datetime.now().isoformat()

        return response
    

    async def read_notes(self) -> str:
        """Reads the notes for the accuracy evaluation process."""
        return self.notes


    async def write_notes(self, new_notes: str) -> str:
        """Writes notes for the accuracy evaluation process.

        Args:
            new_notes: The notes to append to the accuracy evaluation notes.
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
            logger.info(f"{self.agent_name}: Error searching the internet for query: {query}")
            return []


    async def page_summary_tool(self, url: str) -> str:
        """Summarizes the content of a webpage given its URL.

        Args:
            url: The URL of the webpage to summarize.
        """

        if len(self.article_collection.get(ids=[url])["ids"]) == 0:
            logger.info(f"{self.agent_name}: Article {url} not found in database, summarizing and adding to database...")

            try:
                article_metadata, article_text = await get_page(url)
                summary = await summarize_article(article_text, self.router, model=self.summary_model if self.summary_model else "nemotron-3-nano:4b", use_long_prompt=self.use_long_prompt)
            except:
                logger.info(f"{self.agent_name}: Error summarizing article {url}.")
                return f"Error summarizing article {url}."

            try:
                self.article_collection.add(
                    ids=[url],
                    documents=[summary["summary"]],
                    metadatas=[{"url": url, "description": summary["description"], "summary": summary["summary"], "bias": summary["bias"], "points": summary["points"], "article_text": article_text, "timestamp": datetime.now().isoformat(), "metadata": json.dumps(article_metadata)}],
                )
                logger.info(f"{self.agent_name}: Article {url} added to database.")

            except:
                logger.info(f"{self.agent_name}: Error adding article {url} to database.")
                pass

            return summary["summary"]

        return self.article_collection.get(ids=[url])["documents"][0]  # type: ignore


    async def page_text_tool(self, url: str) -> str:
        """Retrieves the full text content of a webpage that has already been summarized given its URL.

        Args:
            url: The URL of the webpage to retrieve text from.
        """

        try:
            page = self.article_collection.get(ids=[url])
            return page["metadatas"][0]["article_text"] # type: ignore

        except:
            logger.info(f"{self.agent_name}: Error: Article {url} not found in database. Please use the page_summary_tool to summarize the article and add it to the database before retrieving the full text.")
            return f"Error: Article {url} not found in database. Please use the page_summary_tool to summarize the article and add it to the database before retrieving the full text."