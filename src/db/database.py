import sqlite3
from src.db import schema


class Database:
    def __init__(self, path='fuzzy_vocab.db'):
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys = ON")

    def create_tables(self):
        schema.create_tables(self.conn)

    def close(self):
        self.conn.close()

    def get_or_create(self, table: str, name: str) -> int:
        c = self.conn.cursor()
        c.execute(f"SELECT id FROM {table} WHERE name = ?", (name,))
        row = c.fetchone()
        if row is not None:
            return row[0]

        c.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))
        self.conn.commit()
        return c.lastrowid

    def link_brand_tier(self, brand_id: int, tier_word_id: int):
        c = self.conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO brand_tier (brand_id, tier_word_id) VALUES (?, ?)",
            (brand_id, tier_word_id)
        )
        self.conn.commit()