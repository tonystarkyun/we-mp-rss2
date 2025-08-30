from  .base import Base,Column,String,Integer,DateTime
class Feed(Base):   
    __tablename__ = 'feeds'
    id = Column(String(255), primary_key=True)
    mp_name =Column(String(255))
    mp_cover = Column(String(255))
    mp_intro = Column(String(255))
    status = Column(Integer)
    sync_time = Column(Integer)
    update_time = Column(Integer)
    created_at = Column(DateTime) 
    updated_at = Column(DateTime)
    faker_id = Column(String(255))