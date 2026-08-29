import asyncio
import json

from src.config import settings
from src.db.crud import persist_tokens
from src.llm.tokens import normalize_tokens

from src.db.database import Database
from src.sheet.sheet import Spreadsheet
from src.llm.llm import LLLM
from src.schemas import TitlesList

import datetime


async def process_title(semaphore: asyncio.Semaphore, llm: LLLM, db: Database, title: str, model: str, i: int, category_len: int):
    title_log = []
    start_time = datetime.datetime.now()
    async with semaphore:
        try:
            title_log.append(f'[{i+1}\{category_len}] Starting processing {title}')
            raw_tokens = await llm.extract(title, model)
            llm_time = datetime.datetime.now()
            llm_elapsed_time = llm_time - start_time
            title_log.append(f'LLM response recieved in {llm_elapsed_time.total_seconds()} sec.')
        except json.JSONDecodeError:
            title_log.append(f"LLM failed to parse response for title\n")
            print("\n".join(title_log))
            return

    tokens = normalize_tokens(raw_tokens, title, title_log)
    normalization_time = datetime.datetime.now()
    normalization_elapsed_time = normalization_time - llm_time
    title_log.append(f'Tokens processed: {tokens}, in {normalization_elapsed_time.total_seconds()} sec.')

    persist_tokens(db, tokens, title_log)
    title_log.append(f'[{i+1}\{category_len}]Done\n')
    print("\n".join(title_log))


async def run_process(db: Database, llm: LLLM, titles: TitlesList) -> None:
    process_start_time = datetime.datetime.now()
    print(f'Starting processing of title from request')
    try:
        titles_len = len(titles)
        print(f'length: {titles_len}')

        semaphore = asyncio.Semaphore(settings.LLM_CONCURENT_REQ)
        await asyncio.gather(*(
            process_title(semaphore, llm, db, title, settings.LLM_MODEL, i, titles_len)
            for i, title in enumerate(titles)
        ))
    finally:
        print(f'Done category')