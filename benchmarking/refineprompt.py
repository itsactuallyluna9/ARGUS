import ollama
import google.genai as gemini
from google.genai.errors import ServerError
from dotenv import load_dotenv
import os
from rich import print
from tenacity import RetryError, retry, retry_if_exception_type, wait_exponential, stop_after_attempt


load_dotenv()


# prompt refiner agent class, takes initial prompt and description of goal, refines it based on recursive feedback from model and possibly gemini function calls, and refine the prompt based on quality of results for a certain number of iterations
class PromptRefiner:
    def __init__(self, initial_prompt: str, goal_description: str, local_model: str = "glm-4.7-flash", local_think: bool = True, gemini_model: str = "gemini-3.1-flash-lite-preview", gemini_think: bool = True):

        self.model = local_model
        self.think = local_think

        self.gemini_model = gemini_model
        self.gemini_think = gemini_think
        self.gemini_client = gemini.Client(api_key=os.environ.get("GEMINI_API_KEY"))

        self.initial_prompt = initial_prompt
        self.goal_description = goal_description
        self.refined_prompt = initial_prompt

        self.system_prompt = """
        You are an expert LLM prompt refinement agent. Your task is to refine the given prompt to better achieve the specified goal. You will use feedback from the model's responses and any relevant tool calls to iteratively improve the prompt.
        You have access to the following tools:
        1. write_notes(content: str): This tool allows you to write notes during the refinement process. You can use this tool to keep track of your thoughts, observations, and any insights you gain as you refine the prompt.
        2. read_notes() -> str: This tool allows you to read the notes you have taken during the refinement process. You can use this tool to review your previous thoughts and observations to inform your next steps in refining the prompt.

        Your refinement process should involve analyzing the model's responses to the current prompt, identifying any shortcomings or areas for improvement, and then modifying the prompt accordingly to better align with the goal. You should continue this iterative process until you believe the prompt is sufficiently refined to achieve the goal effectively. Return the final refined prompt with no additional text.
        """

        self.notes = ""

    def refine_prompt(self, max_iterations: int = 5) -> str:  # type: ignore
        """Refines the prompt based on feedback from the model and tool calls."""

        iteration_count = 0
        available_tools = {"write_notes": self.write_notes, "read_notes": self.read_notes}

        for _ in range(max_iterations):
            messages = [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": f"Refine the prompt to better achieve the goal of {self.goal_description}. Current prompt: {self.refined_prompt}"}]
            iteration_count += 1

            while True:
                print(f"[Iteration {iteration_count}] Sending prompt to model for refinement...")

                response = ollama.chat(model=self.model, think=self.think, messages=messages, tools=[self.write_notes, self.read_notes])

                messages.append(response.message.model_dump())

                if response.message.tool_calls:
                    for call in response.message.tool_calls:
                        tool_name = call.function.name
                        tool_args = call.function.arguments

                        if tool_name in available_tools:
                            tool_response = available_tools[tool_name](**tool_args)
                            messages.append({"role": "tool", "content": f"Tool {tool_name} called with args {tool_args} and returned {tool_response}"})
                            print(f"[Tool Call] {tool_name} called with args {tool_args} and returned {tool_response}")
                        else:
                            messages.append({"role": "tool", "content": f"Unknown tool, did not execute: {tool_name} called with args {tool_args}"})
                            print(f"[Tool Call] Unknown tool, did not execute: {tool_name} called with args {tool_args}")

                else:
                    self.refined_prompt = response.message.content
                    print(f"[Iteration {iteration_count}] Refined Prompt: {self.refined_prompt}")
                    break
        try:
            final_prompt = self.gemini_feedback()

        except RetryError as e:
            print(f"[Error] ServerError encountered: {e}, returning last refined prompt without Gemini feedback.")
            final_prompt = self.refined_prompt

        return final_prompt  # type: ignore

    @retry(retry=retry_if_exception_type(ServerError), wait=wait_exponential(1, 60), stop=stop_after_attempt(5))
    def gemini_feedback(self) -> str:

        chat = self.gemini_client.chats.create(model=self.gemini_model, config=gemini.types.GenerateContentConfig(thinking_config=gemini.types.ThinkingConfig(include_thoughts=self.gemini_think)))

        print(f"[Gemini Feedback] Sending refined prompt to Gemini for feedback...")

        gemini_response = chat.send_message(self.system_prompt + f"\n\nRefine the prompt to better achieve the goal of {self.goal_description}. Current prompt: {self.refined_prompt}")

        print(f"[Gemini Feedback] {gemini_response.text}")  # type: ignore

        return gemini_response.text  # type: ignore

    def write_notes(self, content: str) -> str:
        self.notes = content
        return "Notes updated."

    def read_notes(self) -> str:
        return self.notes


# takes in a list of dicts with prompt name, initial prompt, and goal description, and runs the prompt refiner agent on each, printing the final refined prompt for each
def main(prompts: list[dict[str, str]]):

    for prompt in prompts:
        refiner = PromptRefiner(initial_prompt=prompt["initial_prompt"], goal_description=prompt["goal_description"])

        refined_prompt = refiner.refine_prompt()

        print(f"Final Refined Prompt {prompt['prompt_name']}: {refined_prompt}")


if __name__ == "__main__":
    prompts = [
        {
            "prompt_name": "accuracy_prompt",
            "initial_prompt": """
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
            """,
            "goal_description": "To evaluate the factual accuracy of a news article based on the information provided and additional research, returning a score from 0-100, an explanation for the score, and a list of sources used in the evaluation. Do not remove the tool definitions, only refine them, if necessary.",
        }
    ]

    main(prompts)
