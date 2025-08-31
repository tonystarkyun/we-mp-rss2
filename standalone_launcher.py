#!/usr/bin/env python3
"""
WeRSS 单用户版启动器
负责启动服务并自动打开浏览器
"""

import os
import sys
import time
import threading
import webbrowser
import subprocess
from pathlib import Path
import signal
import atexit

# 添加当前目录到Python路径
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

def resource_path(relative_path):
    """获取资源文件的绝对路径，支持PyInstaller打包"""
    try:
        # PyInstaller创建的临时文件夹路径
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境路径
        base_path = Path(__file__).parent.absolute()
    
    return os.path.join(base_path, relative_path)

def setup_environment():
    """设置运行环境"""
    # 设置工作目录到AppData，确保数据持久化
    work_dir = Path(os.environ.get('APPDATA', Path.home())) / "WeRSS"
    work_dir.mkdir(exist_ok=True)
    os.chdir(work_dir)
    
    # 创建必要的目录
    (work_dir / "data").mkdir(exist_ok=True)
    (work_dir / "static").mkdir(exist_ok=True)
    (work_dir / "logs").mkdir(exist_ok=True)
    
    # 复制配置文件（如果不存在）
    config_file = work_dir / "config.yaml"
    if not config_file.exists():
        try:
            example_config = resource_path("config.example.yaml")
            if os.path.exists(example_config):
                import shutil
                shutil.copy2(example_config, config_file)
                print(f"已创建配置文件: {config_file}")
        except Exception as e:
            print(f"配置文件复制失败: {e}")
    
    # 复制静态文件
    try:
        static_src = resource_path("static")
        static_dst = work_dir / "static"
        if os.path.exists(static_src) and not (static_dst / "index.html").exists():
            import shutil
            shutil.copytree(static_src, static_dst, dirs_exist_ok=True)
            print("已复制静态文件")
    except Exception as e:
        print(f"静态文件复制失败: {e}")
    
    return work_dir

def check_port_available(port=8001):
    """检查端口是否可用"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False

def find_available_port(start_port=8001):
    """查找可用端口"""
    for port in range(start_port, start_port + 100):
        if check_port_available(port):
            return port
    raise RuntimeError("无法找到可用端口")

def wait_for_server(port, timeout=30):
    """等待服务器启动"""
    import requests
    urls = [f"http://localhost:{port}", f"http://127.0.0.1:{port}", f"http://0.0.0.0:{port}"]
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        for url in urls:
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    print(f"服务器已启动，可访问地址: {url}")
                    return True
            except requests.exceptions.RequestException:
                continue
        time.sleep(2)
    
    # 如果HTTP检测失败，尝试简单的端口连接检测
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        if result == 0:
            print(f"端口 {port} 可连接，假定服务已启动")
            return True
    except:
        pass
        
    return False

def open_browser(port):
    """打开浏览器"""
    url = f"http://localhost:{port}"
    print(f"正在打开浏览器: {url}")
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"无法打开浏览器: {e}")
        print(f"请手动在浏览器中打开: {url}")
        return False

def create_desktop_shortcut(work_dir):
    """创建桌面快捷方式（Windows）"""
    try:
        if os.name == 'nt':  # Windows
            import winshell
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "WeRSS.lnk")
            
            with winshell.shortcut(shortcut_path) as shortcut:
                shortcut.path = sys.executable
                shortcut.description = "WeRSS - RSS订阅管理系统"
                shortcut.working_directory = str(work_dir)
            
            print(f"已创建桌面快捷方式: {shortcut_path}")
    except Exception as e:
        print(f"创建快捷方式失败: {e}")

def cleanup_handler(signum=None, frame=None):
    """清理处理器"""
    print("\n正在关闭WeRSS...")
    sys.exit(0)

def main():
    """主函数"""
    # 修复Windows控制台编码问题
    if os.name == 'nt':  # Windows
        try:
            # 设置控制台编码
            os.system('chcp 65001 >nul 2>&1')
            
            # 尝试设置UTF-8编码输出
            import sys
            import codecs
            if sys.stdout is not None and hasattr(sys.stdout, 'detach'):
                try:
                    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
                except (AttributeError, OSError):
                    pass  # 如果失败就使用默认编码
            
            if sys.stderr is not None and hasattr(sys.stderr, 'detach'):
                try:
                    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
                except (AttributeError, OSError):
                    pass  # 如果失败就使用默认编码
        except Exception:
            # 如果编码设置失败，继续使用默认编码
            pass
    
    print("=" * 60)
    print("    欢迎使用商业雷达订阅助手")
    print("    服务加载中，请稍后...")
    print("=" * 60)
    
    try:
        # 设置信号处理
        signal.signal(signal.SIGINT, cleanup_handler)
        signal.signal(signal.SIGTERM, cleanup_handler)
        atexit.register(lambda: print("WeRSS已关闭"))
        
        # 设置环境
        print("正在初始化环境...")
        work_dir = setup_environment()
        
        # 查找可用端口
        print("正在查找可用端口...")
        port = find_available_port()
        print(f"使用端口: {port}")
        
        # 设置环境变量
        os.environ['PORT'] = str(port)
        
        # 启动主服务
        print("正在启动WeRSS服务...")
        
        # 启动服务
        def start_server():
            try:
                print("正在初始化应用服务...")
                print("加载应用模块...")
                print("配置运行环境...")
                
                # 确保当前目录是包含web.py的目录
                original_cwd = os.getcwd()
                
                # 保持在用户数据目录，不要切换回项目目录
                # 如果是PyInstaller打包的环境，添加必要的路径但不切换工作目录
                if hasattr(sys, '_MEIPASS'):
                    # 在打包环境中，需要将临时目录添加到路径
                    if sys._MEIPASS not in sys.path:
                        sys.path.insert(0, sys._MEIPASS)
                # 在开发环境中，添加项目目录到路径但保持当前工作目录
                
                # 添加项目目录到路径（用于导入模块）
                if str(current_dir) not in sys.path:
                    sys.path.insert(0, str(current_dir))
                
                # 设置环境变量和参数
                os.environ['PORT'] = str(port)
                
                # 确保配置文件在正确的位置
                config_file = work_dir / "config.yaml"
                if not config_file.exists():
                    # 从资源目录复制配置文件
                    example_config = resource_path("config.example.yaml")
                    if os.path.exists(example_config):
                        import shutil
                        shutil.copy2(example_config, config_file)
                
                # 检查是否需要初始化数据库
                db_file = work_dir / "data" / "db.db"
                init_flag_file = work_dir / "initialized.flag"
                # 只有数据库不存在且没有初始化标记文件时才初始化
                need_init = not db_file.exists() and not init_flag_file.exists()
                
                print("检查系统初始化状态...")
                # 设置命令行参数，指定配置文件路径
                if need_init:
                    print("首次启动，正在初始化数据库...")
                    print("创建数据表结构...")
                    sys.argv = ['main.py', '-job', 'True', '-init', 'True', '-config', str(config_file)]
                else:
                    print("系统已初始化，跳过数据库初始化...")
                    sys.argv = ['main.py', '-job', 'True', '-init', 'False', '-config', str(config_file)]
                
                # 导入并运行主程序
                try:
                    print("导入应用核心模块...")
                    from main import main as start_main
                    print("启动Web服务器...")
                    start_main()
                except ImportError as e:
                    print(f"导入main模块失败: {e}")
                    import traceback
                    traceback.print_exc()
                except Exception as e:
                    print(f"主服务启动异常: {e}")
                    import traceback
                    traceback.print_exc()
                
            except Exception as e:
                print(f"服务启动失败: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # 恢复原工作目录
                if 'original_cwd' in locals():
                    os.chdir(original_cwd)
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # 等待服务启动
        print("正在等待服务启动...")
        if wait_for_server(port):
            print("✅ WeRSS服务启动成功!")
            
            # 检查是否需要创建初始化标记文件
            db_file = work_dir / "data" / "db.db"
            init_flag_file = work_dir / "initialized.flag"
            
            # 如果标记文件不存在，且数据库存在，验证数据库表并创建标记文件
            if not init_flag_file.exists():
                try:
                    # 检查关键表是否存在
                    import sqlite3
                    db_path = work_dir / "data" / "db.db"
                    if db_path.exists():
                        conn = sqlite3.connect(str(db_path))
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
                        if cursor.fetchone():
                            init_flag_file.touch()
                            print(f"数据库初始化成功，已创建标记文件: {init_flag_file}")
                        else:
                            print("⚠️  数据库表未正确创建，不创建标记文件")
                        conn.close()
                    else:
                        print("⚠️  数据库文件未创建，不创建标记文件")
                except Exception as e:
                    print(f"验证数据库初始化状态失败: {e}")
            
            # 打开浏览器
            print("正在加载应用页面请稍后...")
            threading.Timer(2.0, lambda: open_browser(port)).start()
            
            # 创建桌面快捷方式
            create_desktop_shortcut(work_dir)
            
            print(f"""
