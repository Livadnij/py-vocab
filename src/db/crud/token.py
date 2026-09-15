from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Brand, Descriptor, TierWord, Title, TitleBrand, TitleDescriptor, TitleTierWord
from src.schemas.token import TokenBase


async def get_or_create(session: AsyncSession, model, name: str):
    result = await session.execute(select(model).where(model.name == name))
    instance = result.scalar_one_or_none()
    if instance is not None:
        return instance

    instance = model(name=name)
    session.add(instance)
    await session.flush()
    return instance


async def get_brand_occurrences(session: AsyncSession, brand_ids: list[int]) -> dict[int, int]:
    if not brand_ids:
        return {}
    result = await session.execute(
        select(TitleBrand.brand_id, func.count(TitleBrand.title_id))
        .where(TitleBrand.brand_id.in_(brand_ids))
        .group_by(TitleBrand.brand_id)
    )
    return dict(result.all())

async def get_tier_word_occurrences(session: AsyncSession, tier_word_ids: list[int]) -> dict[int, int]:
    if not tier_word_ids:
        return {}
    result = await session.execute(
        select(TitleTierWord.tier_word_id, func.count(TitleTierWord.title_id))
        .where(TitleTierWord.tier_word_id.in_(tier_word_ids))
        .group_by(TitleTierWord.tier_word_id)
    )
    return dict(result.all())

async def get_descriptor_occurrences(session: AsyncSession, descriptor_ids: list[int]) -> dict[int, int]:
    if not descriptor_ids:
        return {}
    result = await session.execute(
        select(TitleDescriptor.descriptor_id, func.count(TitleDescriptor.title_id))
        .where(TitleDescriptor.descriptor_id.in_(descriptor_ids))
        .group_by(TitleDescriptor.descriptor_id)
    )
    return dict(result.all())


async def persist_tokens(session: AsyncSession, tokens: list[TokenBase], title_log: list[str], title: Title) -> None:
    brands, tiers, descriptors = [], [], []

    for t in tokens:
        if t.label == "descriptor":
            descriptor_inst = await get_or_create(session, Descriptor, t.token)
            if descriptor_inst not in descriptors:
                descriptors.append(descriptor_inst)
            title_log.append(f'Descriptor found. id: {descriptor_inst.id}')

        elif t.label == "brand":
            brand_inst = await get_or_create(session, Brand, t.token)
            if brand_inst not in brands:
                brands.append(brand_inst)
            title_log.append(f'Brand found. id: {brand_inst.id}')

        elif t.label == "tier":
            tier_word_inst = await get_or_create(session, TierWord, t.token)
            if tier_word_inst not in tiers:
                tiers.append(tier_word_inst)
            title_log.append(f'Tier found. id: {tier_word_inst.id}')

    title.brands = brands
    title.tier_words = tiers
    title.descriptors = descriptors

    title_log.append(
        f'brands: {len(brands)}, tiers: {len(tiers)}, descriptors: {len(descriptors)} linked, replacing this title\'s previous links'
    )