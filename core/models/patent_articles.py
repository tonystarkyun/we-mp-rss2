# core/models/patent_articles.py - 专利文章数据模型
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from .base import Base

class PatentArticle(Base):
    """专利检索文章数据模型"""
    __tablename__ = 'patent_articles'
    
    id = Column(String(50), primary_key=True, comment='文章ID')
    patent_id = Column(String(50), ForeignKey('patents.id'), nullable=False, comment='专利链接ID')
    title = Column(String(500), nullable=False, comment='文章标题')
    url = Column(String(1000), nullable=False, comment='文章URL')
    content = Column(Text, comment='文章内容')
    author = Column(String(100), comment='作者')
    publish_time = Column(Integer, comment='发布时间戳')
    status = Column(Integer, default=1, comment='状态：1-正常，1000-删除')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'patent_id': self.patent_id,
            'title': self.title,
            'url': self.url,
            'content': self.content or '',
            'author': self.author or '',
            'publish_time': self.publish_time,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else '',
            'updated_at': self.updated_at.isoformat() if self.updated_at else ''
        }