# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "google-genai",
#     "ollama",
#     "pydantic",
#     "python-dotenv",
#     "rich",
# ]
# ///

#llm benchmarking!
#takes a model and a prompt to make an agent, takes input data and gives structured output,
#logging all the outputs and the model's performance

#needs to have:
#   framework for agent objects to store their prompts and models
#       simple class
#   level 1 2 and 3 testing functions
#       1. algorithmic unit tests
#           give the same model the same prompt 3-5 times and see how different they are?
#       2. model evaluation
#           pass original article and summary to gemini/openai api and get a score - essentially finetuning
#       3. A/B testing - takes a 2nd agent object
#           takes current agent object, plus another agent object, performs levels 1 and 2 tests
#   comprehensive logging system
#       write to file but probably some type of CLI to look at it kinda nicely
#       will display average time and token costs, as well as an option to view actual outputs
#   function to backpropagate prompt and create new agent object with new prompt

#seperately needs:
#   test data set for each question
#       start with summarizing article but test for others later

import ollama
import json
import re
from google import genai
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path


#intended to do the grunt summarizing work with smaller models
#prompt will be followed by the article text / other information provided
#it should describe the information the summarizer will recieve (article text)
#and what it should return (a summary of the article)
#as well as a structured output schema
class Summarizer():


    def __init__(self, prompt: str, model: str):

        self.model = model
        self.prompt = prompt
        ollama.pull(model)

    
    #logs the info related to the response provided
    def log(self, response: ollama.ChatResponse, articleText: str):
        
        # logName = 'logs\\summary_' + response.model + '_' + response.created_at + '.json'
        Path('logs').mkdir(parents=True, exist_ok=True)
        logName = Path('logs') / f'summary_{response.model}_{response.created_at}.json'
        # logName = re.sub('[<>:"/\\|?*]', '-', logName)

        with open(logName, 'w') as f:
            #everything except context to save storage space
            json.dump({
                "model": response.model,
                "created_at": response.created_at,
                "total_duration": response.total_duration,
                "load_duration": response.load_duration,
                "prompt_eval_count": response.prompt_eval_count,
                "prompt_eval_duration": response.prompt_eval_duration,
                "eval_count": response.eval_count,
                "eval_duration": response.eval_duration,
                "prompt": self.prompt,
                "article_text": articleText,
                "response": response.response,
                "thinking": response.thinking
            }, f, indent = 4)

            f.close()


    #when think == True, there will automatically be a schema added at the end of the prompt 
    #to account for lack of structured output
    def summarize(self, articleText: str, think = False):

        if think:

            schema = '''JSON schema: {
                "description": str,
                "articleSummary": str,
                "points": list[str],
                "biasSummary": str
            }'''

            response = ollama.generate(
                model = self.model, 
                prompt = (self.prompt + '\n' + schema + '\n\nArticle text:\n' + articleText),
                think = True
            )

        else:

            response = ollama.generate(
                model = self.model, 
                prompt = (self.prompt + '\n\nArticle text:\n' + articleText),
                think = False,
                format = SumOut.model_json_schema()
            )

        self.log(response, articleText)

        return response
    


#takes string evalPrompt, the blurb of text that will go before any article summaries, and a gemini model name string
class Evaluator():

    
    def __init__(self, model: str, evalPrompt: str):
        
        #loads in api key (GEMINI_API_KEY) from .env file, required for evaluator to function
        load_dotenv()

        self.model = model
        self.evalPrompt = evalPrompt

    
    #takes the path to a summarizer output json file and runs the evaluator on that summary, logging the info in its own json
    def evaluate(self, filePath: str):
        
        with open(filePath, 'rb') as f:

            summaryDict = json.load(f)

            f.close()

        client = genai.Client()

        fullPrompt = self.evalPrompt + '\n\nOriginal article text:\n' + summaryDict['article_text'] + '\n\nSummary to be evaluated:\n' + summaryDict['response']['articleSummary'] + '\n\nKey points:\n' + str(summaryDict['response']['points'])

        response = client.models.generate_content(
            model = self.model,
            contents = fullPrompt,
            config = {
                'response_mime_type': 'application/json',
                'response_schema': EvalOut
            }
        )

        return response, summaryDict
    

    def log(self, response, summaryDict):

        logName = f'logs\\{self.model}_eval_{summaryDict['model']}_{summaryDict['created_at']}.json'
        logName = re.sub('[<>:"/\\|?*]', '-', logName)

        evaluation = json.loads(response.text)

        with open(logName, 'w') as f:
            json.dump({
                'accuracy': evaluation['accuracy'],
                'completeness': evaluation['completeness'],
                'reasoning': evaluation['reasoning'],
                'model': summaryDict['model'],
                'summaryDict': summaryDict,
                'evalModel': self.model
            }, f, indent = 4)

            f.close()
    


