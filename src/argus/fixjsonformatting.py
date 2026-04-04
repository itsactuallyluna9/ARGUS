import ollama
import json
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from argus.llamarouter import LlamaRouter

default_prompt = """
You are a tool designed to take improperly formatted strings and coerce them into your provided JSON schema. You will be given a string that is supposed to be in JSON format, but may have formatting issues such as extra backticks, missing or extra quotation marks, or other common formatting errors. Your task is to parse the string and return a properly formatted JSON object that matches the expected schema.
Return the properly formatted JSON object. Do not include any explanatory text or additional formatting, only return the JSON.
"""


@retry(
    retry=retry_if_exception_type(json.decoder.JSONDecodeError),
    stop=stop_after_attempt(3),
)
async def fix_json_formatting(s: str, schema: type[BaseModel], router: LlamaRouter) -> dict:

    response = await router.generate(
        prompt=f"{default_prompt}\nString to reformat: {s}",
        model="nemotron-3-nano:4b",
        format=json.dumps(schema.model_json_schema()),
    )

    return json.loads(response.content).split("```json")[-1].strip("```json")[0].strip("```")  # type: ignore


class Accuracy_Schema(BaseModel):
    accuracy: int
    reasoning: str
    sources: list[str]


class Completeness_Schema(BaseModel):
    completeness: int
    reasoning: str


class Bias_Schema(BaseModel):
    political_bias_explanation: str
    sensationalism_explanation: str
    emotional_language_explanation: str
    political_score: int
    sensationalism_score: int
    emotional_language_score: int


class SummarizeArticleSchema(BaseModel):
    description: str
    summary: str
    points: list[str]
    bias: str


class URLCheckSchema(BaseModel):
    isValid: bool
