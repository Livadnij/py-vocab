from dataclasses import dataclass

from openai import AsyncOpenAI
from src.llm.prompt import INSTRUCTION
import json
from src.schemas import TokenList

from datetime import timedelta
from time import monotonic


@dataclass
class ExtractionResult:
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int | None
    finish_reason: str
    text: str | None
    model: str
    response: str
    duration: timedelta


class LLLM:
    def __init__(self, base_url: str, api_key: str):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def extract(self, title: str, model: str) -> ExtractionResult:
        start = monotonic()
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": INSTRUCTION},
                {"role": "user", "content": title},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "tokens", "schema": TokenList.model_json_schema()},
            },
        )
        duration = timedelta(seconds=monotonic() - start)

        message = response.choices[0].message
        content = message.content

        reasoning_text = getattr(message, "reasoning_content", None) or getattr(message, "reasoning", None)

        usage = response.usage
        reasoning_tokens = None
        if usage and usage.completion_tokens_details:
            reasoning_tokens = usage.completion_tokens_details.reasoning_tokens

        return ExtractionResult(
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            reasoning_tokens=reasoning_tokens,
            text=reasoning_text,
            finish_reason=response.choices[0].finish_reason,
            model=response.model,
            response=content,
            duration=duration,
        )