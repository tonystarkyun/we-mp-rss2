# core/models/industries.py - 行业动态数据模型
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from .base import Base

class Industry(Base):
    """行业动态数据模型"""
    __tablename__ = 'industries'
    
    id = Column(String(50), primary_key=True, comment='行业链接ID')
    name = Column(String(200), nullable=False, comment='行业链接名称')
    url = Column(String(500), nullable=False, unique=True, comment='行业链接URL')
    avatar = Column(String(500), default='/static/logo.svg', comment='头像URL')
    description = Column(Text, comment='行业链接描述')
    status = Column(Integer, default=1, comment='状态：1-启用，0-禁用')
    article_count = Column(Integer, default=0, comment='文章数量')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'avatar': self.avatar,
            'description': self.description or '',
            'status': self.status,
            'sync_time': self.updated_at.isoformat() if self.updated_at else '',
            'rss_url': f'/feed/{self.id}.rss',
            'article_count': self.article_count
        }