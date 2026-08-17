from src.db.database import Database
from src.db.models import Brand


def main():
    db = Database()
    session = db.session()
    try:
        brands = session.query(Brand).order_by(Brand.name).all()
        for brand in brands:
            tiers = ', '.join(t.name for t in brand.tier_words)
            print(f'{brand.name}: {tiers}')
    finally:
        session.close()
        db.close()


if __name__ == "__main__":
    main()