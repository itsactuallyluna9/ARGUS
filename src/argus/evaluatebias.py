import chromadb
from datetime import datetime
import ollama
from threading import Thread

from argus.fixjsonformatting import fix_json_formatting, Bias_Schema



class Bias_Agent:
    

    def __init__(
        self,
        article_text: str,
        bias_rating: str,
        article_collection: chromadb.Collection,
        analysis_model: str = "glm-4.7-flash",
        think: bool = True,
    ):
        
        self.article_text = article_text
        self.intial_bias = bias_rating

        self.article_collection = article_collection
        self.evaluation_model = analysis_model
        self.think = think

        self.prompt = """
        You are a bias evaluation agent. Your task is to evaluate the political bias, sensationalism, and emotional language of a news article. You will be given the full text of the article, as well as an initial bias rating. 
        You will use this information to provide a final bias rating for the article, as well as an explanation for your rating. 
        This bias evaluation is broken into 3 parts, the political bias, sensationalism, and emotional language. For each part, you will provide a rating on a scale of 1 to 100, with 1 being the least biased and 100 being the most biased. You will also provide an explanation for each rating.
        
        You have access to several tools to help you with this task:
        1. read_notes: This tool allows you to read the notes you have taken during the bias evaluation process.
        2. write_notes: This tool allows you to write notes during the bias evaluation process. You can use this tool to keep track of your thoughts and observations as you evaluate the article.
        3. search_db_tool: This tool allows you to search the article collection for relevant information. You can use this tool to find other articles that are similar to the one you are evaluating, or to find information about the source of the article.
        4. page_text_tool: This tool allows you to retrieve the full text content of a webpage that has already been summarized given its URL. You can use this tool to get more information about the article you are evaluating, or to get the full text of any articles you find using the search_db_tool.

        You should use these tools as needed to gather information and insights that will help you provide a thorough and accurate bias evaluation for the article. 
        When you feel you have enough information to assess the bias in the article, remember to provide a final bias rating for each of the three parts, as well as an explanation for each rating.
        Return your output in the following JSON schema:
        {
            "political_bias": string,
            "sensationalism": string,
            "emotional_language": string,
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
            "emotional_language_score": 0
        }

        self.thread = Thread(target=self.analyze_bias)
        self.thread.start()

    
    def analyze_bias(self) -> dict[str, str | int]:
        
        available_tools = {
            "read_notes": self.read_notes,
            "write_notes": self.write_notes,
            "search_db_tool": self.search_db_tool,
            "page_text_tool": self.page_text_tool
        }

        messages = [{"role": "user", "content": f"Instructions: {self.prompt}\n\nArticle Text: {self.article_text}\n\nInitial Bias Rating: {self.intial_bias}\n\nCurrent date: {datetime.now().strftime('%Y-%m-%d')}"}]

        while True:

            print("Sending message to bias model...")

            response = ollama.chat(
                model = self.evaluation_model,
                think = self.think,
                messages = messages,
                tools = [self.write_notes, self.read_notes, self.search_db_tool, self.page_text_tool]
            )
            messages.append(response.message.model_dump())
            

            print(f"Bias model reasoning: {response.message.thinking}")
            print(f"Bias model response: {response.message.content}")

            if response.message.tool_calls:
                
                for call in response.message.tool_calls:

                    tool_name = call.function.name
                    tool_args = call.function.arguments

                    if tool_name in available_tools:
                        tool_response = available_tools[tool_name](**tool_args)
                        messages.append({"role": "tool", "content": f"Tool name: {tool_name}\nTool response: {tool_response}"})
                        print(f"Tool name: {tool_name}\nTool response: {tool_response}")
                    else:
                        messages.append({"role": "tool", "content": f"Tool name: {tool_name}\nTool response: Tool not found."})
                        print(f"Tool name: {tool_name}\nTool response: Tool not found.")

            else:
                print("No tool calls detected, finalizing bias evaluation...")
                messages.append({'role': 'system', 'content': "Ensure the response is in the correct JSON format according to the schema. This should include a final bias rating (0-100) for each of the three parts (\"political_score\", \"sensationalism_score\", \"emotional_language_score\"), as well as an explanation for each rating (\"political_bias\", \"sensationalism\", \"emotional_language\")."})
                response = ollama.chat(
                    model=self.evaluation_model,
                    think=self.think,
                    messages=messages
                )
                break

        bias_response = fix_json_formatting(response.message.content, Bias_Schema) # type: ignore

        self.bias_rating["political_bias"] = bias_response["political_bias"]
        self.bias_rating["sensationalism"] = bias_response["sensationalism"]
        self.bias_rating["emotional_language"] = bias_response["emotional_language"]
        self.bias_rating["political_score"] = bias_response["political_score"]
        self.bias_rating["sensationalism_score"] = bias_response["sensationalism_score"]
        self.bias_rating["emotional_language_score"] = bias_response["emotional_language_score"]

        return self.bias_rating
    

    def read_notes(self) -> str:
        """Reads notes for the bias evaluation process."""
        return self.notes


    def write_notes(self, new_notes: str) -> str:
        """Writes notes for the bias evaluation process."""
        """Args: notes (str): A string representation of the notes for the bias evaluation."""
        self.notes += f"\n{new_notes}"
        return "Notes updated."
    

    def search_db_tool(self, query: str) -> list[tuple[str, str]]:
        """Searches the article collection for relevant information."""
        """Args: query (str): A string representation of the query to search the article collection."""
        search_results = self.article_collection.query(query_texts=[query], n_results=5)
        results = []
        
        for i in range(len(search_results["ids"])):
            results.append((search_results["metadatas"][i][0]["description"], search_results["ids"][i]))  # type: ignore

        return results


    def page_text_tool(self, url: str) -> str:
        """Retrieves the full text content of a webpage that has already been summarized given its URL."""
        """Args: url (str): The URL of the webpage to retrieve text from."""
        
        try: 
            page = self.article_collection.get(ids=[url]) # type: ignore
            return page["metadatas"][0]["article_text"]  # type: ignore
        
        except:
            return f"Error: Article {url} not found in database."
        

if __name__ == "__main__":

    article_collection = chromadb.HttpClient().get_or_create_collection(name="articles")

    metadata = article_collection.query(query_texts=["Costco"], n_results=1)["metadatas"][0][0] # type: ignore

    bias_agent = Bias_Agent(
        article_text=metadata["article_text"],  # type: ignore
        bias_rating=metadata["bias"],  # type: ignore
        article_collection=article_collection
    )

    bias_evaluation = bias_agent.analyze_bias()
    print(bias_evaluation)