from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    tier_words = relationship("TierWord", secondary="brand_tier", back_populates="brands")


class Descriptor(Base):
    __tablename__ = "descriptors"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class TierWord(Base):
    __tablename__ = "tier_words"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    brands = relationship("Brand", secondary="brand_tier", back_populates="tier_words")


class BrandTier(Base):
    __tablename__ = "brand_tier"

    brand_id = Column(Integer, ForeignKey("brands.id"), primary_key=True)
    tier_word_id = Column(Integer, ForeignKey("tier_words.id"), primary_key=True)