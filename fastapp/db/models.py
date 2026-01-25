from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, String, Integer, func, DateTime
from enum import Enum

Base = declarative_base()
metadata = Base.metadata


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    credits = Column(Integer, default=0)
    github_id = Column(Integer, nullable=True)
    google_id = Column(Integer, nullable=True)
    auth0_id = Column(String(255), nullable=True, unique=True)  # Auth0 'sub' field is a string

    # Remove the collections relationship for now
    stickers = relationship('Sticker', back_populates='creator_user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"id: {self.user_id}, name: {self.name}"

class StickerStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class Sticker(Base):
    __tablename__ = 'stickers'

    sticker_id = Column(Integer, primary_key=True, autoincrement=True)
    storefront_product_id = Column(String(100), nullable=True)
    name = Column(String(100), nullable=False)
    sales = Column(Integer, default=0)
    creator = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    status = Column(String, nullable=False, default=StickerStatus.READY)
    image_path = Column(String, nullable=True)
    error_message = Column(String, nullable=True)

    # Define back_populates for bidirectional relationship
    creator_user = relationship('User', back_populates='stickers')

    def __repr__(self):
        return f"id: {self.sticker_id}, name: {self.name}"

# class Collection(Base):
#     __tablename__ = 'collections'

#     collection_id = Column(Integer, primary_key=True)
#     name = Column(String)
#     user_id = Column(Integer, ForeignKey('users.user_id'))

#     # Add the back_populates to complete the bidirectional relationship
#     creator_user = relationship('User', back_populates='collections')

    # Add other fields as needed
