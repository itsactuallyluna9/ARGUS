import asyncio
import inspect
import json
import re
from typing import Callable, get_type_hints

from openai import AsyncOpenAI
from dataclasses import dataclass
from ollama import Message
import httpx

_LLAMA_TIMEOUT = httpx.Timeout(timeout=1800.0, connect=10.0)

class LlamaRouter:
    
    def __init__(self, ips: list[str], ports: list[int], models: list[str]):

        self.routes = {}

        self.model_aliases = {
            "glm-4.7-flash": "GLM-4.7-Flash-UD-Q4_K_XL",
            "nemotron-3-nano:4b": "NVIDIA-Nemotron3-Nano-4B-Q4_K_M"
        }

        for ip, port, model in zip(ips, ports, models):

            if model in self.model_aliases:
                model = self.model_aliases[model]

            self.add_route(Route(model=model, ip=ip, port=port))


    def add_route(self, route: Route):

        if route.model not in self.routes:
            self.routes[route.model] = []

        self.routes[route.model].append(route)


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

        for i in range(len(routes)):

            route = routes[i]

            if route.active_conversations < min_load:
                min_load = route.active_conversations
                route_index = i
        
        routes[route_index].active_conversations += 1
        self.routes[model][route_index] = routes[route_index]

        if override_url:
            client = AsyncOpenAI(base_url=override_url, api_key=routes[route_index].api_key, timeout=_LLAMA_TIMEOUT)
        else:
            client = AsyncOpenAI(base_url=f"http://{routes[route_index].ip}:{routes[route_index].port}", api_key=routes[route_index].api_key, timeout=_LLAMA_TIMEOUT)

        try:

            print(f"sending prompt to model {model} at {routes[route_index].ip}:{routes[route_index].port} with think={think}")

            print(format)
            print(type(format))

            raw_response = await client.chat.completions.create(
                model = f"~/llamacpp/models/{model}.gguf",
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
            reasoning = message.reasoning_content.strip() if think else None # type: ignore
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

            raise RuntimeError("Model returned no final output content.")

        finally:
            routes[route_index].active_conversations -= 1
            self.routes[model][route_index] = routes[route_index]

        
    async def chat(self, model: str, messages: list[dict], think: bool = False, tools: list = None, format: dict = None, override_url: str = None) -> Message: # type: ignore

        if model in self.model_aliases:
            model = self.model_aliases[model]

        routes = self.get_route(model)
        if not routes:
            raise ValueError(f"No routes available for model {model}")
        
        if tools:
            tools = [function_to_tool(tool) for tool in tools]
        
        min_load = float('inf')
        route_index = -1

        for i in range(len(routes)):

            route = routes[i]

            if route.active_conversations < min_load:
                min_load = route.active_conversations
                route_index = i
        
        routes[route_index].active_conversations += 1
        self.routes[model][route_index] = routes[route_index]

        if override_url:
            client = AsyncOpenAI(base_url=override_url, api_key=routes[route_index].api_key, timeout=_LLAMA_TIMEOUT)
        else:
            client = AsyncOpenAI(base_url=f"http://{routes[route_index].ip}:{routes[route_index].port}", api_key=routes[route_index].api_key, timeout=_LLAMA_TIMEOUT)

        try:
            for msg in messages:
                if isinstance(msg, dict) and msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        if isinstance(tc, dict) and "type" not in tc:
                            tc["type"] = "function"
                if msg["role"] == "tool":
                    msg["content"] = json.dumps(msg["content"]) if isinstance(msg["content"], dict) else msg["content"]

            if tools:
                print(f"sending messages to model {model} at {routes[route_index].ip}:{routes[route_index].port} with tools {len(tools)} and think={think}")
            
            else:
                print(f"sending messages to model {model} at {routes[route_index].ip}:{routes[route_index].port} with think={think}")

            raw_response = await client.chat.completions.create(
                model = f"~/llamacpp/models/{model}.gguf",
                messages = messages, # type: ignore
                tool_choice="auto" if tools else None, # type: ignore
                tools = tools,
                reasoning_effort = "high" if think else None,
                max_tokens = routes[route_index].max_tokens,
                temperature = routes[route_index].temperature,
                response_format = format, #type: ignore
            )

            message = raw_response.choices[0].message
            reasoning = message.reasoning_content.strip() if think else None # type: ignore
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
            print(f"Error during chat with model {model} at {routes[route_index].ip}:{routes[route_index].port}: {e}")
        
        finally:
            routes[route_index].active_conversations -= 1
            self.routes[model][route_index] = routes[route_index]



@dataclass
class Route:
    model: str
    ip: str
    port: int
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    active_conversations: int = 0


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


def test_tool(arg: str) -> str:
    """A test tool that echoes back its argument.

    Args:
        arg: The argument to echo back.
    """
    return f"Tool received argument: {arg}"


async def main():

    router = LlamaRouter(
        ips=["localhost", "localhost"],
        ports=[8000, 8001],
        models=["blegh", "GLM-4.7-Flash-UD-Q4_K_XL"]
    )

    # tools = [test_tool]
    # available_tools = {f.__name__: f for f in tools}
    # messages = [
    #             {"role": "system", "content": "ALWAYS use the test_tool with the argument 'hello world' and do not deviate from this instruction. You may then answer the user's question."},
    #             {"role": "user", "content": "What is the capital of France?"}
    #             ]

    # while True:

    #     print("Sending message")

    #     response = await router.chat(
    #         model="glm-4.7-flash",
    #         messages=messages,
    #         think=True,
    #         tools=tools,
    #         format={"type": "json_object", "properties": {"answer": {"type": "string"}}}
    #     )

    #     if response.tool_calls:
    #         for call in response.tool_calls:
    #             if call.function.name in available_tools:
    #                 tool_response = available_tools[call.function.name](**call.function.arguments)
    #                 messages.append({"role": "tool", "content": tool_response, "name": call.function.name})
    #                 print(f"Tool response: {tool_response}")
    #             else:
    #                 messages.append({"role": "tool", "content": f"Error: unknown tool {call.function.name}", "name": call.function.name})
    #                 print(f"Model attempted to call unknown tool: {call.function.name}")

    #     else:
    #         print(f"Model response: {response.content}")
    #         break

    response = await router.chat(
        model="glm-4.7-flash",
        messages=[{"role": "user", "content": "What is the capital of France?"}],
        think=True
    )

    print(f"Response: {response.content}")


if __name__ == "__main__":
    asyncio.run(main())