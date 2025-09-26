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
from core.models.links import Link
from core.models.link_articles import LinkArticle
from sqlalchemy.orm import Session

router = APIRouter(prefix=f"/links", tags=["链接管理"])

class LinkCreate(BaseModel):
    name: str
    url: str
    avatar: Optional[str] = None
    description: Optional[str] = None

class LinkUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    avatar: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None

@router.get("", summary="获取链接列表")
async def get_links(
    limit: int = 10,
    offset: int = 0,
    kw: str = Query("", description="搜索关键词"),
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 构建查询
        query = session.query(Link)
        
        # 应用搜索过滤
        if kw:
            query = query.filter(
                (Link.name.like(f"%{kw}%")) | (Link.url.like(f"%{kw}%"))
            )
        
        # 获取总数
        total = query.count()
        
        # 应用分页和排序
        links = query.order_by(Link.updated_at.desc()).offset(offset).limit(limit).all()
        
        # 转换为字典格式
        link_list = [link.to_dict() for link in links]
        
        data = {
            'list': link_list,
            'page': {
                'limit': limit,
                'offset': offset
            },
            'total': total
        }
        return success_response(data)
    except Exception as e:
        print(f"获取链接列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50001,
                message=f"获取链接列表失败: {str(e)}",
            )
        )
    finally:
        session.close()

@router.post("", summary="添加订阅链接")
async def add_link(
    link_data: LinkCreate,
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 检查URL是否已存在
        existing_link = session.query(Link).filter(Link.url == link_data.url).first()
        if existing_link:
            return error_response(
                code=40001,
                message="该链接已存在"
            )
        
        # 爬取网站内容
        crawl_result = await crawl_website(link_data.url, max_articles=10)
        
        # 创建新链接记录
        new_link = Link(
            id=str(int(datetime.now().timestamp())),
            name=link_data.name or crawl_result['website_info']['title'] or link_data.url,
            url=link_data.url,
            avatar=link_data.avatar or "/static/logo.svg",
            description=link_data.description or crawl_result['website_info']['description'] or "",
            status=1,
            article_count=crawl_result['total_found']
        )
        
        # 保存到数据库
        session.add(new_link)
        session.flush()  # 获取new_link.id
        
        # 保存爬取的文章到数据库
        if crawl_result['success'] and crawl_result['articles']:
            import time
            for i, article in enumerate(crawl_result['articles']):
                # 生成唯一ID：时间戳 + 链接ID + 序号
                unique_id = f"{new_link.id}_{int(datetime.now().timestamp())}_{i}"
                link_article = LinkArticle(
                    id=unique_id,
                    link_id=new_link.id,
                    title=article.get('title', ''),
                    url=article.get('url', ''),
                    description=article.get('title', ''),  # 暂时用title作为描述
                    publish_time=article.get("publish_time_timestamp", ""),
                    status=1
                )
                session.add(link_article)
                # 避免同时间戳
                time.sleep(0.001)
        
        session.commit()
        
        return success_response({
            "message": "链接添加成功",
            "data": new_link.to_dict(),
            "crawl_result": {
                "success": crawl_result['success'],
                "articles_found": crawl_result['total_found'],
                "articles": crawl_result['articles'][:5]  # 只返回前5篇作为预览
            }
        })
    except Exception as e:
        session.rollback()
        print(f"添加链接错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50002,
                message=f"添加链接失败: {str(e)}",
            )
        )
    finally:
        session.close()

@router.get("/{link_id}", summary="获取链接详情")
async def get_link_detail(
    link_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        # TODO: 从数据库获取链接详情
        mock_link = {
            "id": link_id,
            "name": f"链接{link_id}",
            "url": f"https://example{link_id}.com",
            "avatar": "/static/logo.svg",
            "description": f"这是链接{link_id}的描述",
            "status": 1,
            "sync_time": "2024-01-01T12:00:00",
            "rss_url": f"/feed/{link_id}.rss",
            "article_count": 10
        }
        
        return success_response(mock_link)
    except Exception as e:
        print(f"获取链接详情错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50003,
                message=f"获取链接详情失败: {str(e)}",
            )
        )

@router.put("/{link_id}", summary="更新链接信息")
async def update_link(
    link_id: str,
    link_data: LinkUpdate,
    current_user: dict = Depends(get_current_user)
):
    try:
        # TODO: 更新数据库中的链接信息
        return success_response({"message": "链接更新成功"})
    except Exception as e:
        print(f"更新链接错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50004,
                message=f"更新链接失败: {str(e)}",
            )
        )

