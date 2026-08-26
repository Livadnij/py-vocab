from pydantic import ValidationError

from src.schemas import TokenBase

def normalize_tokens(result: list[dict], title: str, title_log: list[str]) -> list[TokenBase]:
    if isinstance(result, dict):
        result = result.get('tokens', [])

    tokens = []
    for element in result:
        try:
            if element['token'].lower() in title.lower():
                tokens.append(TokenBase.model_validate(element))
            else:
                title_log.append(f"'{element['token']}' doesnt exist in title: '{title}'. Dropping token")
        except ValidationError:
            title_log.append(f"While processing '{element['token']}' token error happen. Dropping token")
            continue
    return tokens