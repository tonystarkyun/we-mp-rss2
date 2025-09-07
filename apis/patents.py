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
from core.models.patents import Patent
from core.models.patent_articles import PatentArticle
from sqlalchemy.orm import Session

router = APIRouter(prefix=f"/patents", tags=["专利检索"])

class PatentCreate(BaseModel):
    name: str
    url: str
    avatar: Optional[str] = None
    description: Optional[str] = None

class PatentUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    avatar: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None

@router.get("", summary="获取专利链接列表")
async def get_patents(
    limit: int = 10,
    offset: int = 0,
    kw: str = Query("", description="搜索关键词"),
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 构建查询
        query = session.query(Patent)
        
        # 应用搜索过滤
        if kw:
            query = query.filter(
                (Patent.name.like(f"%{kw}%")) | (Patent.url.like(f"%{kw}%"))
            )
        
        # 获取总数
        total = query.count()
        
        # 应用分页和排序
        patents = query.order_by(Patent.updated_at.desc()).offset(offset).limit(limit).all()
        
        # 转换为字典格式
        patent_list = [patent.to_dict() for patent in patents]
        
        data = {
            'list': patent_list,
            'page': {
                'limit': limit,
                'offset': offset
            },
            'total': total
        }
        return success_response(data)
    except Exception as e:
        print(f"获取专利链接列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50001,
                message=f"获取专利链接列表失败: {str(e)}",
            )
        )
    finally:
        session.close()

@router.post("", summary="添加专利检索链接")
async def add_patent(
    patent_data: PatentCreate,
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 检查URL是否已存在
        existing_patent = session.query(Patent).filter(Patent.url == patent_data.url).first()
        if existing_patent:
            return error_response(
                code=40001,
                message="该专利链接已存在"
            )
        
        # 爬取网站内容
        crawl_result = await crawl_website(patent_data.url, max_articles=10)
        
        # 创建新专利链接记录
        new_patent = Patent(
            id=str(int(datetime.now().timestamp())),
            name=patent_data.name or crawl_result['website_info']['title'] or patent_data.url,
            url=patent_data.url,
            avatar=patent_data.avatar or "/static/logo.svg",
            description=patent_data.description or crawl_result['website_info']['description'] or "",
            status=1,
            article_count=crawl_result['total_found']
        )
        
        # 保存到数据库
        session.add(new_patent)
        session.flush()  # 获取new_patent.id
        
        # 保存爬取的文章到数据库
        if crawl_result['success'] and crawl_result['articles']:
            import time
            for i, article in enumerate(crawl_result['articles']):
                # 生成唯一ID：时间戳 + 专利ID + 序号
                unique_id = f"{new_patent.id}_{int(datetime.now().timestamp())}_{i}"
                patent_article = PatentArticle(
                    id=unique_id,
                    patent_id=new_patent.id,
                    title=article.get('title', ''),
                    url=article.get('url', ''),
                    publish_time=article.get("publish_time_timestamp", ""),
                    status=1
                )
                session.add(patent_article)
                # 避免同时间戳
                time.sleep(0.001)
        
        session.commit()
        
        return success_response({
            "message": "专利链接添加成功",
            "data": new_patent.to_dict(),
            "crawl_result": {
                "success": crawl_result['success'],
                "articles_found": crawl_result['total_found'],
                "articles": crawl_result['articles'][:5]  # 只返回前5篇作为预览
            }
        })
    except Exception as e:
        session.rollback()
        print(f"添加专利链接错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50002,
                message=f"添加专利链接失败: {str(e)}",
            )
        )
    finally:
        session.close()

