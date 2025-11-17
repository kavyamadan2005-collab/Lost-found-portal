from datetime import datetime, date

from sqlalchemy import Column, Integer, BigInteger, String, Text, Enum, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("user", "admin", name="user_roles"), nullable=False, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("Item", back_populates="user")


class Item(Base):
    __tablename__ = "items"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    type = Column(Enum("lost", "found", name="item_types"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    location = Column(String(255))
    date_reported = Column(Date)
    status = Column(Enum("open", "matched", "closed", name="item_statuses"), default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="items")
    images = relationship("ItemImage", back_populates="item")


class ItemImage(Base):
    __tablename__ = "item_images"

    id = Column(BigInteger, primary_key=True, index=True)
    item_id = Column(BigInteger, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", back_populates="images")
    features = relationship("ImageFeature", back_populates="image")


class ImageFeature(Base):
    __tablename__ = "image_features"

    id = Column(BigInteger, primary_key=True, index=True)
    image_id = Column(BigInteger, ForeignKey("item_images.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(100), nullable=False)
    feature_dim = Column(Integer, nullable=False)
    feature_vec = Column(String, nullable=False)  # serialized vector (e.g., JSON); adjust to BLOB if needed
    created_at = Column(DateTime, default=datetime.utcnow)

    image = relationship("ItemImage", back_populates="features")