🎉 WeRSS已成功启动！

📋 访问信息:
   - 本地地址: http://localhost:{port}
   - 数据目录: {work_dir}
   
👤 默认账户:
   - 用户名: Administrator  
   - 密码: admin@123

💡 使用说明:
   - 浏览器会自动打开WebUI界面
   - 可以通过系统托盘图标控制程序
   - 数据保存在用户目录下的WeRSS文件夹

按 Ctrl+C 退出程序
""")
            
            # 保持程序运行
            try:
                print("程序正在运行中，按 Ctrl+C 退出...")
                print("-" * 50)
                
                last_status_time = 0
                while True:
                    current_time = time.time()
                    
                    # 每10秒显示一次状态信息
                    if current_time - last_status_time >= 10:
                        status_time = time.strftime("%H:%M:%S")
                        print(f"[{status_time}] 服务运行正常 - http://localhost:{port}")
                        last_status_time = current_time
                    
                    time.sleep(1)
                    
                    # 检查服务器线程是否还活着
                    if not server_thread.is_alive():
                        print("⚠️  服务器线程已停止")
                        break
            except KeyboardInterrupt:
                print("\n收到退出信号，正在关闭服务...")
            except Exception as e:
                print(f"\n运行时错误: {e}")
                import traceback
                traceback.print_exc()
                print("程序将在5秒后退出...")
                time.sleep(5)
                
        else:
            print("❌ 服务启动失败，请检查错误信息")
            print(f"尝试手动访问: http://localhost:{port}")
            print("程序将在5秒后自动退出，或按回车键立即退出...")
            
            # 给用户5秒时间查看错误
            import select
            import sys
            
            if os.name == 'nt':  # Windows
                try:
                    import msvcrt
                    start_time = time.time()
                    while time.time() - start_time < 5:
                        if msvcrt.kbhit():
                            msvcrt.getch()
                            break
                        time.sleep(0.1)
                except:
                    input("按回车键退出...")
            else:
                input("按回车键退出...")
            sys.exit(1)
            
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        print("详细错误信息:")
        traceback.print_exc()
        print("\n程序将在10秒后自动退出，或按回车键立即退出...")
        
        # 给用户时间查看错误
        if os.name == 'nt':  # Windows
            try:
                import msvcrt
                start_time = time.time()
                while time.time() - start_time < 10:
                    if msvcrt.kbhit():
                        msvcrt.getch()
                        break
                    time.sleep(0.1)
            except:
                input("按回车键退出...")
        else:
            input("按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()