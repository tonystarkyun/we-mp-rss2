# Geckodriver 手动安装指南

## Windows 系统安装步骤

1. 访问 geckodriver 发布页面:
   https://github.com/mozilla/geckodriver/releases

2. 下载对应版本:
   - 32位系统: geckodriver-vX.XX-win32.zip
   - 64位系统: geckodriver-vX.XX-win64.zip

3. 解压下载的zip文件:
   - 将解压后的 geckodriver.exe 文件复制到:
     `c:\Users\Administrator\Desktop\Wx\we-mp-rss\driver\`

4. 验证安装:
   - 打开命令提示符
   - 执行: `driver\geckodriver.exe --version`
   - 应该显示版本号

## Linux 系统安装步骤

1. 终端执行以下命令下载:
```bash
wget https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz
```

2. 解压并安装:
```bash
tar -xvzf geckodriver-*
chmod +x geckodriver
sudo mv geckodriver /usr/local/bin/
```

3. 验证安装:
```bash
geckodriver --version
```

## 安装后测试

1. 确保已安装Python和selenium:
```bash
pip install selenium
```

2. 运行测试脚本:
```bash
python driver/web.py
```

## 常见问题解决

Q: 下载速度慢怎么办？
A: 可以使用国内镜像源替换下载URL中的域名:
   - 将 github.com 替换为 hub.fastgit.org
   - 或使用 ghproxy.com 代理

Q: 权限不足错误？
A: Linux系统请使用sudo执行安装命令