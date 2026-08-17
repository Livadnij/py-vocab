import asyncio
import json

from src.config import LLM_CONCURENT_REQ, LLM_MODEL, PRODUCTS_SHEET_RANGE
from src.db.crud import persist_tokens
from src.llm.tokens import normalize_tokens


async def process_title(semaphore, llm, session, title, model, i: int, category_len: int):
    async with semaphore:
        try:
            print(f'[{i+1}\{category_len}] Starting processing {title}')
            raw_tokens = await llm.extract(title=title, model=model)
        except json.JSONDecodeError:
            print(f"[LLM] Failed to parse response for title: {title!r}")
            return

    tokens = normalize_tokens(raw_tokens)
    print(f'[{i+1}\{category_len}]: response recieved: {tokens}')

    persist_tokens(session, tokens, i, category_len)
    print(f'[{i+1}\{category_len}]Done\n')


async def run_category(db, sheet, llm, category: str) -> None:
    print(f'Starting processing of {category} category')
    db.create_tables()
    session = db.session()
    try:
        titles = sheet.read_column_content(category, PRODUCTS_SHEET_RANGE)
        category_len = len(titles)
        print(f'length: {category_len}')

        semaphore = asyncio.Semaphore(LLM_CONCURENT_REQ)
        await asyncio.gather(*(
            process_title(semaphore, llm, session, title, LLM_MODEL, i, category_len)
            for i, title in enumerate(titles)
        ))
    finally:
        print(f'Done category: {category}')
        session.close()
        db.close()