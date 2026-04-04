import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, IPvAnyInterface, PositiveInt


class StderrSink(BaseModel):
    level: str = "INFO"
    filter: str | None = None


class FileSink(BaseModel):
    path: Path
    level: str = "DEBUG"
    filter: str | None = None
    rotation: str = "100 MB"
    compression: str = "gz"
    retention: int = 5


class LoggingConfig(BaseModel):
    stderr: StderrSink = Field(default_factory=StderrSink)
    file: FileSink | None = None


class Agent(BaseModel):
    model: str  # TODO: our default
    thinking: bool  # TODO: true for all but summarizer default
    use_long_prompts: bool = True
    max_tool_calls: PositiveInt = 512


class Agents(BaseModel):
    summarizer: Agent = Field(default_factory=lambda: Agent(model="nemotron-3-nano:4b", thinking=False))
    accuracy: Agent = Field(default_factory=lambda: Agent(model="glm-4.7-flash", thinking=True))
    bias: Agent = Field(default_factory=lambda: Agent(model="glm-4.7-flash", thinking=True))
    completeness: Agent = Field(default_factory=lambda: Agent(model="glm-4.7-flash", thinking=True))


class ModelRoute(BaseModel):
    url: HttpUrl
    model_name: str
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 1024 * 16


class ChromaConfig(BaseModel):
    backend: Literal["memory", "persistent", "http"]
    path: Path | None = None
    url: HttpUrl | None = None


class Config(BaseModel):
    host: IPvAnyInterface
    port: PositiveInt
    agents: Agents
    model_routes: list[ModelRoute]
    chroma: ChromaConfig
    webhooks: list[HttpUrl] = []
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(path: Path) -> Config:
    with path.open("rb") as f:
        config = tomllib.load(f)
    return Config.model_validate(config)


if __name__ == "__main__":
    print(load_config(Path("config.toml")))
