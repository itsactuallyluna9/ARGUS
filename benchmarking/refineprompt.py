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

    def refine_prompt(self, iteration_num=1, feedback: str = "") -> str:  # type: ignore
        """Refines the prompt based on feedback from the model and tool calls."""

        available_tools = {"write_notes": self.write_notes, "read_notes": self.read_notes}

        messages = [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": f"Refine the prompt to better achieve the goal of {self.goal_description}. Current prompt: {self.refined_prompt}"}]

        while True:
            print(f"[Iteration {iteration_num}] Sending prompt to model for refinement...")

            response = ollama.chat(model=self.model, think=self.think, messages=messages) #, tools=[self.write_notes, self.read_notes])

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
                print(f"[Iteration {iteration_num}] Refined Prompt: {self.refined_prompt}\n\n")
                feedback = input("Please enter any feedback for the refined prompt (press enter to skip): ")
                break
        try:
            if len(feedback) > 0:
                final_prompt = self.refine_prompt(feedback=feedback, iteration_num=iteration_num+1)
            else:
                final_prompt = self.refined_prompt

        except RetryError as e:
            print(f"[Error] ServerError encountered: {e}, returning last refined prompt without Gemini feedback.")
            final_prompt = self.refined_prompt

        return final_prompt  # type: ignore


    @retry(retry=retry_if_exception_type(ServerError), wait=wait_exponential(1, 60), stop=stop_after_attempt(5))
    def gemini_feedback(self, feedback: str) -> str:

        chat = self.gemini_client.chats.create(model=self.gemini_model, config=gemini.types.GenerateContentConfig(thinking_config=gemini.types.ThinkingConfig(include_thoughts=self.gemini_think)))

        print(f"[Gemini Feedback] Sending refined prompt to Gemini for feedback...")

        gemini_response = chat.send_message(self.system_prompt + f"\n\nRefine the prompt to better achieve the goal of {self.goal_description}. Current prompt: {self.refined_prompt}\n User feedback: {feedback}")

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
            "prompt_name": "summary_prompt",
            "initial_prompt": """
You are a tool designed to summarize articles. You will be given the full text of an article, and your task is to return 4 things:
A 1 sentence description of the article for indexing purposes (“description”). This should completely describe the subject of the article without going into too much detail.
A 2-3 paragraph summary of the article (“summary”). You should aim to cover the content of the article as accurately and completely as possible without editorializing or overexplaining.
A list of 2-3 key points in the article (“points”). These should focus on the factual claims made in the article. Do not comment on the accuracy of the points, only report the direct claims made or implied by the article.
A 2-3 sentence summary of any political and reporting bias apparent from the text of the article (“bias”).

Output your response in the provided json schema.

JSON schema: {
    "description": str,
    "summary": str,
    "points": list[str],
    "bias": str
}
""",
            "goal_description": "summarize articles in a way that is accurate, complete, and useful for indexing and understanding the content of the article, while also identifying any bias present in the article and returning a list of key points.",
        }
    ]

    main(prompts)
