from pydantic import ValidationError

from src.schemas import TokenBase


def normalize_tokens(result) -> list[TokenBase]:
    if isinstance(result, dict):
        result = result.get('tokens', [])

    tokens = []
    for element in result:
        try:
            tokens.append(TokenBase.model_validate(element))
        except ValidationError:
            continue
    return tokens