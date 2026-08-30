import json
from pydantic import ValidationError
from src.llm.llm import ExtractionResult
from src.schemas import TokenList


class ResponseParsingError(Exception):
    """Raised when an LLM response can't be turned into a valid TokenList."""


def parse_extraction_response(response: ExtractionResult) -> TokenList:
    if response.finish_reason == "length":
        raise ResponseParsingError("response was truncated (finish_reason=length)")

    try:
        data = json.loads(response.response)
    except json.JSONDecodeError as e:
        raise ResponseParsingError(f"invalid JSON: {e}") from e

    try:
        return TokenList.model_validate(data)
    except ValidationError as e:
        raise ResponseParsingError(f"schema validation failed: {e}") from e