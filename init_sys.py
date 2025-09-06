from core.models.user import User
from core.models.article import Article
from core.models.config_management import ConfigManagement
from core.models.feed import Feed
from core.models.message_task import MessageTask
from core.db import Db,DB
from core.config import cfg
from core.auth import pwd_context
import time
import os
from core.print import print_info, print_error
def init_user(_db: Db):
    try:
      username,password="zkzc",os.getenv("PASSWORD", "wf2151328")
      session=_db.get_session()
      session.add(User(
          id=0,
          username=username,
          password_hash=pwd_context.hash(password),
          role="admin",  # 设置为管理员角色
          is_active=True
          ))
      session.commit()
      print_info(f"初始化用户成功,请使用以下凭据登录：{username}")
    except Exception as e:
        # print_error(f"Init error: {str(e)}")
        pass
def sync_models():
     # 同步模型到表结构
         from data_sync import DatabaseSynchronizer
         DB.create_tables()
         time.sleep(3)
         synchronizer = DatabaseSynchronizer(db_url=cfg.get("db",""))
         synchronizer.sync()
         print_info("模型同步完成")

     

 
def init():
    sync_models()
    init_user(DB)

if __name__ == '__main__':
    init()