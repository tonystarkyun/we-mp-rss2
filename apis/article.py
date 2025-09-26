from fastapi import APIRouter, Depends, HTTPException, status as fast_status, Query
from core.auth import get_current_user
from core.db import DB
from core.models.base import DATA_STATUS
from core.models.article import Article,ArticleBase
from sqlalchemy import and_, or_, desc
from .base import success_response, error_response
from core.config import cfg
from apis.base import format_search_kw
from core.print import print_warning, print_info, print_error, print_success
router = APIRouter(prefix=f"/articles", tags=["文章管理"])


    
@router.delete("/clean", summary="清理无效文章(MP_ID不存在于Feeds表中的文章)")
async def clean_orphan_articles(
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        from core.models.feed import Feed
        from core.models.article import Article
        
        # 找出Articles表中mp_id不在Feeds表中的记录
        subquery = session.query(Feed.id).subquery()
        deleted_count = session.query(Article)\
            .filter(~Article.mp_id.in_(subquery))\
            .delete(synchronize_session=False)
        
        session.commit()
        
        return success_response({
            "message": "清理无效文章成功",
            "deleted_count": deleted_count
        })
    except Exception as e:
        session.rollback()
        print(f"清理无效文章错误: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="清理无效文章失败"
            )
        )
    
@router.delete("/clean_duplicate_articles", summary="清理重复文章")
async def clean_duplicate(
    current_user: dict = Depends(get_current_user)
):
    try:
        from tools.clean import clean_duplicate_articles
        (msg, deleted_count) =clean_duplicate_articles()
        return success_response({
            "message": msg,
            "deleted_count": deleted_count
        })
    except Exception as e:
        print(f"清理重复文章: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="清理重复文章"
            )
        )


