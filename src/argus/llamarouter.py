import asyncio
from asyncio import tools
import inspect
import json
from pyexpat.errors import messages
import re
from typing import Callable, get_type_hints
from loguru import logger

from openai import AsyncOpenAI
from dataclasses import dataclass, field
from ollama import Message
import httpx
from pydantic import HttpUrl

from argus.config import ModelRoute

_LLAMA_TIMEOUT = httpx.Timeout(timeout=1800.0, connect=10.0)



class LlamaRouter:
    
    
    def __init__(self, model_routes: list[ModelRoute]):

        self.routes = {}

        self.model_aliases = {
            "glm-4.7-flash": "GLM-4.7-Flash-UD-Q4_K_XL",
            "nemotron-3-nano:4b": "NVIDIA-Nemotron3-Nano-4B-Q4_K_M"
        }

        for route in model_routes:

            if route.model_name in self.model_aliases:
                route.model_name = self.model_aliases[route.model_name]

            self.add_route(Route(**route.model_dump()))


    def add_route(self, route: Route):

        if route.model_name not in self.routes:
            self.routes[route.model_name] = []

        self.routes[route.model_name].append(route)


    def get_route(self, model: str) -> list[Route]:

        if model in self.model_aliases:
            model = self.model_aliases[model]

        return self.routes.get(model, [])
    

    async def generate(self, model: str, prompt: str, think: bool = False, format: str = None, override_url: str = None) -> Message: # type: ignore

        if model in self.model_aliases:
            model = self.model_aliases[model]

        routes = self.get_route(model)
        if not routes:
            raise ValueError(f"No routes available for model {model}")
        
        min_load = float('inf')
        route_index = -1

        length = len(prompt) + (len(str(format)) if format else 0) + (1000 if think else 0)
        tokens = length / 4 + 100

        routes = [route for route in routes if route.max_tokens >= tokens]

        if not routes:
            raise ValueError(f"No routes available for model {model} that can handle the prompt length")

        for i in range(len(routes)):

            route = routes[i]

            if route.active_conversations < min_load:
                min_load = route.active_conversations
                route_index = i

        routes[route_index].active_conversations += 1   
        self.routes[model][route_index] = routes[route_index]

        logger.info(f"Selected route {routes[route_index].url} waiting for model {model} with current load {routes[route_index].active_conversations} and approximate token count {tokens}")
        await routes[route_index].request_lock.acquire()
        logger.info(f"Acquired lock for route {routes[route_index].url} and model {model}")

        override_client = None
        if override_url:
            override_client = AsyncOpenAI(base_url=override_url, api_key=routes[route_index].api_key, timeout=_LLAMA_TIMEOUT)
        client = override_client or routes[route_index].client

        try:

            logger.info(f"Sending prompt to model {model} at {routes[route_index].url} with think={think} and approximate token count {tokens}")

            raw_response = await client.chat.completions.create(
                model = model,
                messages = [{
                    "role": "user",
                    "content": prompt
                }],
                reasoning_effort = "high" if think else None,
                max_tokens = routes[route_index].max_tokens,
                temperature = routes[route_index].temperature,
                response_format = format, #type: ignore
            )

            message = raw_response.choices[0].message

            try:
                reasoning = message.reasoning_content.strip() if think else None # type: ignore
            except AttributeError:
                reasoning = None

            response_text = (message.content or "").strip()

            # for models that use literal <think> tags to indicate reasoning, we can remove them from the final output if think is True
            response_text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()

            if format and len(response_text.split("```json")) > 1:
                response_text = response_text.split("```json")[-1].strip("```json").strip("```")

            response = Message(
                role="assistant",
                content=response_text,
                thinking=reasoning
            )

            if response_text:
                return response

            else:
                return Message(
                    role="assistant",
                    content=f"Error: model returned empty response"
                )
            
        except Exception as e:
            logger.info(f"Error during generate with model {model} at {routes[route_index].url}: {e}")
            logger.info(f"Error type: {type(e)}")
            return Message(
                role="assistant",
                content=f"Error: {str(e)}"
            )

        finally:
            if override_client:
                await override_client.close()
            routes[route_index].active_conversations -= 1
            routes[route_index].request_lock.release()
            self.routes[model][route_index] = routes[route_index]

        
    async def chat(self, model: str, messages: list[dict], think: bool = False, tools: list = None, format: str = None, override_url: str = None) -> Message: # type: ignore

        if model in self.model_aliases:
            model = self.model_aliases[model]

        routes = self.get_route(model)
        if not routes:
            raise ValueError(f"No routes available for model {model}")
        
        if tools:
            tools = [function_to_tool(tool) for tool in tools]
        
        min_load = float('inf')
        route_index = -1

        length = len("".join(message["content"] for message in messages if "content" in message)) + len("".join(message["role"] for message in messages if "role" in message)) + (len(str(format)) if format else 0) + (len(str(tools)) if tools else 0) + (1000 if think else 0)
        tokens = length / 4 + 100

        routes = [route for route in routes if route.max_tokens >= tokens]

        if not routes:
            raise ValueError(f"No routes available for model {model} that can handle the prompt length")

        for i in range(len(routes)):

            route = routes[i]

            if route.active_conversations < min_load:
                min_load = route.active_conversations
                route_index = i
        
        routes[route_index].active_conversations += 1
        self.routes[model][route_index] = routes[route_index]

        logger.info(f"Selected route {routes[route_index].url} waiting for model {model} with current load {routes[route_index].active_conversations} and approximate token count {tokens}")
        await routes[route_index].request_lock.acquire()
        logger.info(f"Acquired lock for route {routes[route_index].url} and model {model}")

        override_client = None
        if override_url:
            override_client = AsyncOpenAI(base_url=override_url, api_key=routes[route_index].api_key, timeout=_LLAMA_TIMEOUT)
        client = override_client or routes[route_index].client

        try:
            for msg in messages:
                if isinstance(msg, dict) and msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        if isinstance(tc, dict) and "type" not in tc:
                            tc["type"] = "function"
                if msg["role"] == "tool":
                    msg["content"] = json.dumps(msg["content"]) if isinstance(msg["content"], dict) else msg["content"]

            if tools:
                logger.info(f"Sending messages to model {model} at {routes[route_index].url} with tools {len(tools)} and think={think} and approximate token count {tokens}")
            
            else:
                logger.info(f"Sending messages to model {model} at {routes[route_index].url} with think={think} and approximate token count {tokens}")

            raw_response = await client.chat.completions.create(
                model = model,
                messages = messages, # type: ignore
                tool_choice="auto" if tools else None, # type: ignore
                tools = tools,
                reasoning_effort = "high" if think else None,
                max_tokens = routes[route_index].max_tokens,
                temperature = routes[route_index].temperature,
                response_format = format, # type: ignore
            )

            message = raw_response.choices[0].message

            try:
                reasoning = message.reasoning_content.strip() if think else None # type: ignore
            except AttributeError:
                reasoning = None
                
            response_text = (message.content or "").strip()

            # for models that use literal <think> tags to indicate reasoning, we can remove them from the final output if think is True
            response_text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()

            if format and len(response_text.split("```json")) > 1:
                response_text = response_text.split("```json")[-1].strip("```json").strip("```")

            response = Message(
                role="assistant",
                content=response_text,
                thinking=reasoning,
                tool_name=message.tool_calls[0].function.name if message.tool_calls else None, # type: ignore
                tool_calls=[
                    Message.ToolCall(
                        function=Message.ToolCall.Function(
                            name=call.function.name, # type: ignore
                            arguments=json.loads(call.function.arguments) if isinstance(call.function.arguments, str) else call.function.arguments # type: ignore
                        )
                    ) for call in message.tool_calls 
                ] if message.tool_calls else None
            )

            return response
        
        except Exception as e:
            logger.info(f"Error during chat with model {model} at {routes[route_index].url}: {e}")
            logger.info(f"Error type: {type(e)}")
            return Message(
                role="assistant",
                content=f"Error: {str(e)}"
            )
        
        finally:
            if override_client:
                await override_client.close()
            routes[route_index].active_conversations -= 1
            routes[route_index].request_lock.release()
            self.routes[model][route_index] = routes[route_index]



