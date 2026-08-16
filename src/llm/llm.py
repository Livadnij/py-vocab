from openai import AsyncOpenAI
from src.llm.prompt import INSTRUCTION
import json
from src.schemas import TokenList

class LLLM:
    def __init__(self, base_url: str, api_key: str):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def extract(self, title: str, model: str):
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": INSTRUCTION},
                {"role": "user", "content": title}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "tokens", "schema": TokenList.model_json_schema()}
            }
        )
        return json.loads(response.choices[0].message.content)["tokens"]
