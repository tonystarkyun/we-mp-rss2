from  .base import Column,String,Integer,DateTime
from .base import Base
class Tags(Base):   
    __tablename__ = 'tags'
    id = Column(String(255), primary_key=True)
    name =Column(String(255))
    cover = Column(String(255))
    intro = Column(String(255))
    status = Column(Integer)
    sync_time = Column(Integer)
    update_time = Column(Integer)
    created_at = Column(DateTime) 
    updated_at = Column(DateTime)