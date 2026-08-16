def create_tables(conn):
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS brands (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS descriptors (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS tier_words (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS brand_tier (
        brand_id INTEGER NOT NULL,
        tier_word_id INTEGER NOT NULL,
        PRIMARY KEY (brand_id, tier_word_id),
        FOREIGN KEY (brand_id) REFERENCES brands(id),
        FOREIGN KEY (tier_word_id) REFERENCES tier_words(id)
    )
    """)

    conn.commit()