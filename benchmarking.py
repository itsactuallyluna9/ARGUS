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



class Agent():


    def __init__(self, prompt: str, model: str):

        self.model = model
        self.prompt = prompt

    
    #logs the info related to the response provided
    def log(self, response):
        
        logName = 'logs\\' + response.model + '_' + response.created_at + '.json'
        logName = re.sub('[<>:"/\\|?*]', '-', logName)

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
                "response": response.response,
                "thinking": response.thinking
            }, f, indent = 4)
    


#intended to use larger models to score responses from summarizer agents
#prompt will be followed by the text in the functions, 
#it should describe what information the evaluator is recieving (summary + article text)
#and how it should be evaluating it (is it an accurate summary?)
#as well as a structured output schema
class Evaluator(Agent):


    def __init__(self, prompt: str, model: str):

        super().__init__(prompt, model)

    
    def evaluate(self, inputData: str):

        response = ollama.generate(model = self.model, prompt = (self.prompt + '\n\n' + inputData))

        self.log(response)

        return response



#intended to do the grunt summarizing work with smaller models
#prompt will be followed by the article text / other information provided
#it should describe the information the summarizer will recieve (article text)
#and what it should return (a summary of the article)
#as well as a structured output schema
class Summarizer(Agent):

    
    def __init__(self, prompt: str, model: str):

        super().__init__(prompt, model)

    
    def summarize(self, articleText: str):

        response = ollama.generate(model = self.model, prompt = (self.prompt + '\n\n' + articleText))

        self.log(response)

        return response
    


if __name__ == '__main__':

    ollama.pull(model = 'qwen3:8b')

    s = Summarizer(
        prompt = '''Analyze the following article and return a 1 sentence description of its topic, a 1 paragraph narrative summary, a list of 3-5 key points (focusing primarily on factual claims), and a brief summary of the article’s political and reporting biases. 
        Return only in JSON with the following schema: 
        {“description”: string, “articlesummary”: string, “points”: list[string], “biassummary”: string}''',
        model = 'qwen3:8b'
        )
    
    article = '''Article text: WASHINGTON — The Trump administration announced Friday that it has begun "substantial" layoffs of federal workers, as the government remains shut down due to the inability of Congress to reach a funding deal.  "The RIFs have begun," White House budget director Russ Vought said on X, referring to "reduction in force" for workers.  While he didn't provide details, a spokesperson for the White House Office of Management and Budget confirmed to NBC News that the layoffs have begun and said they will be "substantial."  Affected agencies include the departments of Interior, Homeland Security, Treasury, Education, Energy, Housing and Urban Development and Health and Human Services, as well as the Environmental Protection Agency, according to an administration official.  Spokespeople for several of those departments confirmed to NBC News that they were sending layoff notices on Friday but declined to enumerate how many employees were affected, referring comment to OMB.  Democrats pushed back, saying that a shutdown does not require President Donald Trump to fire workers or give him new powers to do so, arguing the White House is being vindictive.  A DHS spokesperson said that the layoffs at the department were occurring within the Cybersecurity and Infrastructure Security Agency, which has been a major target of Trump's since its then-director affirmed that he lost the 2020 election to President Joe Biden. "During the last administration, CISA was focused on censorship, branding and electioneering," the DHS spokesperson said. "This is part of getting CISA back on mission."  HHS spokesman Andrew Nixon said the cuts at that department were focused on countering a "bloated bureaucracy" created under the Biden administration, adding: "HHS continues to close wasteful and duplicative entities, including those that are at odds with the Trump administration’s Make America Healthy Again agenda."  We’d like to hear from you about how you’re experiencing the government shutdown, whether you’re a federal employee who can’t work right now or someone who is feeling the effects of shuttered services in your everyday life. Please contact us at tips@nbcuni.com or reach out to us here.  Prominent unions responded Friday by questioning the legality of the White House’s move and threatening legal action, including AFL-CIO, which tweeted, “America’s unions will see you in court.”  AFSCME President Lee Saunders said the “mass firings are illegal” and will hurt families, vowing to “pursue every available level avenue to stop” the administration’s action.  Federal employee unions had already sued the Trump administration over OMB's threat to trigger mass firings of federal workers before the shutdown even began on Oct. 1. Plaintiffs in that ongoing lawsuit filed a supplementary motion on Friday asking for an immediate temporary restraining order preventing the OMB from ordering agencies to conduct reductions in force. It cited Vought’s post on X declaring that “The RIFs have begun.”  For Trump world, the focus shifts to next year's Nobel Peace Prize  The White House's move defies the wishes of Sen. Susan Collins, R-Maine, the Appropriations Committee chair who oversees government funding.  "I've made very clear that I do not believe there should be firings of furloughed workers," Collins told reporters on Wednesday.  Collins said Friday after the announcement, “I strongly oppose OMB Director Russ Vought’s attempt to permanently lay off federal workers who have been furloughed due to a completely unnecessary government shutdown caused by Senator Schumer.”  Sen. Lisa Murkowski of Alaska, another Republican on the Appropriations Committee, also criticized the layoffs, saying in a post on X that they were "poorly timed and yet another example of this administration’s punitive actions toward the federal workforce."  "The termination of federal employees in a shutdown will further hurt hard-working Americans who have dedicated their lives to public service and jeopardize agency missions once we finally re-open the government," Murkowski wrote.  Senate Minority Leader Chuck Schumer, D-N.Y., said, “Let’s be blunt: nobody’s forcing Trump and Vought to do this. ... They’re callously choosing to hurt people—the workers who protect our country, inspect our food, respond when disasters strike. This is deliberate chaos.”  “Here’s what’s worse: Republicans would rather see thousands of Americans lose their jobs than sit down and negotiate with Democrats to reopen the government,” Schumer said.  And Sen. Patty Murray, D-Wash., the top Democrat on the Appropriations Committee, said “this administration has been recklessly firing—and rehiring—essential workers all year,” adding: “This is nothing new, and no one should be intimidated by these crooks.”  Vought's announcement came one day after the Senate failed for the seventh time to pass either the Republican bill to keep the government open temporarily or the Democratic alternative that includes additional health care funding.'''
    
    for i in range(10):
        s.summarize(article)