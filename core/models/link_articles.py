# core/models/link_articles.py - 链接文章数据模型
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from .base import Base

class LinkArticle(Base):
    """链接文章数据模型"""
    __tablename__ = 'link_articles'
    
    id = Column(String(50), primary_key=True, comment='文章ID')
    link_id = Column(String(50), ForeignKey('links.id'), nullable=False, comment='链接ID')
    title = Column(String(500), nullable=False, comment='文章标题')
    url = Column(String(1000), nullable=False, comment='文章URL')
    description = Column(Text, comment='文章描述')
    pic_url = Column(String(500), comment='文章封面图片URL')
    status = Column(Integer, default=1, comment='状态：1-正常，0-禁用，1000-删除')
    publish_time = Column(Integer, comment='发布时间戳')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    is_export = Column(Integer, default=0, comment='是否已导出：1-是，0-否')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'link_id': self.link_id,
            'title': self.title,
            'url': self.url,
            'description': self.description or '',
            'pic_url': self.pic_url or '',
            'status': self.status,
            'publish_time': self.publish_time,
            'created_at': self.created_at.isoformat() if self.created_at else '',
            'updated_at': self.updated_at.isoformat() if self.updated_at else '',
            'is_export': self.is_export,
            'mp_name': '链接文章',  # 兼容前端显示
            'account_name': '链接文章'
        }