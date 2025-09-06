#!/usr/bin/env python3
"""
修复管理员账号
"""
import os
import sqlite3
import hashlib

def fix_admin():
    """修复管理员账号"""
    db_path = "dist/data/db.db"
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查现有管理员
        cursor.execute("SELECT id, username, password_hash FROM users WHERE id = '0'")
        admin = cursor.fetchone()
        
        if admin:
            print(f"📋 找到现有管理员: ID={admin[0]}, 用户名={admin[1]}")
            
            # 使用简单的密码哈希（用于测试）
            import hashlib
            password = "wf2151328"
            # 使用MD5作为临时解决方案（生产环境不推荐）
            password_hash = hashlib.md5(password.encode()).hexdigest()
            
            # 更新管理员账号
            cursor.execute("""
                UPDATE users 
                SET username = ?, password_hash = ?, role = ?, is_active = 1
                WHERE id = '0'
            """, ("zkzc", password_hash, "admin"))
            
            print("✅ 管理员账号已更新:")
            print(f"   用户名: zkzc")
            print(f"   密码: {password}")
            print(f"   哈希: {password_hash}")
            
        else:
            print("❌ 没有找到ID为0的管理员")
            # 创建新管理员
            password = "wf2151328"
            password_hash = hashlib.md5(password.encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO users (id, username, password_hash, role, is_active) 
                VALUES ('0', 'zkzc', ?, 'admin', 1)
            """, (password_hash,))
            
            print("✅ 新管理员已创建")
        
        conn.commit()
        
        # 验证修改
        cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = 'zkzc'")
        updated_admin = cursor.fetchone()
        if updated_admin:
            print(f"\n✅ 验证成功: {updated_admin}")
        else:
            print("\n❌ 验证失败")
            
    except Exception as e:
        print(f"❌ 修复过程中出错: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 修复管理员账号...")
    print("=" * 50)
    fix_admin()
    print("=" * 50)
    print("🎉 修复完成！请重启应用并使用 zkzc/wf2151328 登录")