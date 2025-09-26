#!/usr/bin/env python3
"""
数据库清理脚本 - 为分发准备干净的数据库
"""
import os
import sqlite3
import shutil
from datetime import datetime

def clean_database():
    """清理数据库，保留表结构但删除用户数据"""
    db_path = "dist/data/db.db"
    backup_path = f"dist/data/db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    # 备份原数据库
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        print(f"✅ 原数据库已备份到: {backup_path}")
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📋 发现 {len(tables)} 个数据表:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # 需要清理数据的表（保留结构，删除数据）
        tables_to_clean = [
            'articles',          # 文章数据
            'feeds',            # RSS源数据
            'message_tasks',    # 消息任务
            'links',            # 链接数据
            'link_articles',    # 链接文章关联
            'patent_articles',  # 专利文章关联
            'industry_articles' # 行业文章关联
        ]
        
        # 需要完全清理的表（删除数据，保留一个默认管理员）
        users_table = 'users'
        
        # 清理数据表
        cleaned_count = 0
        for table_name in tables_to_clean:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            if count > 0:
                cursor.execute(f"DELETE FROM {table_name}")
                print(f"🧹 清理表 {table_name}: 删除了 {count} 条记录")
                cleaned_count += count
            else:
                print(f"✨ 表 {table_name}: 已经是空的")
        
        # 清理用户表但保留默认管理员
        cursor.execute(f"SELECT COUNT(*) FROM {users_table}")
        user_count = cursor.fetchone()[0]
        if user_count > 1:
            # 删除除了id=0的管理员外的所有用户
            cursor.execute(f"DELETE FROM {users_table} WHERE id != 0")
            cursor.execute(f"SELECT COUNT(*) FROM {users_table}")
            remaining_users = cursor.fetchone()[0]
            deleted_users = user_count - remaining_users
            print(f"👥 清理用户表: 删除了 {deleted_users} 个用户，保留 {remaining_users} 个管理员")
        else:
            print(f"👥 用户表: 只有 {user_count} 个用户，保持不变")
        
        # 清理缓存目录
        cache_dir = "dist/data/cache"
        if os.path.exists(cache_dir):
            cache_files = []
            for root, dirs, files in os.walk(cache_dir):
                for file in files:
                    if file not in ['.gitkeep', 'README.md']:
                        cache_files.append(os.path.join(root, file))
            
            if cache_files:
                for cache_file in cache_files:
                    try:
                        os.remove(cache_file)
                    except:
                        pass
                print(f"🗑️  清理缓存文件: 删除了 {len(cache_files)} 个缓存文件")
            else:
                print(f"📁 缓存目录: 已经是干净的")
        
        # 提交更改
        conn.commit()
        print(f"✅ 数据库清理完成！总共清理了 {cleaned_count} 条记录")
        
        # 优化数据库
        cursor.execute("VACUUM")
        print("🔧 数据库已优化")
        
        # 检查最终状态
        print("\n📊 清理后的数据库状态:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   - {table_name}: {count} 条记录")
        
    except Exception as e:
        print(f"❌ 清理过程中出错: {e}")
        conn.rollback()
    finally:
        conn.close()

def clean_files():
    """清理用户上传的文件"""
    files_dir = "dist/data/files"
    if os.path.exists(files_dir):
        cleaned_files = 0
        for root, dirs, files in os.walk(files_dir):
            for file in files:
                if file not in ['.gitkeep', 'default-avatar.png']:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        cleaned_files += 1
                    except:
                        pass
        
        if cleaned_files > 0:
            print(f"📄 清理用户文件: 删除了 {cleaned_files} 个文件")
        else:
            print(f"📁 用户文件目录: 已经是干净的")

if __name__ == "__main__":
    print("🚀 开始清理数据库，准备分发版本...")
    print("=" * 50)
    
    if not os.path.exists("dist/data/db.db"):
        print("❌ 未找到数据库文件: dist/data/db.db")
        exit(1)
    
    # 清理数据库
    clean_database()
    
    # 清理文件
    clean_files()
    
    print("=" * 50)
    print("🎉 清理完成！现在可以安全分发 dist 目录了")
    print("")
    print("分发版本包含:")
    print("✅ 干净的数据库（只有表结构和默认管理员）")
    print("✅ 完整的应用程序和浏览器")
    print("✅ 默认管理员账号: zkzc / wf2151328")
    print("")
    print("建议:")
    print("1. 测试分发版本是否正常工作")
    print("2. 打包: tar -czf we-rss-linux-clean.tar.gz dist/")
    print("3. 原数据库已自动备份到 dist/data/ 目录")