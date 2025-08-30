from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.reflection import Inspector

def check_primary_keys():
    # 连接到数据库（假设使用SQLite）
    engine = create_engine('sqlite:///db.db')
    inspector = inspect(engine)
    
    # 检查article表
    print("检查article表的主键:")
    pk_columns = inspector.get_pk_constraint('articles')
    print(f"主键列: {pk_columns['constrained_columns']}")
    
    # 检查所有列定义
    print("\n所有列定义:")
    for column in inspector.get_columns('articles'):
        print(f"{column['name']}: {column['type']} {'(主键)' if column['primary_key'] else ''}")

if __name__ == '__main__':
    check_primary_keys()