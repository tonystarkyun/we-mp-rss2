#!/usr/bin/env python3
from core.models.user import User
from core.db import Db
from core.auth import pwd_context
import uuid
import os
from datetime import datetime

# 创建数据库连接
db = Db(tag="用户创建")

def create_admin_user():
    """创建管理员用户"""
    try:
        username = "zkzc"
        password = os.getenv("PASSWORD", "wf2151328")
        
        session = db.get_session()
        
        # 检查用户是否已存在
        existing_user = session.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"用户 {username} 已存在")
            session.close()
            return existing_user
        
        # 创建新用户
        user = User(
            id=str(uuid.uuid4()),  # 使用UUID作为字符串ID
            username=username,
            password_hash=pwd_context.hash(password),
            role="admin",
            is_active=True,
            nickname="管理员",
            permissions="all",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        session.add(user)
        session.commit()
        session.close()
        
        print(f"✅ 成功创建管理员用户: {username}")
        print(f"🔑 密码: {password}")
        return user
        
    except Exception as e:
        print(f"❌ 创建用户失败: {str(e)}")
        return None

if __name__ == "__main__":
    create_admin_user()