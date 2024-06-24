from typing import Optional
from pydantic import BaseModel, Field

class MemeBase(BaseModel):
    title: str
    description: str

class MemeCreate(MemeBase):
    image_url: str

class MemeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

class Meme(MemeBase):
    id: int
    image_url: str
    download_url: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True
