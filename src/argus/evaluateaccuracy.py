import chromadb
from datetime import datetime
import ollama
from ddgs import DDGS, exceptions
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from argus.fixjsonformatting import fix_json_formatting, Accuracy_Schema
from argus.scraper import get_page
from argus.summarizearticle import summarize_article



class Accuracy_Agent:


    def __init__(self, article_text: str, bias_rating: str, key_points: list[str], related_summaries: list[tuple[str, str]], article_collection: chromadb.Collection):
        
        self.article_text = article_text
        self.bias_rating = bias_rating
        self.key_points = key_points
        self.related_summaries = related_summaries
        self.article_collection = article_collection

        self.prompt = """
        You are an accuracy checker for news articles. You will be given the full text of an article, a bias rating, a list of key points, and a list of summaries and URLs of related articles. 
        Your task is to evaluate how factually accurate the article is based on the information provided and any additional information you can gather using the tools at your disposal. You should return an accuracy score between 0 and 100 evaluating how factually accurate the article is based on the evidence gathered, and a few sentences justification for the value you chose for accuracy. Additionally, return a list of the source URLs that were used to make your decision. This should include all of the sources that you considered, both those from the related articles and from your own research, but should exclude sources on irrelevant topics.

        You have access to several tools to help you with this task:
        1. A notes tool where you can write out the steps you plan to take to evaluate the article's accuracy. You can read these notes with a read_notes function and write to them with a write_notes function. You should use this tool extremely frequently to keep track of your progress and ensure that you are being thorough in your evaluation.
        2. A search_db_tool that takes a query and returns a list of relevant articles and their URLs from a database of articles. You should use this tool to find more information about the topic of the article and to gather evidence for or against the key points in the article.
        3. A search_internet_tool that takes a query and returns a list of relevant articles and their URLs from an internet search. You should prefer using the search_db_tool to find sources that are already in the database, but you can use the search_internet_tool to find additional sources if needed.
        4. A page_summary_tool that takes a URL and returns a summary of the article at that URL. You should use this tool to quickly gather information from sources that you find with the search_db_tool and search_internet_tool without having to read through the full text of each article.
        5. A page_text_tool that takes a URL and returns the full text of the article at that URL, but only for articles that have already been summarized and added to the database. You should use this tool to get more detailed information from sources that you find with the search_db_tool and search_internet_tool if the summary provided by the page_summary_tool does not give you enough information to evaluate the accuracy of the article.
        
        When evaluating the accuracy of the article, you should follow the steps below:
        1. Read through the article text and the bias rating, key points, and related summaries and URLs to get a general understanding of the article and its context.
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

        self.notes = ""


    #initiates agentic model to evaluate articles accuracy, will use tool calls to research and take notes, coerces to structured output, returns accuracy score, reasoning, and sources used in evaluation
    def evaluate_accuracy(self, model: str = "gpt-oss:20b", think: bool = True) -> tuple[int, str, list[str]]: # type: ignore
        
        available_tools = {
            "read_notes": self.read_notes,
            "write_notes": self.write_notes,
            "search_db_tool": self.search_db_tool,
            "search_internet_tool": self.search_internet_tool,
            "page_summary_tool": self.page_summary_tool,
            "page_text_tool": self.page_text_tool,
        }

        messages=[{"role": "user", "content": f"Instructions: {self.prompt}\nArticle text: {self.article_text}\nBias rating: {self.bias_rating}\nKey points: {self.key_points}\nRelated summaries and URLs: {self.related_summaries} \nCurrent date:{datetime.now().strftime('%Y-%m-%d')}",}]

        while True:
            
            print("Sending message to model...")

            response = ollama.chat(
                model=model,
                think=think,
                messages=messages,
                tools=[self.read_notes, self.write_notes, self.search_db_tool, self.search_internet_tool, self.page_summary_tool, self.page_text_tool],
            )
            messages.append(response.message) # type: ignore

            print(f"Model reasoning: {response.message.thinking}")
            print(f"Model response: {response.message.content}")

            if response.message.tool_calls:
                for call in response.message.tool_calls:
                    if call.function.name in available_tools:
                        result = available_tools[call.function.name](
                            **call.function.arguments
                        )
                        print(f"Tool call: {call.function.name} with arguments {call.function.arguments} returned result {result}")
                        messages.append({'role': 'tool', 'tool_name': call.function.name, 'content': str(result)})
            
            else:
                messages.append({'role': 'system', 'content': "Ensure the response is in the correct JSON format according to the schema. The output should include an accuracy score (0-100), reasoning, and the URLs for sources used in the evaluation."})
                response = ollama.chat(
                    model=model,
                    think=think,
                    messages=messages
                )
                break

        accuracy_response = fix_json_formatting(response.message.content, Accuracy_Schema) # type: ignore

        return accuracy_response["accuracy"], accuracy_response["reasoning"], accuracy_response["sources"]  # type: ignore


    def read_notes(self) -> str:
        """Reads the notes for the accuracy evaluation process."""
        return self.notes
    

    def write_notes(self, notes: str) -> str:
        """Writes notes for the accuracy evaluation process."""
        """Args: notes (str): A string representation of the notes for the accuracy evaluation."""
        self.notes = notes
        return notes


    def search_db_tool(self, query: str) -> list[tuple[str, str]]:
        """Searches the article collection database for relevant articles based on a query and returns a list of tuples containing the article title and URL."""
        """Args: query (str): The search query."""
        search_results = self.article_collection.query(query_texts=[query], n_results=5)
        results = []
        
        for i in range(len(search_results["ids"])):
            results.append((search_results["metadatas"][i][0]["description"], search_results["ids"][i]))  # type: ignore

        return results

    
    @retry(retry=retry_if_exception_type(exceptions.DDGSException))
    def search_internet_tool(self, query: str) -> list[tuple[str, str]]:
        """Searches for articles related to the query and returns a list of tuples containing the article title and URL."""
        """Args: query (str): The search query."""

        search_results = DDGS().text(query, max_results=5)
        results = []

        for result in search_results:
            results.append((result["title"], result["href"]))

        return results


    def page_summary_tool(self, url: str) -> str:
        """Summarizes the content of a webpage given its URL."""
        """Args: url (str): The URL of the webpage to summarize."""
        
        if len(self.article_collection.get(ids=[url])["ids"]) == 0:

            print(f"Article {url} not found in database, summarizing and adding to database...")
            
            article_text = get_page(url)
            summary = summarize_article(article_text)

            try:
                self.article_collection.add(
                ids=[url], 
                documents=[summary["articleSummary"]], 
                metadatas=[{
                        "url": url,
                        "description": summary["description"],
                        "summary": summary["articleSummary"],
                        "bias": summary["biasSummary"],
                        "points": summary["points"],
                        "article_text": article_text,
                        "timestamp": datetime.now().isoformat(),
                    }],
                )
                print(f"Article {url} added to database.")

            except:
                print(f"Error adding article {url} to database.")
                pass

            return summary["articleSummary"]  # type: ignore
        
        return self.article_collection.get(ids=[url])["documents"][0]  # type: ignore

    
    def page_text_tool(self, url: str) -> str:
        """Retrieves the full text content of a webpage that has already been summarized given its URL."""
        """Args: url (str): The URL of the webpage to retrieve text from."""
        
        try: 
            page = self.article_collection.get(ids=[url]) # type: ignore
            return page["metadatas"][0]["article_text"]  # type: ignore
        
        except:
            return f"Error: Article {url} not found in database. Please use the page_summary_tool to summarize the article and add it to the database before retrieving the full text."
        
if __name__ == "__main__":
    print("starting")
    article_text = get_page("https://www.usatoday.com/story/travel/2026/03/23/check-tsa-wait-times-government-shutdown-airports/89282748007/?utm_source=firefox-newtab-en-us")
    print(article_text)
    bias_rating = ""
    key_points = []
    related_summaries = []

    collection = chromadb.HttpClient().get_or_create_collection(name="articles")

    accuracy_agent = Accuracy_Agent(article_text, bias_rating, key_points, related_summaries, collection)

    print(accuracy_agent.evaluate_accuracy(model="glm-4.7-flash", think=True))