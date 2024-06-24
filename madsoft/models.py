from sqlalchemy import Column, Integer, String
from .database import Base

class Meme(Base):
    __tablename__ = "memes_models"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True)
    image_url = Column(String)
    description = Column(String)