#!/usr/bin/env python3
"""
网络访问测试脚本
"""
import requests
import socket

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 创建一个UDP套接字
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "无法获取"

def test_access():
    """测试不同方式的访问"""
    port = 8001
    local_ip = get_local_ip()
    
    test_urls = [
        f"http://localhost:{port}",
        f"http://127.0.0.1:{port}",
        f"http://{local_ip}:{port}" if local_ip != "无法获取" else None
    ]
    
    print(f"本机IP地址: {local_ip}")
    print("=" * 50)
    
    for url in test_urls:
        if url is None:
            continue
            
        try:
            print(f"测试访问: {url}")
            response = requests.get(url, timeout=5)
            print(f"  状态码: {response.status_code}")
            print(f"  响应长度: {len(response.text)} 字符")
            if response.status_code == 500:
                print(f"  错误内容: {response.text[:200]}...")
            print("  ✅ 成功")
        except requests.exceptions.ConnectionError:
            print("  ❌ 连接失败")
        except requests.exceptions.Timeout:
            print("  ❌ 超时")
        except Exception as e:
            print(f"  ❌ 错误: {e}")
        print()

def check_port_binding():
    """检查端口绑定"""
    import subprocess
    try:
        result = subprocess.run(['ss', '-tulpn'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if '8001' in line:
                print(f"端口绑定: {line.strip()}")
    except Exception as e:
        print(f"检查端口绑定失败: {e}")

if __name__ == "__main__":
    print("🔍 WeRSS 网络访问测试")
    print("=" * 50)
    
    check_port_binding()
    print()
    
    test_access()
    
    print("🔧 如果遇到问题，请检查:")
    print("1. 防火墙设置 (ufw, firewalld)")
    print("2. 应用是否正在运行")
    print("3. 端口是否被其他程序占用")
    print(f"4. 局域网访问: http://{get_local_ip()}:8001")