@dataclass
class Route:
    model_name: str
    url: HttpUrl
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    request_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    active_conversations: int = 0
    client: AsyncOpenAI = field(default=None, init=False, repr=False)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.client = AsyncOpenAI(
            base_url=str(self.url),
            api_key=self.api_key,
            timeout=_LLAMA_TIMEOUT,
        )



PYTHON_TYPE_TO_JSON = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def function_to_tool(func: Callable) -> dict:
    """Convert a Python function into an OpenAI-compatible tool schema dict.

    Uses the function's name, docstring, type annotations, and default values
    to build the schema.  Compatible with both OpenAI and Ollama interfaces.

    Supported annotation types: str, int, float, bool, list, dict.
    Parameters without a type annotation default to "string".
    The first line of the docstring becomes the tool description.
    Per-parameter descriptions can be added with `Args:` / `Parameters:` sections
    using Google-style docstrings.
    """
    sig = inspect.signature(func)
    hints = get_type_hints(func)

    # --- parse parameter descriptions from docstring ---
    param_docs: dict[str, str] = {}
    doc = inspect.getdoc(func) or ""
    description = doc.split("\n")[0].strip() if doc else func.__name__

    in_args_section = False
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(("args:", "parameters:")):
            in_args_section = True
            continue
        if in_args_section:
            if stripped == "" or (not stripped.startswith(" ") and stripped.endswith(":")):
                in_args_section = False
                continue
            # expect "name: description" or "name (type): description"
            match = re.match(r"(\w+)(?:\s*\(.*?\))?\s*:\s*(.+)", stripped)
            if match:
                param_docs[match.group(1)] = match.group(2).strip()

    # --- build properties & required list ---
    properties: dict[str, dict] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        json_type = PYTHON_TYPE_TO_JSON.get(hints.get(name, str), "string")
        prop: dict = {"type": json_type}
        if name in param_docs:
            prop["description"] = param_docs[name]
        properties[name] = prop

        if param.default is inspect.Parameter.empty:
            required.append(name)

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }
