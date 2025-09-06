#!/usr/bin/env python3
"""
检查并修复用户数据
"""
import os
import sqlite3
import sys
sys.path.append('.')

def check_and_fix_user():
    """检查并修复用户数据"""
    db_path = "dist/data/db.db"
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查用户表结构
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("👤 用户表结构:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # 检查现有用户
        cursor.execute("SELECT id, username, password_hash, role, is_active FROM users")
        users = cursor.fetchall()
        print(f"\n📋 现有用户 ({len(users)} 个):")
        for user in users:
            print(f"   ID: {user[0]}, 用户名: {user[1]}, 角色: {user[3]}, 激活: {user[4]}")
            print(f"   密码哈希: {user[2][:50]}...")
        
        if not users:
            print("\n⚠️  没有找到任何用户，需要创建默认管理员")
            create_default_admin(cursor)
        else:
            # 检查默认管理员
            admin_user = None
            for user in users:
                if user[1] == 'zkzc' or user[0] == 0:
                    admin_user = user
                    break
            
            if not admin_user:
                print("\n⚠️  没有找到默认管理员 'zkzc'，需要创建")
                create_default_admin(cursor)
            else:
                print(f"\n✅ 找到默认管理员: {admin_user[1]}")
                # 验证密码哈希
                verify_password_hash(admin_user[2])
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ 检查过程中出错: {e}")
    finally:
        conn.close()

def create_default_admin(cursor):
    """创建默认管理员"""
    try:
        # 导入密码哈希模块
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        username = "zkzc"
        password = "wf2151328"
        password_hash = pwd_context.hash(password)
        
        # 删除可能存在的旧用户
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        
        # 插入新的默认管理员
        cursor.execute("""
            INSERT INTO users (id, username, password_hash, role, is_active) 
            VALUES (0, ?, ?, 'admin', 1)
        """, (username, password_hash))
        
        print(f"✅ 创建默认管理员成功")
        print(f"   用户名: {username}")
        print(f"   密码: {password}")
        print(f"   角色: admin")
        print(f"   哈希: {password_hash}")
        
    except Exception as e:
        print(f"❌ 创建管理员失败: {e}")

def verify_password_hash(hash_value):
    """验证密码哈希格式"""
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # 尝试验证密码
        is_valid = pwd_context.verify("wf2151328", hash_value)
        print(f"   密码验证: {'✅ 正确' if is_valid else '❌ 错误'}")
        
        # 检查哈希格式
        if hash_value.startswith('$2b$'):
            print("   哈希格式: ✅ bcrypt")
        else:
            print("   哈希格式: ❌ 未知格式")
            print("   需要重新生成密码哈希")
            
    except Exception as e:
        print(f"   密码验证失败: {e}")

if __name__ == "__main__":
    print("🔍 检查用户数据...")
    print("=" * 50)
    check_and_fix_user()
    print("=" * 50)
    print("✅ 检查完成")