@router.delete("/{link_id}", summary="删除订阅链接")
async def delete_link(
    link_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 查找链接
        link = session.query(Link).filter(Link.id == link_id).first()
        if not link:
            return error_response(
                code=40004,
                message="链接不存在"
            )
        
        # 先删除该链接下的所有文章
        articles = session.query(LinkArticle).filter(LinkArticle.link_id == link_id).all()
        for article in articles:
            session.delete(article)
        
        # 再删除链接本身
        session.delete(link)
        session.commit()
        
        # 清理缓存文件 (RSS缓存等)
        try:
            from core.rss import RSS
            rss = RSS()
            rss.clear_cache(mp_id=link_id)
            print(f"已清理链接 {link_id} 的RSS缓存")
        except Exception as cache_error:
            print(f"清理缓存文件时出错: {cache_error}")
        
        # 清理头像文件 (如果有)
        try:
            import os
            if link.avatar and link.avatar != "/static/logo.svg" and os.path.exists(link.avatar):
                os.remove(link.avatar)
                print(f"已删除头像文件: {link.avatar}")
        except Exception as file_error:
            print(f"清理头像文件时出错: {file_error}")
        
        return success_response({
            "message": "链接及其文章删除成功",
            "id": link_id,
            "deleted_articles_count": len(articles)
        })
    except Exception as e:
        session.rollback()
        print(f"删除链接错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50005,
                message=f"删除链接失败: {str(e)}",
            )
        )
    finally:
        session.close()

@router.get("/update/{link_id}", summary="更新链接内容")
async def update_link_content(
    link_id: str,
    start_page: int = Query(0, description="开始页数"),
    end_page: int = Query(1, description="结束页数"),
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 查找链接
        link = session.query(Link).filter(Link.id == link_id).first()
        if not link:
            return error_response(
                code=40004,
                message="链接不存在"
            )
        
        print(f"开始更新链接内容: {link.name} ({link.url})")
        
        # 计算需要爬取的文章数量（简单实现，每页10篇文章）
        articles_per_page = 10
        max_articles = (end_page - start_page + 1) * articles_per_page
        
        # 重新爬取网站内容
        crawl_result = await crawl_website(link.url, max_articles=max_articles)
        
        if not crawl_result['success']:
            return error_response(
                code=50007,
                message=f"爬取失败: {crawl_result.get('error', '未知错误')}"
            )
        
        # 删除旧文章（可选，这里选择保留旧文章，只添加新文章）
        # 保存新爬取的文章
        new_articles_count = 0
        if crawl_result['articles']:
            import time
            for i, article in enumerate(crawl_result['articles']):
                # 检查文章是否已存在（通过URL去重）
                existing = session.query(LinkArticle).filter(
                    LinkArticle.link_id == link_id,
                    LinkArticle.url == article.get('url', '')
                ).first()
                
                if existing:
                    continue  # 跳过已存在的文章
                
                # 生成唯一ID
                unique_id = f"{link_id}_{int(datetime.now().timestamp())}_{i}"
                link_article = LinkArticle(
                    id=unique_id,
                    link_id=link_id,
                    title=article.get('title', ''),
                    url=article.get('url', ''),
                    publish_time=article.get("publish_time_timestamp", ""),
                    status=1
                )
                session.add(link_article)
                new_articles_count += 1
                time.sleep(0.001)
        
        # 更新链接的文章数量和更新时间
        total_articles = session.query(LinkArticle).filter(
            LinkArticle.link_id == link_id,
            LinkArticle.status != 1000
        ).count()
        link.article_count = total_articles
        
        session.commit()
        
        print(f"链接更新完成: 新增{new_articles_count}篇文章，总计{total_articles}篇文章")
        
        return success_response({
            "message": f"链接内容更新成功",
            "new_articles": new_articles_count,
            "total_articles": total_articles,
            "crawl_info": {
                "success": crawl_result['success'],
                "articles_found": crawl_result['total_found']
            }
        })
    except Exception as e:
        session.rollback()
        print(f"更新链接内容错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50006,
                message=f"更新链接内容失败: {str(e)}",
            )
        )
    finally:
        session.close()

@router.get("/export", summary="导出链接")
async def export_links(
    current_user: dict = Depends(get_current_user)
):
    try:
        # TODO: 实现链接导出逻辑
        mock_data = [
            {"name": "示例链接1", "url": "https://example1.com", "description": "示例描述1"},
            {"name": "示例链接2", "url": "https://example2.com", "description": "示例描述2"}
        ]
        
        # 创建临时文件
        temp_file = f"/tmp/links_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f, ensure_ascii=False, indent=2)
        
        return FileResponse(
            temp_file,
            media_type='application/json',
            filename=f"links_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
    except Exception as e:
        print(f"导出链接错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50007,
                message=f"导出链接失败: {str(e)}",
            )
        )

class CrawlTestRequest(BaseModel):
    url: str
    max_articles: int = 10

@router.post("/crawl-test", summary="测试网站爬虫")
async def test_website_crawl(
    request: CrawlTestRequest,
    current_user: dict = Depends(get_current_user)
):
    """测试爬取指定网站的内容"""
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
        print(f"测试爬虫错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50009,
                message=f"测试爬虫失败: {str(e)}",
            )
        )

@router.post("/import", summary="导入链接")
async def import_links(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        # 读取上传的文件
        content = await file.read()
        links_data = json.loads(content.decode('utf-8'))
        
        # TODO: 实现链接导入逻辑，保存到数据库
        imported_count = len(links_data)
        
        return success_response({
            "message": f"成功导入{imported_count}个链接",
            "count": imported_count
        })
    except Exception as e:
        print(f"导入链接错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50008,
                message=f"导入链接失败: {str(e)}",
            )
        )