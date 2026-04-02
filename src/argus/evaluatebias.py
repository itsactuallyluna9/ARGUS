import asyncio
import chromadb
from datetime import datetime
import os
import json

from argus.fixjsonformatting import Bias_Schema
from argus.llamarouter import LlamaRouter


class Bias_Agent:


    def __init__(self, article_text: str, article_metadata: dict, bias_rating: str, router: LlamaRouter, article_collection: chromadb.Collection, analysis_model: str = "glm-4.7-flash", think: bool = True, use_long_prompt: bool = True):

        self.article_text = article_text
        self.title = article_metadata.get("title", "No title found")  # type: ignore
        self.source_name = article_metadata.get("source", "No source found")  # type: ignore
        self.date = article_metadata.get("date", "No date found")  # type: ignore
        self.intial_bias = bias_rating

        self.router = router
        self.article_collection = article_collection
        self.evaluation_model = analysis_model
        self.think = think

        self.agent_metadata = {}
        self.agent_metadata["scheduled"] = datetime.now().isoformat()

        self.default_prompt = """
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

        self.notes = ""

        self.bias_rating = {
            "political_bias": "Empty for now!",
            "sensationalism": "Empty for now!",
            "emotional_language": "Empty for now!",
            "political_score": 0,
            "sensationalism_score": 0,
            "emotional_language_score": 0,
        }

        if use_long_prompt:
            with open(os.path.join(os.getcwd(), "prompts", "biasprompt.md"), "r") as f:
                self.prompt = f.read()
        else:
            self.prompt = self.default_prompt


    async def analyze_bias(self) -> dict[str, str | int]:
        self.agent_metadata["started"] = datetime.now().isoformat()
        self.agent_metadata["total_tool_calls"] = 0
        self.agent_metadata["tool_calls"] = {}

        available_tools = {
            "read_notes": self.read_notes,
            "write_notes": self.write_notes,
            "search_db_tool": self.search_db_tool,
            "page_text_tool": self.page_text_tool,
        }

        messages = [
            {
                "role": "user",
                "content": f"Instructions: {self.prompt}\n\nText of {self.title} from {self.source_name} on {self.date}: {self.article_text}\n\nInitial Bias Rating: {self.intial_bias}\n\nCurrent date: {datetime.now().strftime('%Y-%m-%d')}",
            }
        ]

        while True:
            print("Sending message to bias model...")

            response = await self.router.chat(
                model=self.evaluation_model,
                think=self.think,
                messages=messages,
                tools=[
                    self.write_notes,
                    self.read_notes,
                    self.search_db_tool,
                    self.page_text_tool,
                ],
            )
            messages.append(response.model_dump())

            print(f"Bias model reasoning: {response.thinking}")
            print(f"Bias model response: {response.content}")

            if response.tool_calls:
                for call in response.tool_calls:
                    tool_name = call.function.name
                    tool_args = call.function.arguments

                    if tool_name in available_tools:
                        tool_response = available_tools[tool_name](**tool_args)
                        messages.append(
                            {
                                "role": "tool",
                                "content": f"Tool name: {tool_name}\nTool response: {tool_response}",
                            }
                        )
                        print(f"Tool name: {tool_name}\nTool response: {tool_response}")
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
                        print(f"Tool name: {tool_name}\nTool response: Tool not found.")

            else:
                print("No tool calls detected, finalizing bias evaluation...")
                messages = [messages[-1]]  # remove the last model response that contained no tool calls
                messages.append(
                    {
                        "role": "system",
                        "content": 'Ensure the response is in the correct JSON format according to the schema. This should include a final bias rating (0-100) for each of the three parts ("political_score", "sensationalism_score", "emotional_language_score"), as well as an explanation for each rating ("political_bias", "sensationalism", "emotional_language").',
                    }
                )
                response = await self.router.chat(model=self.evaluation_model, think=self.think, messages=messages, format=json.dumps(Bias_Schema.model_json_schema()))  # type: ignore
                break

        response = json.loads(response.content.split("```json")[-1].strip("```json").strip("```")) #type: ignore

        self.bias_rating["political_bias"] = response["political_bias_explanation"]
        self.bias_rating["sensationalism"] = response["sensationalism_explanation"]
        self.bias_rating["emotional_language"] = response["emotional_language_explanation"]
        self.bias_rating["political_score"] = response["political_score"]
        self.bias_rating["sensationalism_score"] = response["sensationalism_score"]
        self.bias_rating["emotional_language_score"] = response["emotional_language_score"]

        self.agent_metadata["finished"] = datetime.now().isoformat()

        return self.bias_rating

    
    async def read_notes(self) -> str:
        """Reads notes for the bias evaluation process."""
        return self.notes

    
    async def write_notes(self, new_notes: str) -> str:
        """Writes notes for the bias evaluation process.

        Args:
            new_notes: The notes to append to the bias evaluation notes.
        """
        self.notes = self.notes + "\n\n" + new_notes
        return "Notes updated."

    
    async def search_db_tool(self, query: str) -> list[tuple[str, str]]:
        """Searches the article collection for relevant information.

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

    
    async def page_text_tool(self, url: str) -> str:
        """Retrieves the full text content of a webpage that has already been summarized given its URL.

        Args:
            url: The URL of the webpage to retrieve text from.
        """

        try:
            page = self.article_collection.get(ids=[url])  # type: ignore
            return page["metadatas"][0]["article_text"]  # type: ignore

        except:
            return f"Error: Article {url} not found in database."


if __name__ == "__main__":
    article_collection = chromadb.HttpClient().get_or_create_collection(name="articles")

    metadata = article_collection.query(query_texts=["Costco"], n_results=1)["metadatas"][0][0]  # type: ignore
    article_metadata = {"title": "costco article", "source": "costco news", "date": "2024-01-01"}

    bias_agent = Bias_Agent(
        article_text=metadata["article_text"],  # type: ignore
        bias_rating=metadata["bias"],  # type: ignore
        article_metadata=article_metadata,  # type: ignore
        article_collection=article_collection,
        router=LlamaRouter(["100.67.68.111", "localhost"], [8080, 8080], ["GLM-4.7-Flash-UD-Q4_K_XL", "NVIDIA-Nemotron3-Nano-4B-Q4_K_M"]),
        use_long_prompt=False
    )

    bias_evaluation = asyncio.run(bias_agent.analyze_bias())
    print(bias_evaluation)
