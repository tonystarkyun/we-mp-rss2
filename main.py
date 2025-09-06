import uvicorn
from core.config import cfg
from core.print import print_warning
import threading
import os

def main():
    """主启动函数，可被外部调用"""
    db_path = cfg.get("db", "data/db.db")
    # 只有数据库不存在时才初始化，或者明确指定强制初始化
    # 处理重置数据库参数
    if cfg.args.reset == "True":
        print("🚨 正在完全重置数据库...")
        from reset_database_final import reset_database, clean_files
        if reset_database():
            print("✅ 数据库重置完成")
        else:
            print("❌ 数据库重置失败")
            exit(1)
    
    if cfg.args.init=="True" and not os.path.exists(db_path):
        import init_sys as init
        init.init()
    elif cfg.args.init=="force":
        import init_sys as init
        init.init()
    if  cfg.args.job =="True" and cfg.get("server.enable_job",False):
        from jobs import start_all_task
        threading.Thread(target=start_all_task,daemon=True).start()
    else:
        print_warning("未开启定时任务")
    print("启动服务器")
    
    # 支持环境变量设置端口（用于独立版本）
    port = int(os.environ.get('PORT', cfg.get("port", 8001)))
    AutoReload = cfg.get("server.auto_reload", False)
    
    uvicorn.run("web:app", 
                host="0.0.0.0", 
                port=port, 
                reload=AutoReload,
                reload_excludes=['static','web_ui','data'])

if __name__ == '__main__':
    main()