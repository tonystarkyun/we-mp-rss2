#!/usr/bin/env python3
"""
最终版数据库重置脚本
"""
import os
import sqlite3
import shutil
from datetime import datetime
import bcrypt

def reset_database():
    """完全重置数据库"""
    db_path = "dist/data/db.db" if os.path.exists("dist/data/db.db") else "data/db.db"
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False
    
    # 备份原数据库
    backup_path = f"{os.path.dirname(db_path)}/db_reset_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(db_path, backup_path)
    print(f"✅ 原数据库已备份到: {backup_path}")
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📋 找到 {len(tables)} 个数据表")
        
        # 清空所有表的数据（保留表结构）
        total_deleted = 0
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            if count > 0:
                cursor.execute(f"DELETE FROM {table_name}")
                total_deleted += count
                print(f"🧹 清空表 {table_name}: 删除了 {count} 条记录")
        
        print(f"✅ 数据清理完成！总共删除了 {total_deleted} 条记录")
        
        # 尝试重置自增ID（如果存在）
        try:
            cursor.execute("SELECT COUNT(*) FROM sqlite_sequence")
            cursor.execute("DELETE FROM sqlite_sequence")
            print("🔄 重置自增ID序列")
        except sqlite3.OperationalError:
            print("ℹ️ 无sqlite_sequence表，跳过重置")
        
        # 创建默认管理员
        create_default_admin(cursor)
        
        # 提交更改
        conn.commit()
        
        # 优化数据库
        cursor.execute("VACUUM")
        print("🔧 数据库已优化")
        
        # 检查最终状态
        print("\n📊 重置后的数据库状态:")
        non_empty_tables = 0
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"   - {table_name}: {count} 条记录")
                non_empty_tables += 1
        
        if non_empty_tables == 0:
            print("   - 所有表都是空的（除了新创建的管理员）")
        
        return True
        
    except Exception as e:
        print(f"❌ 重置过程中出错: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def create_default_admin(cursor):
    """创建默认管理员"""
    try:
        username = "zkzc"
        password = "wf2151328"
        
        # 使用bcrypt生成密码哈希
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        # 检查users表是否存在必要字段
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # 构建INSERT语句（只使用存在的字段）
        base_fields = {
            'id': 0,
            'username': username,
            'password_hash': password_hash,
            'role': 'admin',
            'is_active': 1
        }
        
        # 添加可选字段
        if 'nickname' in columns:
            base_fields['nickname'] = '默认管理员'
        
        fields = list(base_fields.keys())
        values = list(base_fields.values())
        placeholders = ','.join(['?' for _ in values])
        
        cursor.execute(f"""
            INSERT INTO users ({','.join(fields)}) 
            VALUES ({placeholders})
        """, values)
        
        print(f"👤 创建默认管理员:")
        print(f"   用户名: {username}")
        print(f"   密码: {password}")
        print(f"   角色: admin")
        
        # 验证密码
        is_valid = bcrypt.checkpw(password_bytes, password_hash.encode('utf-8'))
        print(f"   验证: {'✅ 正确' if is_valid else '❌ 错误'}")
        
    except Exception as e:
        print(f"❌ 创建管理员失败: {e}")
        raise

if __name__ == "__main__":
    print("🚨 最终版数据库重置")
    print("⚠️  删除所有数据，只保留默认管理员！")
    print("=" * 60)
    
    print("🚀 开始重置...")
    
    # 重置数据库
    if reset_database():
        print("=" * 60)
        print("🎉 数据库重置完成！")
        print("")
        print("✅ 现在数据库完全干净，只包含:")
        print("   - 默认管理员: zkzc / wf2151328")
        print("   - 空的数据表（保留结构）")
        print("")
        print("🚀 启动命令:")
        print("   cd dist && ./we-rss-linux")
    else:
        print("❌ 重置失败")