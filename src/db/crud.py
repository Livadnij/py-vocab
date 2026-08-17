from sqlalchemy.orm import Session

from src.db.models import Brand, Descriptor, TierWord
from src.schemas import TokenBase


def get_or_create(session: Session, model, name: str):
    instance = session.query(model).filter_by(name=name).first()
    if instance is not None:
        return instance

    instance = model(name=name)
    session.add(instance)
    session.commit()
    return instance


def link_brand_tier(session: Session, brand: Brand, tier_word: TierWord):
    if tier_word not in brand.tier_words:
        brand.tier_words.append(tier_word)
        session.commit()


def persist_tokens(session: Session, tokens: list[TokenBase], i, category_len) -> None:
    brand_tokens = [t for t in tokens if t.label == "brand"]
    if len(brand_tokens) != 1:
        return

    brand = get_or_create(session, Brand, brand_tokens[0].token)
    print(f'[{i+1}\{category_len}]: brand is created successfuly. brand id: {brand.id}')

    for t in tokens:
        if t.label == "descriptor":
            descriptor = get_or_create(session, Descriptor, t.token)
            print(f'[{i+1}\{category_len}]: descriptor is created successfuly. descriptor id: {descriptor.id}')
        elif t.label == "tier":
            tier_word = get_or_create(session, TierWord, t.token)
            print(f'[{i+1}\{category_len}]: tier is created successfuly. tier id: {tier_word.id}')
            link_brand_tier(session, brand, tier_word)
            print(f'[{i+1}\{category_len}]: connection between link and brand is made')