#!/usr/bin/env python3
"""
使用bcrypt修复管理员账号
"""
import os
import sqlite3
import bcrypt

def fix_admin_bcrypt():
    """使用bcrypt修复管理员账号"""
    db_path = "dist/data/db.db"
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查现有管理员
        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = 'zkzc'")
        admin = cursor.fetchone()
        
        if admin:
            print(f"📋 找到管理员: ID={admin[0]}, 用户名={admin[1]}")
            print(f"当前哈希: {admin[2]}")
            
            # 使用bcrypt生成正确的密码哈希
            password = "wf2151328"
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
            
            # 更新管理员密码哈希
            cursor.execute("""
                UPDATE users 
                SET password_hash = ?
                WHERE username = 'zkzc'
            """, (password_hash,))
            
            print("✅ 管理员密码哈希已更新:")
            print(f"   用户名: zkzc")
            print(f"   密码: {password}")
            print(f"   新哈希: {password_hash}")
            
            # 验证bcrypt哈希
            is_valid = bcrypt.checkpw(password_bytes, password_hash.encode('utf-8'))
            print(f"   验证: {'✅ 正确' if is_valid else '❌ 错误'}")
            
        else:
            print("❌ 没有找到zkzc用户")
        
        conn.commit()
        
        # 最终验证
        cursor.execute("SELECT username, password_hash FROM users WHERE username = 'zkzc'")
        updated_admin = cursor.fetchone()
        if updated_admin:
            print(f"\n✅ 数据库验证成功: 用户名={updated_admin[0]}")
            print(f"   哈希长度: {len(updated_admin[1])} (bcrypt哈希通常60字符)")
        else:
            print("\n❌ 数据库验证失败")
            
    except Exception as e:
        print(f"❌ 修复过程中出错: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 使用bcrypt修复管理员账号...")
    print("=" * 50)
    fix_admin_bcrypt()
    print("=" * 50)
    print("🎉 修复完成！请重启应用并使用 zkzc/wf2151328 登录")