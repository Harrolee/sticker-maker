from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, String, Integer, func

Base = declarative_base()
metadata = Base.metadata


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    credits = Column(Integer, default=0)
    github_id = Column(Integer, nullable=True)
    google_id = Column(Integer, nullable=True)

    # Relationship to link to stickers and collections
    stickers = relationship('Sticker', back_populates='creator_user', cascade='all, delete-orphan')
    collections = relationship('Collection', back_populates='creator_user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"id: {self.user_id}, name: {self.name}"

class Sticker(Base):
    __tablename__ = 'stickers'

    sticker_id = Column(Integer, primary_key=True, autoincrement=True)
    storefront_product_id = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    sales = Column(Integer, default=0)
    creator = Column(Integer, ForeignKey('users.user_id'), nullable=False)

    # Define back_populates for bidirectional relationship
    creator_user = relationship('User', back_populates='stickers')

    def __repr__(self):
        return f"id: {self.sticker_id}, name: {self.name}"