@router.delete("/{patent_id}", summary="删除专利链接")
async def delete_patent(
    patent_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 查找专利链接
        patent = session.query(Patent).filter(Patent.id == patent_id).first()
        if not patent:
            return error_response(
                code=40004,
                message="专利链接不存在"
            )
        
        # 先删除该专利链接下的所有文章
        articles = session.query(PatentArticle).filter(PatentArticle.patent_id == patent_id).all()
        for article in articles:
            session.delete(article)
        
        # 再删除专利链接本身
        session.delete(patent)
        session.commit()
        
        # 清理缓存文件 (RSS缓存等)
        try:
            from core.rss import RSS
            rss = RSS()
            rss.clear_cache(mp_id=patent_id)
            print(f"已清理专利链接 {patent_id} 的RSS缓存")
        except Exception as cache_error:
            print(f"清理缓存文件时出错: {cache_error}")
        
        # 清理头像文件 (如果有)
        try:
            import os
            if patent.avatar and patent.avatar != "/static/logo.svg" and os.path.exists(patent.avatar):
                os.remove(patent.avatar)
                print(f"已删除头像文件: {patent.avatar}")
        except Exception as file_error:
            print(f"清理头像文件时出错: {file_error}")
        
        return success_response({
            "message": "专利链接及其文章删除成功",
            "id": patent_id,
            "deleted_articles_count": len(articles)
        })
    except Exception as e:
        session.rollback()
        print(f"删除专利链接错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50005,
                message=f"删除专利链接失败: {str(e)}",
            )
        )
    finally:
        session.close()

@router.get("/update/{patent_id}", summary="更新专利内容")
async def update_patent_content(
    patent_id: str,
    start_page: int = Query(0, description="开始页数"),
    end_page: int = Query(1, description="结束页数"),
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 查找专利链接
        patent = session.query(Patent).filter(Patent.id == patent_id).first()
        if not patent:
            return error_response(
                code=40004,
                message="专利链接不存在"
            )
        
        print(f"开始更新专利内容: {patent.name} ({patent.url})")
        
        # 计算需要爬取的文章数量（简单实现，每页10篇文章）
        articles_per_page = 10
        max_articles = (end_page - start_page + 1) * articles_per_page
        
        # 重新爬取网站内容
        crawl_result = await crawl_website(patent.url, max_articles=max_articles)
        
        if not crawl_result['success']:
            return error_response(
                code=50007,
                message=f"爬取失败: {crawl_result.get('error', '未知错误')}"
            )
        
        # 保存新爬取的文章
        new_articles_count = 0
        if crawl_result['articles']:
            import time
            for i, article in enumerate(crawl_result['articles']):
                # 检查文章是否已存在（通过URL去重）
                existing = session.query(PatentArticle).filter(
                    PatentArticle.patent_id == patent_id,
                    PatentArticle.url == article.get('url', '')
                ).first()
                
                if existing:
                    continue  # 跳过已存在的文章
                
                # 生成唯一ID
                unique_id = f"{patent_id}_{int(datetime.now().timestamp())}_{i}"
                patent_article = PatentArticle(
                    id=unique_id,
                    patent_id=patent_id,
                    title=article.get('title', ''),
                    url=article.get('url', ''),
                    publish_time=article.get("publish_time_timestamp", ""),
                    status=1
                )
                session.add(patent_article)
                new_articles_count += 1
                time.sleep(0.001)
        
        # 更新专利链接的文章数量和更新时间
        total_articles = session.query(PatentArticle).filter(
            PatentArticle.patent_id == patent_id,
            PatentArticle.status != 1000
        ).count()
        patent.article_count = total_articles
        
        session.commit()
        
        print(f"专利更新完成: 新增{new_articles_count}篇文章，总计{total_articles}篇文章")
        
        return success_response({
            "message": f"专利内容更新成功",
            "new_articles": new_articles_count,
            "total_articles": total_articles,
            "crawl_info": {
                "success": crawl_result['success'],
                "articles_found": crawl_result['total_found']
            }
        })
    except Exception as e:
        session.rollback()
        print(f"更新专利内容错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50006,
                message=f"更新专利内容失败: {str(e)}",
            )
        )
    finally:
        session.close()

class CrawlTestRequest(BaseModel):
    url: str
    max_articles: int = 10

@router.post("/crawl-test", summary="测试专利网站爬虫")
async def test_patent_crawl(
    request: CrawlTestRequest,
    current_user: dict = Depends(get_current_user)
):
    """测试爬取指定专利网站的内容"""
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
        print(f"测试专利爬虫错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50009,
                message=f"测试专利爬虫失败: {str(e)}",
            )
        )