#custom dict for json schema in summarizer
class SumOut(BaseModel):
    description: str
    articleSummary: str
    points: list[str]
    biasSummary: str
    


#custom dict for json schema in evaluator
class EvalOut(BaseModel):
    accuracy: int
    completeness: int
    reasoning: str



summaryPrompt = '''You are a tool designed to summarize articles. You will be given the full text of an article, and your task is to return 4 things:
1. A 1 sentence description of the article for indexing purposes (“description”). This should completely describe the subject of the article without going into too much detail. 
2. A 2-3 paragraph summary of the article (“articleSummary”). You should aim to cover the content of the article as accurately and completely as possible without editorializing or overexplaining.
3. A list of 3-5 key points in the article (“points”). These should focus on the factual claims made in the article. Do not comment on the accuracy of the points, only report the direct claims made by the article.
4. A 2-3 sentence summary of any political and reporting bias apparent from the text of the article (“biasSummary”). 

Output your response in the provided json schema.
'''

evalPrompt = '''You are a tool designed to rate the accuracy and completeness of article summaries. In this prompt you will be given the full text of an article, a summary of the article, and a list of key factual claims from that article. Your task is to judge the completeness and accuracy of the article and return 3 values:
1. An accuracy score (“accuracy”) for the summary between 0 and 100 evaluating how accurate the summary and key points are to the original text of the article,
2. A completeness score (“completeness”) for the summary between 0 and 100 evaluating how complete the summary and key points are and if they left out any important details,
3. A few sentences justification for the values you chose for accuracy and completeness (“reasoning”).

Output your answer in the provided json schema.
'''

