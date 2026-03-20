import json
import chromadb
import ollama
from tenacity import retry, stop_after_attempt, retry_if_exception_type

from argus.findsources import related_articles_from_topic
from argus.scraper import get_page
from argus.summarizearticle import summarize_article

# default_prompt = '''
# You are a tool designed to evaluate the factuality and quality of an article summary.
# You will be given the text of an article, a bias rating for the article, a list of summaries of related articles (including their URLs), and a list of article summaries evidencing key points from the article.
# Your task is to evaluate the how factually accurate the article is, and how complete the reporting of the article is compared to the related articles' summaries.
# You should return an accuracy score between 0 and 100 evaluating how factually accurate the article is based on the evidence provided, a completeness score between 0 and 100 evaluating how complete the article's reporting is and if they left out any important details, and a few sentences justification for the values you chose for accuracy and completeness.
# Output your answer in the provided json schema.
# JSON schema: {
#     "accuracy": int,
#     "completeness": int,
#     "reasoning": str
# }
# '''

accuracy_prompt = '''
You are a tool designed to evaluate the factual accuracy of an article. You will be given the text of an article, a bias rating for the article, and a list of summaries of related articles (including their URLs).
You will also have access to two tools: a "related_sources_tool" that takes a topic and returns a list of related articles and their summaries, and a "source_summary_tool" that takes a URL and returns a summary of the article at that URL.
Your task is to evaluate how factually accurate the article is. You are encouraged to use the tools at your disposal to gather more information and evidence before making your evaluation.
When you feel that you have gathered enough information to accurately assess the article's factual accuracy, return an accuracy score between 0 and 100 evaluating how factually accurate the article is based on the evidence gathered, and a few sentences justification for the value you chose for accuracy. Additionally, return a list of the source URLs that were used to make your decision. This should include all of the sources that you considered, both those from the related articles and from your own research, but should exclude sources on irrelevant topics.
Output your answer in the provided json schema.
JSON schema: {
    "accuracy": int,
    "reasoning": str,
    "sources": list[str]
}
'''

correct_accuracy_prompt = '''
You are a tool 
'''

completeness_prompt =  '''
You are a tool designed to evaluate the completeness of reporting of an article based on the article text, a bias rating for the article, and a list of summaries of related articles (including their URLs).
Your task is to evaluate how complete the reporting of the article is compared to the information in the other articles. You should return a completeness score between 0 and 100 evaluating how complete the article's reporting is and if they left out any important details, and a few sentences justification for the value you chose for completeness.
Output your answer in the provided json schema.
JSON schema: {
    "completeness": int,
    "reasoning": str
}
'''

further_research_prompt = '''
You are a tool designed to generate further research topics based on an article's content, bias rating, and a list of key points.
Your task is to generate a list of research topics that would be useful for fact checking the claims of the article, based on the article text, bias rating, and key points. These research topics should be specific and actionable, such that a researcher could use them to guide their fact checking process.
Output your answer as a JSON object containing a list of strings, each representing a research topic.
JSON schema: {
    "research_topics": list[str]
}
'''

reformat_prompt = '''
You are a tool designed to reformat the output of a summarization model. You will be given a string that is supposed to be in JSON format, but may have formatting issues such as extra backticks, missing or extra quotation marks, or other common formatting errors. Your task is to parse the string and return a properly formatted JSON object that matches the expected schema.
Return the properly formatted JSON object. Do not include any explanatory text, only return the JSON.
'''



@retry(retry=retry_if_exception_type(KeyError), stop=stop_after_attempt(3))
def evaluate_completeness(article_text: str, bias_rating: str, related_summaries: list[tuple[str, str]], evaluation_model: str = 'gpt-oss:20b', think: bool = True) -> tuple[int, str]:

    response = ollama.generate(model=evaluation_model, think=think, prompt=f"{completeness_prompt}\nArticle text: {article_text}\nBias rating: {bias_rating}\nRelated summaries and URLs: {related_summaries}")

    evaluation = fix_json_formatting(response.response)

    completeness_score = int(evaluation['completeness']) # type: ignore
    explanation = evaluation['reasoning'] # type: ignore

    return completeness_score, explanation