@router.api_route("", summary="获取文章列表",methods= ["GET", "POST"], operation_id="get_articles_list")
async def get_articles(
    offset: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=100),
    status: str = Query(None),
    search: str = Query(None),
    mp_id: str = Query(None),
    link_id: str = Query(None),
    patent_id: str = Query(None),
    industry_id: str = Query(None),
    has_content:bool=Query(False),
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 如果是查询专利文章 (patent_id参数存在，即使为空字符串)
        if patent_id is not None:
            print(f"查询专利文章，patent_id: {patent_id}")
            try:
                from core.models.patent_articles import PatentArticle
                query = session.query(PatentArticle)
                if status:
                    query = query.filter(PatentArticle.status == int(status))
                else:
                    query = query.filter(PatentArticle.status != 1000)  # 排除已删除
                if patent_id != '':  # 如果不是查询全部
                    query = query.filter(PatentArticle.patent_id == patent_id)
                if search:
                    query = query.filter(PatentArticle.title.like(f'%{search}%'))
                    
                # 获取总数
                total = query.count()
                print(f"专利文章总数: {total}")
                query = query.order_by(PatentArticle.publish_time.desc()).offset(offset).limit(limit)
                articles = query.all()
                print(f"查询到专利文章数量: {len(articles)}")
                
                # 转换为统一格式
                article_list = []
                for article in articles:
                    article_dict = article.to_dict()
                    article_list.append(article_dict)
                    
                from .base import success_response
                return success_response({
                    "list": article_list,
                    "total": total
                })
            except Exception as e:
                print(f"查询专利文章错误: {str(e)}")
                import traceback
                traceback.print_exc()
                raise e
        
        # 如果是查询行业动态文章 (industry_id参数存在，即使为空字符串)
        if industry_id is not None:
            print(f"查询行业动态文章，industry_id: {industry_id}")
            try:
                from core.models.industry_articles import IndustryArticle
                query = session.query(IndustryArticle)
                if status:
                    query = query.filter(IndustryArticle.status == int(status))
                else:
                    query = query.filter(IndustryArticle.status != 1000)  # 排除已删除
                if industry_id != '':  # 如果不是查询全部
                    query = query.filter(IndustryArticle.industry_id == industry_id)
                if search:
                    query = query.filter(IndustryArticle.title.like(f'%{search}%'))
                    
                # 获取总数
                total = query.count()
                print(f"行业动态文章总数: {total}")
                query = query.order_by(IndustryArticle.publish_time.desc()).offset(offset).limit(limit)
                articles = query.all()
                print(f"查询到行业动态文章数量: {len(articles)}")
                
                # 转换为统一格式
                article_list = []
                for article in articles:
                    article_dict = article.to_dict()
                    article_list.append(article_dict)
                    
                from .base import success_response
                return success_response({
                    "list": article_list,
                    "total": total
                })
            except Exception as e:
                print(f"查询行业动态文章错误: {str(e)}")
                import traceback
                traceback.print_exc()
                raise e
        
        # 如果是查询链接文章 (link_id参数存在，即使为空字符串)
        if link_id is not None:
            print(f"查询链接文章，link_id: {link_id}")
            try:
                from core.models.link_articles import LinkArticle
                query = session.query(LinkArticle)
                if status:
                    query = query.filter(LinkArticle.status == int(status))
                else:
                    query = query.filter(LinkArticle.status != 1000)  # 排除已删除
                if link_id != '':  # 如果不是查询全部
                    query = query.filter(LinkArticle.link_id == link_id)
                if search:
                    query = query.filter(LinkArticle.title.like(f'%{search}%'))
                    
                # 获取总数
                total = query.count()
                print(f"链接文章总数: {total}")
                query = query.order_by(LinkArticle.publish_time.desc()).offset(offset).limit(limit)
                articles = query.all()
                print(f"查询到链接文章数量: {len(articles)}")
                
                # 转换为统一格式
                article_list = []
                for article in articles:
                    article_dict = article.to_dict()
                    article_list.append(article_dict)
                    
                from .base import success_response
                return success_response({
                    "list": article_list,
                    "total": total
                })
            except Exception as e:
                print(f"查询链接文章错误: {str(e)}")
                import traceback
                traceback.print_exc()
                raise e
        
        # 原有的公众号文章查询逻辑
        # 构建查询条件
        query = session.query(ArticleBase)
        if has_content:
            query=session.query(Article)
        if status:
            query = query.filter(Article.status == status)
        else:
            query = query.filter(Article.status != DATA_STATUS.DELETED)
        if mp_id:
            query = query.filter(Article.mp_id == mp_id)
        if search:
            query = query.filter(
               format_search_kw(search)
            )
        
        # 获取总数
        total = query.count()
        query= query.order_by(Article.publish_time.desc()).offset(offset).limit(limit)
        # query= query.order_by(Article.id.desc()).offset(offset).limit(limit)
        # 分页查询（按发布时间降序）
        articles = query.all()
        
        # 打印生成的 SQL 语句（包含分页参数）
        print_warning(query.statement.compile(compile_kwargs={"literal_binds": True}))
                       
        # 查询公众号名称
        from core.models.feed import Feed
        mp_names = {}
        for article in articles:
            if article.mp_id and article.mp_id not in mp_names:
                feed = session.query(Feed).filter(Feed.id == article.mp_id).first()
                mp_names[article.mp_id] = feed.mp_name if feed else "未知公众号"
        
        # 合并公众号名称到文章列表
        article_list = []
        for article in articles:
            article_dict = article.__dict__
            article_dict["mp_name"] = mp_names.get(article.mp_id, "未知公众号")
            article_list.append(article_dict)
        
        from .base import success_response
        return success_response({
            "list": article_list,
            "total": total
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"获取文章列表异常: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=fast_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50001,
                message=f"获取文章列表失败: {str(e)}"
            )
        )
    finally:
        session.close()

@router.get("/{article_id}", summary="获取文章详情")
async def get_article_detail(
    article_id: str,
    content: bool = False,
    # current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        article = session.query(Article).filter(Article.id==article_id).filter(Article.status != DATA_STATUS.DELETED).first()
        if not article:
            from .base import error_response
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="文章不存在"
                )
            )
        return success_response(article)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"获取文章详情失败: {str(e)}"
            )
        )   

