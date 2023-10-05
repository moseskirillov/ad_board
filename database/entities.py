from datetime import datetime
from typing import List

from sqlalchemy import (
    MetaData,
    Integer,
    String,
    BigInteger,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship


class Base(AsyncAttrs, DeclarativeBase):
    metadata = MetaData(schema="public")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(length=255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(length=255), nullable=True)
    phone: Mapped[str] = mapped_column(String(length=255), nullable=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    telegram_login: Mapped[str] = mapped_column(String(length=255), nullable=True)
    register_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    last_login: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    ads: Mapped[List["Ad"]] = relationship()


class AdCategory(Base):
    __tablename__ = "ad_categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(length=255), nullable=False)
    alias: Mapped[str] = mapped_column(String(length=255), nullable=False)
    ads: Mapped[List["Ad"]] = relationship()


class Ad(Base):
    __tablename__ = "ads"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(length=255), nullable=False)
    description: Mapped[str] = mapped_column(String(length=1000), nullable=False)
    cost: Mapped[int] = mapped_column(Integer, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    is_rejected: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="ads", lazy="joined")
    category_id: Mapped[int] = mapped_column(
        ForeignKey("ad_categories.id"), nullable=True
    )
    category: Mapped["AdCategory"] = relationship(back_populates="ads", lazy="joined")
    images: Mapped[List["Image"]] = relationship(lazy="joined")
    messages: Mapped[List["MessageId"]] = relationship(lazy="joined")


class Image(Base):
    __tablename__ = "images"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image_id: Mapped[str] = mapped_column(String(length=300), nullable=True)
    media_id: Mapped[str] = mapped_column(String(length=300), nullable=True)
    ad_id: Mapped[int] = mapped_column(ForeignKey("ads.id"), nullable=True)
    ad: Mapped["Ad"] = relationship(back_populates="images", lazy="joined")


class MessageId(Base):
    __tablename__ = "message_ids"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(Integer, nullable=False)
    ad_id: Mapped[int] = mapped_column(ForeignKey("ads.id"), nullable=True)