def generate_further_research_topics(article_text: str, bias_rating: str, key_points: list[str], evaluation_model: str = 'gpt-oss:20b', think: bool = True) -> list[str]:
    
    response = ollama.generate(model=evaluation_model, think=think, prompt=f"{further_research_prompt}\nArticle text: {article_text}\nBias rating: {bias_rating}\nKey points: {key_points}")

    research_topics_response = fix_json_formatting(response.response)

    research_topics = research_topics_response['research_topics'] # type: ignore

    return research_topics # type: ignore


#will use tool calls to take research topics, first check the database for relevant information, then generate search queries to find more sources, then evaluate those sources and use all the information to evaluate the article's accuracy
def evaluate_accuracy(article_text: str, bias_rating: str, related_summaries: list[tuple[str, str]], article_collection: chromadb.Collection, evaluation_model: str = 'gpt-oss:20b', think: bool = True) -> tuple[int, str, list[str]]:
    
    messages = [
        {"role": "system", "content": accuracy_prompt},
        {"role": "user", "content": f"Article text: {article_text}\nBias rating: {bias_rating}\nRelated summaries and URLs: {related_summaries}"}
    ]

    #defining function local to method to pass article_collection in all tool calls
    def source_summary_tool(url: str):
        if len(article_collection.get(ids=[url])["ids"]) == 0:

            print(f"Article {url} not found in database, summarizing and adding to database...")
            
            return summarize_article(get_page(url))

        return article_collection.get(ids=[url])["documents"][0] #type: ignore

    available_tools = {
        "related_sources_tool": related_sources_tool, 
        "source_summary_tool": source_summary_tool
    }

    thinking = True
    while thinking:

        response = ollama.chat(
            model = evaluation_model,
            think = think,
            messages = messages,
            tools = [related_sources_tool, source_summary_tool]
        )

        messages.append(response.message) # type: ignore
        print(f"Thinking: {response.message.thinking}")
        print(response.message.content)

        if response.message.tool_calls:
            for call in response.message.tool_calls:
                if call.function.name in available_tools:

                    print(f"Calling {call.function.name} with arguments {call.function.arguments}")
                    result = available_tools[call.function.name](**call.function.arguments)
                    print(f"Result: {result}")

                    messages.append({"role": "tool", "tool_name": call.function.name, "content": str(result)})

        else: 
            messages.append({
                "role": "user", 
                "content": '''Ensure that your output is correctly formatted.
                    You should have an accuracy score from 0-100, a few sentences explaining your reasoning, and a list of URLs for the sources you used.
                    Return your output in the following JSON schema:
                    {
                        "accuracy": int,
                        "reasoning": str,
                        "sources": list[str]
                    }
                    Return only the JSON-formatted output, no additional text.
                '''
            })

            response = ollama.chat(
                model = evaluation_model,
                think = think,
                messages = messages
            )
            thinking = False

    print(response.message.content)

    accuracy_response = fix_json_formatting(response.message.content) # type: ignore

    accuracy_score = accuracy_response['accuracy'] # type: ignore
    explanation = accuracy_response['reasoning'] # type: ignore
    sources_used = accuracy_response['sources'] # type: ignore

    return accuracy_score, explanation, sources_used # type: ignore


def related_sources_tool(topic: str) -> list[tuple[str, str]]:
    
    return related_articles_from_topic(topic)


@retry(retry=retry_if_exception_type(json.decoder.JSONDecodeError), stop=stop_after_attempt(3))
def fix_json_formatting(s: str) -> str:
    
    reformatted_response = json.loads(ollama.generate(model='nemotron-3-nano:4b', think=True, prompt=f"{reformat_prompt}\nString to reformat: {s}").response)

    return reformatted_response