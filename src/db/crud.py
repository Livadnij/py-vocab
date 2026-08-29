from sqlalchemy.orm import Session

from src.db.models import Brand, Descriptor, TierWord
from src.schemas import TokenBase

from src.db.database import Database

from src.db.models import Base



def get_or_create(session: Session, model: type[Base], name: str):
    instance = session.query(model).filter_by(name=name).first()
    if instance is not None:
        return instance

    instance = model(name=name)
    session.add(instance)
    session.flush()
    return instance


def link_brand_tier(brand: Brand, tier_word: TierWord):
    if tier_word not in brand.tier_words:
        brand.tier_words.append(tier_word)


def persist_tokens(db: Database, tokens: list[TokenBase], title_log:list[str]) -> None:
    brand_tokens = [t for t in tokens if t.label == "brand"]
    if len(brand_tokens) != 1:
        return
    with db.session() as session:
        brand = get_or_create(session, Brand, brand_tokens[0].token)
        title_log.append(f'Brand is created successfuly. brand id: {brand.id}')

        for t in tokens:
            if t.label == "descriptor":
                descriptor = get_or_create(session, Descriptor, t.token)
                title_log.append(f'Descriptor is created successfuly. descriptor id: {descriptor.id}')
            elif t.label == "tier":
                tier_word = get_or_create(session, TierWord, t.token)
                title_log.append(f'Tier is created successfuly. tier id: {tier_word.id}')
                link_brand_tier(brand, tier_word)
                title_log.append(f'Connection between link and brand is made')

        session.commit()