articleText = '''WASHINGTON — The Trump administration announced Friday that it has begun "substantial" layoffs of federal workers, as the government remains shut down due to the inability of Congress to reach a funding deal.  "The RIFs have begun," White House budget director Russ Vought said on X, referring to "reduction in force" for workers.  While he didn't provide details, a spokesperson for the White House Office of Management and Budget confirmed to NBC News that the layoffs have begun and said they will be "substantial."  Affected agencies include the departments of Interior, Homeland Security, Treasury, Education, Energy, Housing and Urban Development and Health and Human Services, as well as the Environmental Protection Agency, according to an administration official.  Spokespeople for several of those departments confirmed to NBC News that they were sending layoff notices on Friday but declined to enumerate how many employees were affected, referring comment to OMB.  Democrats pushed back, saying that a shutdown does not require President Donald Trump to fire workers or give him new powers to do so, arguing the White House is being vindictive.  A DHS spokesperson said that the layoffs at the department were occurring within the Cybersecurity and Infrastructure Security Agency, which has been a major target of Trump's since its then-director affirmed that he lost the 2020 election to President Joe Biden. "During the last administration, CISA was focused on censorship, branding and electioneering," the DHS spokesperson said. "This is part of getting CISA back on mission."  HHS spokesman Andrew Nixon said the cuts at that department were focused on countering a "bloated bureaucracy" created under the Biden administration, adding: "HHS continues to close wasteful and duplicative entities, including those that are at odds with the Trump administration’s Make America Healthy Again agenda."  We’d like to hear from you about how you’re experiencing the government shutdown, whether you’re a federal employee who can’t work right now or someone who is feeling the effects of shuttered services in your everyday life. Please contact us at tips@nbcuni.com or reach out to us here.  Prominent unions responded Friday by questioning the legality of the White House’s move and threatening legal action, including AFL-CIO, which tweeted, “America’s unions will see you in court.”  AFSCME President Lee Saunders said the “mass firings are illegal” and will hurt families, vowing to “pursue every available level avenue to stop” the administration’s action.  Federal employee unions had already sued the Trump administration over OMB's threat to trigger mass firings of federal workers before the shutdown even began on Oct. 1. Plaintiffs in that ongoing lawsuit filed a supplementary motion on Friday asking for an immediate temporary restraining order preventing the OMB from ordering agencies to conduct reductions in force. It cited Vought’s post on X declaring that “The RIFs have begun.”  For Trump world, the focus shifts to next year's Nobel Peace Prize  The White House's move defies the wishes of Sen. Susan Collins, R-Maine, the Appropriations Committee chair who oversees government funding.  "I've made very clear that I do not believe there should be firings of furloughed workers," Collins told reporters on Wednesday.  Collins said Friday after the announcement, “I strongly oppose OMB Director Russ Vought’s attempt to permanently lay off federal workers who have been furloughed due to a completely unnecessary government shutdown caused by Senator Schumer.”  Sen. Lisa Murkowski of Alaska, another Republican on the Appropriations Committee, also criticized the layoffs, saying in a post on X that they were "poorly timed and yet another example of this administration’s punitive actions toward the federal workforce."  "The termination of federal employees in a shutdown will further hurt hard-working Americans who have dedicated their lives to public service and jeopardize agency missions once we finally re-open the government," Murkowski wrote.  Senate Minority Leader Chuck Schumer, D-N.Y., said, “Let’s be blunt: nobody’s forcing Trump and Vought to do this. ... They’re callously choosing to hurt people—the workers who protect our country, inspect our food, respond when disasters strike. This is deliberate chaos.”  “Here’s what’s worse: Republicans would rather see thousands of Americans lose their jobs than sit down and negotiate with Democrats to reopen the government,” Schumer said.  And Sen. Patty Murray, D-Wash., the top Democrat on the Appropriations Committee, said “this administration has been recklessly firing—and rehiring—essential workers all year,” adding: “This is nothing new, and no one should be intimidated by these crooks.”  Vought's announcement came one day after the Senate failed for the seventh time to pass either the Republican bill to keep the government open temporarily or the Democratic alternative that includes additional health care funding.'''
summary = '''The article details the Trump administration's initiation of substantial layoffs of federal workers during a government shutdown.\",\n  \"articlesummary\": \"Amid a government shutdown due to a funding impasse, the Trump administration began laying off federal workers, a move condemned by Democrats and some Republicans as vindictive and illegal. Affected agencies span multiple departments, including Homeland Security, Treasury, and Health and Human Services, with justifications provided by the administration centered around eliminating bureaucracy and refocusing agency missions. Unions have threatened legal action, and several senators have voiced opposition to the layoffs, highlighting the political and legal challenges surrounding the administration's actions.'''

# e = Evaluator('gemini-2.5-pro', evalPrompt)
# response, summaryDict = e.evaluate('C:\\Users\\Willow (Display)\\Documents\\Programming Projects\\School\\news-fact-checker\\logs\\qwen3-8b_2025-10-27T21-01-56.3890504Z.json')
# e.log(response, summaryDict)


# print(response)

def benchmark_summarizer(models: list[str], iterations: int):
    from rich.progress import Progress

    with Progress() as progress:
        for model in progress.track(models, description="Benchmarking Summarizers..."):
            think = False
            if model.endswith('-think'):
                model = model[:-6]
                think = True
            
            s = Summarizer(summaryPrompt, model)
            for _ in progress.track(range(iterations), description=f"Running {model}..."):
                results = s.summarize(articleText, think=think)
                s.log(results, articleText)

# s = Summarizer(summaryPrompt, 'qwen3:8b')

# s.log(s.summarize(articleText, think = False), articleText)

if __name__ == "__main__":
    # gemma3 4B, gemma3 12B, qwen3 8B, qwen3 27(?)B, and llama3 8B?, and qwen 14B
    benchmark_summarizer([
        'gemma3:4b', 'gemma3:12b',
        'qwen3:8b', 'qwen3:14b', 'qwen3:30b',
        'qwen3:8b-think', 'qwen3:14b-think', 'qwen3:30b-think',
        'llama3:8b', 'llama3.1:8b'], 10)