@router.delete("/{article_id}", summary="删除文章")
async def delete_article(
    article_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        article_deleted = False
        delete_message = "文章不存在"
        
        # 尝试删除公众号文章
        from core.models.article import Article
        article = session.query(Article).filter(Article.id == article_id).first()
        if article:
            article.status = DATA_STATUS.DELETED
            if cfg.get("article.true_delete", False):
                session.delete(article)
            session.commit()
            article_deleted = True
            delete_message = "公众号文章已删除"
        
        # 如果不是公众号文章，尝试删除专利文章
        if not article_deleted:
            try:
                from core.models.patent_articles import PatentArticle
                patent_article = session.query(PatentArticle).filter(PatentArticle.id == article_id).first()
                if patent_article:
                    session.delete(patent_article)
                    session.commit()
                    article_deleted = True
                    delete_message = "专利文章已删除"
            except Exception as e:
                print(f"尝试删除专利文章失败: {str(e)}")
        
        # 如果不是专利文章，尝试删除行业动态文章
        if not article_deleted:
            try:
                from core.models.industry_articles import IndustryArticle
                industry_article = session.query(IndustryArticle).filter(IndustryArticle.id == article_id).first()
                if industry_article:
                    session.delete(industry_article)
                    session.commit()
                    article_deleted = True
                    delete_message = "行业动态文章已删除"
            except Exception as e:
                print(f"尝试删除行业动态文章失败: {str(e)}")
        
        # 如果不是行业动态文章，尝试删除链接文章
        if not article_deleted:
            try:
                from core.models.link_articles import LinkArticle
                link_article = session.query(LinkArticle).filter(LinkArticle.id == article_id).first()
                if link_article:
                    session.delete(link_article)
                    session.commit()
                    article_deleted = True
                    delete_message = "链接文章已删除"
            except Exception as e:
                print(f"尝试删除链接文章失败: {str(e)}")
        
        if not article_deleted:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="文章不存在或已被删除"
                )
            )
        
        return success_response(None, message=delete_message)
    except HTTPException as e:
        raise e
    except Exception as e:
        session.rollback()
        print(f"删除文章异常: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50001,
                message=f"删除文章失败: {str(e)}"
            )
        )

@router.get("/{article_id}/next", summary="获取下一篇文章")
async def get_next_article(
    article_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 获取当前文章的发布时间
        current_article = session.query(Article).filter(Article.id == article_id).first()
        if not current_article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="当前文章不存在"
                )
            )
        
        # 查询发布时间更晚的第一篇文章
        next_article = session.query(Article)\
            .filter(Article.publish_time > current_article.publish_time)\
            .filter(Article.status != DATA_STATUS.DELETED)\
            .filter(Article.mp_id == current_article.mp_id)\
            .order_by(Article.publish_time.asc())\
            .first()
        
        if not next_article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40402,
                    message="没有下一篇文章"
                )
            )
        
        return success_response(next_article)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"获取下一篇文章失败: {str(e)}"
            )
        )

@router.get("/{article_id}/prev", summary="获取上一篇文章")
async def get_prev_article(
    article_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 获取当前文章的发布时间
        current_article = session.query(Article).filter(Article.id == article_id).first()
        if not current_article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="当前文章不存在"
                )
            )
        
        # 查询发布时间更早的第一篇文章
        prev_article = session.query(Article)\
            .filter(Article.publish_time < current_article.publish_time)\
            .filter(Article.status != DATA_STATUS.DELETED)\
            .filter(Article.mp_id == current_article.mp_id)\
            .order_by(Article.publish_time.desc())\
            .first()
        
        if not prev_article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40403,
                    message="没有上一篇文章"
                )
            )
        
        return success_response(prev_article)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"获取上一篇文章失败: {str(e)}"
            )
        )