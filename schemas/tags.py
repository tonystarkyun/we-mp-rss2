from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class TagsBase(BaseModel):
    name: str
    cover: Optional[str] = None
    intro: Optional[str] = None
    status: int = 1

class TagsCreate(TagsBase):
    pass

class Tags(TagsBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True