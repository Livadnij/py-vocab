from src.db.database import Database
from src.config import *
from src.sheet.sheet import Spreadsheet
from src.llm.llm import LLLM
from src.schemas import *
import asyncio

from pydantic import ValidationError


def normalize_tokens(result):
    if isinstance(result, dict):
        result = result.get('tokens', [])

    tokens = []
    for element in result:
        try:
            tokens.append(TokenBase.model_validate(element))
        except ValidationError:
            continue
    return tokens

async def process_title(semaphore, llm, db, title, model, i : int, category_len:int):
    async with semaphore:
        try:
            print(f'[LLM] Starting processing {title}')
            raw_tokens = await llm.extract(title=title, model=model)
        except json.JSONDecodeError:
            print(f"[LLM] Failed to parse response for title: {title!r}")
            return

    tokens = normalize_tokens(raw_tokens)

    print(f'[LLM]: response recieved: {tokens}')

    brand_tokens = [t for t in tokens if t.label == "brand"]
    if len(brand_tokens) != 1:
        return

    print('[DB]: adding brand')
    brand_id = db.get_or_create("brands", brand_tokens[0].token)
    print(f'[DB]: brand is created successfuly. brand id: {brand_id}')

    for t in tokens:
        if t.label == "descriptor":
            descriptor_id=db.get_or_create("descriptors", t.token)
            print(f'[DB]: descriptor is created successfuly. descriptor id: {descriptor_id}')
        elif t.label == "tier":
            tier_id = db.get_or_create("tier_words", t.token)
            print(f'[DB]: tier is created successfuly. tier id: {tier_id}')
            db.link_brand_tier(brand_id, tier_id)
            print(f'[DB]: connection between link and brand is made')
    print(f'Done {i+1}/{category_len}\n')
    

async def main():
    db = Database()
    sheet = Spreadsheet(GOOGLE_SERVICE_ACCOUNT_JSON_PRODUCTS, PRODUCTS_SHEET_ID)
    llm = LLLM(LLM_BASE_URL, LLM_API_KEY)
    category = "Телевізори"
    print(f'Starting processing of {category} category')
    try:
        db.create_tables()
        titles = sheet.read_column_content(category, PRODUCTS_SHEET_RANGE)
        category_len = len(titles)
        print(f'length: {category_len}')
        semaphore = asyncio.Semaphore(LLM_CONCURENT_REQ)
        await asyncio.gather(*(process_title(semaphore, llm, db, title, LLM_MODEL, i, category_len) for i, title in enumerate(titles)))
    finally:
        print(f'Done category: {category}')
        db.close()


if __name__ == "__main__":
    asyncio.run(main())