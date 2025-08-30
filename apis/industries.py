from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.background import BackgroundTasks
from core.auth import get_current_user
from core.db import DB
from .base import success_response, error_response
from datetime import datetime
from core.config import cfg
import io
import os
import json
from typing import Optional, List
from pydantic import BaseModel
from core.crawler import crawl_website
from core.models.industries import Industry
from core.models.industry_articles import IndustryArticle
from sqlalchemy.orm import Session

router = APIRouter(prefix=f"/industries", tags=["行业动态"])

class IndustryCreate(BaseModel):
    name: str
    url: str
    avatar: Optional[str] = None
    description: Optional[str] = None

class IndustryUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    avatar: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None

@router.get("", summary="获取行业动态链接列表")
async def get_industries(
    limit: int = 10,
    offset: int = 0,
    kw: str = Query("", description="搜索关键词"),
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 构建查询
        query = session.query(Industry)
        
        # 应用搜索过滤
        if kw:
            query = query.filter(
                (Industry.name.like(f"%{kw}%")) | (Industry.url.like(f"%{kw}%"))
            )
        
        # 获取总数
        total = query.count()
        
        # 应用分页和排序
        industries = query.order_by(Industry.updated_at.desc()).offset(offset).limit(limit).all()
        
        # 转换为字典格式
        industry_list = [industry.to_dict() for industry in industries]
        
        data = {
            'list': industry_list,
            'page': {
                'limit': limit,
                'offset': offset
            },
            'total': total
        }
        return success_response(data)
    except Exception as e:
        print(f"获取行业动态链接列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50001,
                message=f"获取行业动态链接列表失败: {str(e)}",
            )
        )
    finally:
        session.close()

@router.post("", summary="添加行业动态链接")
async def add_industry(
    industry_data: IndustryCreate,
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 检查URL是否已存在
        existing_industry = session.query(Industry).filter(Industry.url == industry_data.url).first()
        if existing_industry:
            return error_response(
                code=40001,
                message="该行业动态链接已存在"
            )
        
        # 爬取网站内容
        crawl_result = await crawl_website(industry_data.url, max_articles=10)
        
        # 创建新行业动态链接记录
        new_industry = Industry(
            id=str(int(datetime.now().timestamp())),
            name=industry_data.name or crawl_result['website_info']['title'] or industry_data.url,
            url=industry_data.url,
            avatar=industry_data.avatar or "/static/logo.svg",
            description=industry_data.description or crawl_result['website_info']['description'] or "",
            status=1,
            article_count=crawl_result['total_found']
        )
        
        # 保存到数据库
        session.add(new_industry)
        session.flush()  # 获取new_industry.id
        
        # 保存爬取的文章到数据库
        if crawl_result['success'] and crawl_result['articles']:
            import time
            for i, article in enumerate(crawl_result['articles']):
                # 生成唯一ID：时间戳 + 行业ID + 序号
                unique_id = f"{new_industry.id}_{int(datetime.now().timestamp())}_{i}"
                industry_article = IndustryArticle(
                    id=unique_id,
                    industry_id=new_industry.id,
                    title=article.get('title', ''),
                    url=article.get('url', ''),
                    publish_time=int(datetime.now().timestamp()),
                    status=1
                )
                session.add(industry_article)
                # 避免同时间戳
                time.sleep(0.001)
        
        session.commit()
        
        return success_response({
            "message": "行业动态链接添加成功",
            "data": new_industry.to_dict(),
            "crawl_result": {
                "success": crawl_result['success'],
                "articles_found": crawl_result['total_found'],
                "articles": crawl_result['articles'][:5]  # 只返回前5篇作为预览
            }
        })
    except Exception as e:
        session.rollback()
        print(f"添加行业动态链接错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50002,
                message=f"添加行业动态链接失败: {str(e)}",
            )
        )
    finally:
        session.close()

@router.delete("/{industry_id}", summary="删除行业动态链接")
async def delete_industry(
    industry_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 查找行业动态链接
        industry = session.query(Industry).filter(Industry.id == industry_id).first()
        if not industry:
            return error_response(
                code=40004,
                message="行业动态链接不存在"
            )
        
        # 删除行业动态链接
        session.delete(industry)
        session.commit()
        
        return success_response({"message": "行业动态链接删除成功"})
    except Exception as e:
        session.rollback()
        print(f"删除行业动态链接错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50005,
                message=f"删除行业动态链接失败: {str(e)}",
            )
        )
    finally:
        session.close()

@router.get("/update/{industry_id}", summary="更新行业动态内容")
async def update_industry_content(
    industry_id: str,
    start_page: int = Query(0, description="开始页数"),
    end_page: int = Query(1, description="结束页数"),
    current_user: dict = Depends(get_current_user)
):
    try:
        return success_response({"message": f"行业动态{industry_id}内容更新成功"})
    except Exception as e:
        print(f"更新行业动态内容错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50006,
                message=f"更新行业动态内容失败: {str(e)}",
            )
        )

class CrawlTestRequest(BaseModel):
    url: str
    max_articles: int = 10

@router.post("/crawl-test", summary="测试行业动态网站爬虫")
async def test_industry_crawl(
    request: CrawlTestRequest,
    current_user: dict = Depends(get_current_user)
):
    """测试爬取指定行业动态网站的内容"""
    try:
        result = await crawl_website(request.url, request.max_articles)
        
        return success_response({
            "website_info": result['website_info'],
            "crawl_success": result['success'],
            "articles_found": result['total_found'],
            "articles": result['articles'],
            "error": result['error']
        })
    except Exception as e:
        print(f"测试行业动态爬虫错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50009,
                message=f"测试行业动态爬虫失败: {str(e)}",
            )
        )