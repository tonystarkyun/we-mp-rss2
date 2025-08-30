
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, UploadFile, File,Request
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from core.auth import get_current_user
from core.db import DB
from core.wx import search_Biz
from .base import success_response, error_response
from datetime import datetime
from core.config import cfg
from core.res import save_avatar_locally
import csv
import io
import os
router = APIRouter(prefix=f"/export", tags=["导入/导出"])
@router.get("/mps/export", summary="导出公众号列表")
async def export_mps(
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    kw: str = Query(""),
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        from core.models.feed import Feed
        query = session.query(Feed)
        if kw:
            query = query.filter(Feed.mp_name.ilike(f"%{kw}%"))
        
        mps = query.order_by(Feed.created_at.desc()).limit(limit).offset(offset).all()
        
        # 准备CSV数据
        headers = ["id", "公众号名称", "封面图", "简介", "状态", "创建时间", "faker_id"]
        data = [[
            mp.id,
            mp.mp_name,
            mp.mp_cover,
            mp.mp_intro,
            mp.status,
            mp.created_at.isoformat(),
            mp.faker_id
        ] for mp in mps]
        
        # 创建临时CSV文件
        temp_file = "temp_mp_export.csv"
        with open(temp_file, "w", encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(data)
        
        # 返回文件下载
        return FileResponse(
            temp_file,
            media_type="text/csv",
            filename="公众号列表.csv",
            background=BackgroundTask(lambda: os.remove(temp_file))
        )
        
    except Exception as e:
        print(f"导出公众号列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="导出公众号列表失败"
            )
        )

@router.post("/mps/import", summary="导入公众号列表")
async def import_mps(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        from core.models.feed import Feed
        
        # 读取上传的CSV文件
        contents = (await file.read()).decode('utf-8-sig')
        csv_reader = csv.DictReader(io.StringIO(contents))
        
        # 验证必要字段
        required_columns = ["公众号名称", "封面图", "简介"]
        if not all(col in csv_reader.fieldnames for col in required_columns):
            missing_cols = [col for col in required_columns if col not in csv_reader.fieldnames]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    code=40001,
                    message=f"CSV文件缺少必要列: {', '.join(missing_cols)}"
                )
            )
        
        # 导入数据
        imported = 0
        updated = 0
        skipped = 0
        
        for row in csv_reader:
            mp_id = row["id"]
            mp_name = row["公众号名称"]
            mp_cover = row["封面图"]
            mp_intro = row.get("简介", "")
            status_val = int(row.get("状态", 1)) if row.get("状态") else 1
            faker_id = row.get("faker_id", "")
            
            # 检查是否已存在
            existing = session.query(Feed).filter(Feed.faker_id == faker_id).first()
            
            if existing:
                # 更新现有记录
                existing.mp_cover = mp_cover
                existing.mp_intro = mp_intro
                existing.status = status_val
                existing.faker_id = faker_id
                updated += 1
            else:
                # 创建新记录
                mp = Feed(
                    id=mp_id,
                    mp_name=mp_name,
                    mp_cover=mp_cover,
                    mp_intro=mp_intro,
                    status=status_val,
                    faker_id=faker_id,
                    created_at=datetime.now()
                )
                import base64
                if mp.id == None:
                    _mp_id=base64.b64decode(faker_id).decode("utf-8")
                    mp.id=f"MP_WXS_{_mp_id}"
                session.add(mp)
                imported += 1
        
        session.commit()
        
        return success_response({
            "message": "导入公众号列表成功",
            "stats": {
                "total": imported + updated + skipped,
                "imported": imported,
                "updated": updated,
                "skipped": skipped
            }
        })
        
    except Exception as e:
        session.rollback()
        print(f"导入公众号列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="导入公众号列表失败"
            )
        )

@router.get("/mps/opml", summary="导出公众号列表为OPML格式")
async def export_mps_opml(
    request: Request,
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    kw: str = Query(""),
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        from core.models.feed import Feed
        query = session.query(Feed)
        if kw:
            query = query.filter(Feed.mp_name.ilike(f"%{kw}%"))
        
        mps = query.order_by(Feed.created_at.desc()).limit(limit).offset(offset).all()
        rss_domain=cfg.get("rss.base_url",str(request.base_url))
        if rss_domain=="":
            rss_domain=str(request.base_url)
        # 生成OPML内容
        opml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.0">
  <head>
    <title>公众号订阅列表</title>
    <dateCreated>{date}</dateCreated>
  </head>
  <body>
{outlines}
  </body>
</opml>'''.format(
            date=datetime.now().isoformat(),
            outlines=''.join([f'<outline text="{mp.mp_name}" title="{mp.mp_name}" type="rss"  xmlUrl="{rss_domain}feed/{mp.id}.atom"/>\n' for mp in mps])
        )
        
        # 创建临时OPML文件
        temp_file = "temp_mp_export.opml"
        with open(temp_file, "w", encoding='utf-8') as f:
            f.write(opml_content)
        
        # 返回文件下载
        return FileResponse(
            temp_file,
            media_type="application/xml",
            filename="公众号订阅列表.opml",
            background=BackgroundTask(lambda: os.remove(temp_file))
        )
        
    except Exception as e:
        print(f"导出OPML列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50002,
                message="导出OPML列表失败"
            )
        )