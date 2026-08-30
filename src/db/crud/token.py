from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Brand, BrandTier, Descriptor, TierWord, Title
from src.schemas import TokenBase

from src.db.models import Base


async def get_or_create(session: AsyncSession, model, name: str):
    result = await session.execute(select(model).where(model.name == name))
    instance = result.scalar_one_or_none()

    if instance is not None:
        await session.execute(
            update(model).where(model.id == instance.id).values(occurrence=model.occurrence + 1)
        )
        await session.flush()
        return instance

    instance = model(name=name)
    session.add(instance)
    await session.flush()
    return instance


async def link_brand_tier(session: AsyncSession, brand: Brand, tier_word: TierWord) -> None:
    result = await session.execute(
        select(BrandTier).where(BrandTier.brand_id == brand.id, BrandTier.tier_word_id == tier_word.id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        await session.execute(
            update(BrandTier)
            .where(BrandTier.brand_id == brand.id, BrandTier.tier_word_id == tier_word.id)
            .values(occurrence=BrandTier.occurrence + 1)
        )
    else:
        session.add(BrandTier(brand_id=brand.id, tier_word_id=tier_word.id))
    await session.flush()


def link_title_brand(title: Title, brand: Brand):
    if brand not in title.brands:
        title.brands.append(brand)

def link_title_tier(title: Title, tier_word: TierWord):
    if tier_word not in title.tier_words:
        title.tier_words.append(tier_word)

def link_title_descriptor(title: Title, descriptor: Descriptor):
    if descriptor not in title.descriptors:
        title.descriptors.append(descriptor)


async def persist_tokens(session: AsyncSession, tokens: list[TokenBase], title_log: list[str], title: Title) -> None:
    brands, tiers, descriptors = [], [], []

    for t in tokens:
        if t.label == "descriptor":
            descriptor_inst = await get_or_create(session, Descriptor, t.token)
            link_title_descriptor(title, descriptor_inst)
            descriptors.append(descriptor_inst)
            title_log.append(f'Descriptor created/updated. id: {descriptor_inst.id}')

        elif t.label == "brand":
            brand_inst = await get_or_create(session, Brand, t.token)
            link_title_brand(title, brand_inst)
            brands.append(brand_inst)
            title_log.append(f'Brand created/updated. id: {brand_inst.id}')

        elif t.label == "tier":
            tier_word_inst = await get_or_create(session, TierWord, t.token)
            link_title_tier(title, tier_word_inst)
            tiers.append(tier_word_inst)
            title_log.append(f'Tier created/updated. id: {tier_word_inst.id}')

    for b in brands:
        for t in tiers:
            await link_brand_tier(session, b, t)
            title_log.append(f'Connection between "{t.name}" tier and "{b.name}" brand strengthened')

    title_log.append(f'brands: {len(brands)}, tiers: {len(tiers)}, descriptors: {len(descriptors)} were created')