from uuid import UUID

from sqlalchemy import Enum, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from datetime import timedelta, datetime
from sqlalchemy import MetaData
import enum


class AttemptStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"

class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)


convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)


class Brand(TimestampMixin, Base):
    __tablename__ = "brands"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    occurrence: Mapped[int] = mapped_column(nullable=False, default=1)

    tier_words: Mapped[list["TierWord"]] = relationship(secondary="brand_tier", back_populates="brands")
    titles: Mapped[list["Title"]] = relationship(secondary="title_brands", back_populates="brands")


class Descriptor(TimestampMixin, Base):
    __tablename__ = "descriptors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    occurrence: Mapped[int] = mapped_column(nullable=False, default=1)

    titles: Mapped[list["Title"]] = relationship(secondary="title_descriptors", back_populates="descriptors")


class TierWord(TimestampMixin, Base):
    __tablename__ = "tier_words"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    occurrence: Mapped[int] = mapped_column(nullable=False, default=1)

    brands: Mapped[list["Brand"]] = relationship(secondary="brand_tier", back_populates="tier_words")
    titles: Mapped[list["Title"]] = relationship(secondary="title_tier_words", back_populates="tier_words")


class BrandTier(TimestampMixin, Base):
    __tablename__ = "brand_tier"
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), primary_key=True)
    tier_word_id: Mapped[int] = mapped_column(ForeignKey("tier_words.id"), primary_key=True)
    occurrence: Mapped[int] = mapped_column(nullable=False, default=1)


class TitleBrand(CreatedAtMixin, Base):
    __tablename__ = "title_brands"
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id"), primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), primary_key=True)


class TitleTierWord(CreatedAtMixin, Base):
    __tablename__ = "title_tier_words"
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id"), primary_key=True)
    tier_word_id: Mapped[int] = mapped_column(ForeignKey("tier_words.id"), primary_key=True)


class TitleDescriptor(CreatedAtMixin, Base):
    __tablename__ = "title_descriptors"
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id"), primary_key=True)
    descriptor_id: Mapped[int] = mapped_column(ForeignKey("descriptors.id"), primary_key=True)


class Title(CreatedAtMixin, Base):
    __tablename__ = "titles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(unique=True, nullable=False)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"))

    request: Mapped["Request"] = relationship(back_populates="titles")
    attempts: Mapped[list["ProcessingAttempt"]] = relationship(back_populates="title")
    brands: Mapped[list["Brand"]] = relationship(secondary="title_brands", back_populates="titles")
    tier_words: Mapped[list["TierWord"]] = relationship(secondary="title_tier_words", back_populates="titles")
    descriptors: Mapped[list["Descriptor"]] = relationship(secondary="title_descriptors", back_populates="titles")


class ProcessingAttempt(CreatedAtMixin, Base):
    __tablename__ = "processing_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id"))
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"))
    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus, name="attempt_status", native_enum=False),
        nullable=False,
        default=AttemptStatus.pending,
        index=True,
    )

    title: Mapped["Title"] = relationship(back_populates="attempts")
    request: Mapped["Request"] = relationship(back_populates="attempts")
    thinking: Mapped["Thinking | None"] = relationship(back_populates="attempt")
    attempt_errors: Mapped[list["AttemptError"]] = relationship(back_populates="attempt")


class Request(TimestampMixin, Base):
    __tablename__ = "requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(unique=True)
    titles_amount: Mapped[int] = mapped_column(nullable=False)
    elapsed_time: Mapped[timedelta | None] = mapped_column(nullable=True)

    titles: Mapped[list['Title']] = relationship(back_populates='request')
    attempts: Mapped[list["ProcessingAttempt"]] = relationship(back_populates="request")
    hard_errors: Mapped[list["HardError"]] = relationship(back_populates="request")


class Thinking(CreatedAtMixin, Base):
    __tablename__ = "thinkings"
    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("processing_attempts.id"), unique=True)
    prompt_tokens: Mapped[int] = mapped_column(nullable=False)
    completion_tokens: Mapped[int] = mapped_column(nullable=False)
    reasoning_tokens: Mapped[int | None] = mapped_column(nullable=True)
    text: Mapped[str | None] = mapped_column(nullable=True)
    finish_reason: Mapped[str] = mapped_column(nullable=False)
    model: Mapped[str] = mapped_column(nullable=False)
    response: Mapped[str | None] = mapped_column(nullable=True)
    duration: Mapped[timedelta] = mapped_column(nullable=False)

    attempt: Mapped["ProcessingAttempt"] = relationship(back_populates="thinking")


class HardError(CreatedAtMixin, Base):
    __tablename__ = "hard_errors"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"))
    message: Mapped[str] = mapped_column(nullable=False)

    request: Mapped["Request"] = relationship(back_populates="hard_errors")


class AttemptError(CreatedAtMixin, Base):
    __tablename__ = "attempt_errors"
    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("processing_attempts.id"))
    message: Mapped[str] = mapped_column(nullable=False)

    attempt: Mapped["ProcessingAttempt"] = relationship(back_populates="attempt_errors")
