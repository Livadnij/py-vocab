import asyncio

from src.config import GOOGLE_SERVICE_ACCOUNT_JSON_PRODUCTS, LLM_API_KEY, LLM_BASE_URL, PRODUCTS_SHEET_ID
from src.db.database import Database
from src.llm.llm import LLLM
from src.processing import run_category
from src.sheet.sheet import Spreadsheet

CATEGORY = ""


async def main():
    db = Database()
    sheet = Spreadsheet(GOOGLE_SERVICE_ACCOUNT_JSON_PRODUCTS, PRODUCTS_SHEET_ID)
    llm = LLLM(LLM_BASE_URL, LLM_API_KEY)

    db.create_tables()

    await run_category(db, sheet, llm, CATEGORY)


if __name__ == "__main__":
    asyncio.run(main())