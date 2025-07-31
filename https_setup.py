#!/usr/bin/env python3
"""
HTTPS配置脚本

此脚本提供了为FastAPI应用配置HTTPS的完整解决方案，包括：
1. 自签名证书生成（开发环境）
2. Let's Encrypt证书配置（生产环境）
3. 反向代理配置（Nginx）

使用方法：
1. 开发环境：python https_setup.py --dev
2. 生产环境：python https_setup.py --prod
3. 生成配置文件：python https_setup.py --config
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def generate_self_signed_cert():
    """生成自签名SSL证书（仅用于开发环境）"""
    print("🔐 生成自签名SSL证书...")
    
    cert_dir = Path("certs")
    cert_dir.mkdir(exist_ok=True)
    
    # 生成私钥
    subprocess.run([
        "openssl", "genrsa", "-out", "certs/server.key", "2048"
    ], check=True)
    
    # 生成证书签名请求
    subprocess.run([
        "openssl", "req", "-new", "-key", "certs/server.key", 
        "-out", "certs/server.csr", "-subj", 
        "/C=CN/ST=Beijing/L=Beijing/O=Dream/OU=IT/CN=localhost"
    ], check=True)
    
    # 生成自签名证书
    subprocess.run([
        "openssl", "x509", "-req", "-days", "365", 
        "-in", "certs/server.csr", "-signkey", "certs/server.key", 
        "-out", "certs/server.crt"
    ], check=True)
    
    print("✅ 自签名证书生成完成")
    print("📁 证书文件位置:")
    print(f"   私钥: {cert_dir}/server.key")
    print(f"   证书: {cert_dir}/server.crt")
    print("⚠️  注意：自签名证书仅用于开发环境，浏览器会显示安全警告")

def create_https_main():
    """创建支持HTTPS的main.py文件"""
    https_main_content = '''#!/usr/bin/env python3
"""
HTTPS版本的main.py
支持HTTP和HTTPS双协议启动
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import ssl
import os
from pathlib import Path

from database import engine, Base
from routers import user, points, generation, chat, payment
from config import settings

# 数据库初始化
def create_tables():
    """创建数据库表"""
    try:
        print("🚀 正在检查并创建数据库表...")
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表检查和创建完成")
    except Exception as e:
        print(f"❌ 数据库表操作失败: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建数据库表
    create_tables()
    yield
    # 关闭时的清理操作
    print("应用关闭")

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="用户管理后端API系统",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(user.router, prefix="/api/v1")
app.include_router(points.router, prefix="/api/v1")
app.include_router(generation.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(payment.router, prefix="/api/v1")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Dream Backend API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "API is running"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "服务器内部错误，请稍后重试"
        }
    )

def get_ssl_context():
    """获取SSL上下文"""
    cert_file = Path("certs/server.crt")
    key_file = Path("certs/server.key")
    
    if not cert_file.exists() or not key_file.exists():
        print("❌ SSL证书文件不存在，请先生成证书")
        print("💡 运行: python https_setup.py --dev")
        return None
    
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(cert_file, key_file)
    return ssl_context

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="启动Dream Backend API服务器")
    parser.add_argument("--https", action="store_true", help="启用HTTPS")
    parser.add_argument("--host", default="0.0.0.0", help="绑定主机地址")
    parser.add_argument("--port", type=int, default=8000, help="端口号")
    parser.add_argument("--reload", action="store_true", help="启用热重载")
    
    args = parser.parse_args()
    
    if args.https:
        ssl_context = get_ssl_context()
        if ssl_context:
            print(f"🔒 启动HTTPS服务器: https://{args.host}:{args.port}")
            uvicorn.run(
                "main_https:app",
                host=args.host,
                port=args.port,
                reload=args.reload,
                ssl_keyfile="certs/server.key",
                ssl_certfile="certs/server.crt",
                log_level="info"
            )
        else:
            sys.exit(1)
    else:
        print(f"🌐 启动HTTP服务器: http://{args.host}:{args.port}")
        uvicorn.run(
            "main_https:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )
'''
    
    with open("main_https.py", "w", encoding="utf-8") as f:
        f.write(https_main_content)
    
    print("✅ 创建HTTPS版本的main.py文件: main_https.py")

def create_nginx_config():
    """创建Nginx反向代理配置"""
    nginx_config = '''
# Nginx配置文件 - HTTPS反向代理
# 文件位置: /etc/nginx/sites-available/dream-backend

server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名
    
    # HTTP重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;  # 替换为你的域名
    
    # SSL证书配置
    ssl_certificate /path/to/your/certificate.crt;  # 替换为你的证书路径
    ssl_certificate_key /path/to/your/private.key;  # 替换为你的私钥路径
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # 反向代理到FastAPI应用
    location / {
        proxy_pass http://127.0.0.1:8000;  # FastAPI应用地址
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件缓存
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
'''
    
    with open("nginx-https.conf", "w", encoding="utf-8") as f:
        f.write(nginx_config)
    
    print("✅ 创建Nginx配置文件: nginx-https.conf")

def create_docker_compose():
    """创建Docker Compose配置（包含HTTPS支持）"""
    docker_compose = '''
version: '3.8'

services:
  dream-backend:
    build: .
    ports:
      - "8000:8000"  # HTTP
      - "8443:8443"  # HTTPS
    volumes:
      - ./certs:/app/certs:ro  # 挂载证书目录
    environment:
      - DATABASE_URL=mysql+pymysql://user:password@db:3306/dream_db
    depends_on:
      - db
    command: python main_https.py --https --port 8443
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-https.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - dream-backend
  
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: dream_db
      MYSQL_USER: user
      MYSQL_PASSWORD: password
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

volumes:
  mysql_data:
'''
    
    with open("docker-compose-https.yml", "w", encoding="utf-8") as f:
        f.write(docker_compose)
    
    print("✅ 创建Docker Compose配置: docker-compose-https.yml")

def create_lets_encrypt_script():
    """创建Let's Encrypt证书申请脚本"""
    script_content = '''
#!/bin/bash
# Let's Encrypt证书申请脚本

# 检查是否安装了certbot
if ! command -v certbot &> /dev/null; then
    echo "❌ certbot未安装，正在安装..."
    # Ubuntu/Debian
    sudo apt update
    sudo apt install certbot python3-certbot-nginx -y
    # CentOS/RHEL
    # sudo yum install certbot python3-certbot-nginx -y
fi

# 申请证书
echo "🔐 申请Let's Encrypt证书..."
echo "请确保："
echo "1. 域名已正确解析到此服务器"
echo "2. 80和443端口已开放"
echo "3. Nginx已正确配置"
read -p "确认继续？(y/N): " confirm

if [[ $confirm == [yY] ]]; then
    read -p "请输入域名: " domain
    read -p "请输入邮箱: " email
    
    # 申请证书
    sudo certbot --nginx -d $domain --email $email --agree-tos --non-interactive
    
    if [ $? -eq 0 ]; then
        echo "✅ 证书申请成功！"
        echo "📁 证书位置: /etc/letsencrypt/live/$domain/"
        echo "🔄 自动续期已配置"
        
        # 测试自动续期
        sudo certbot renew --dry-run
    else
        echo "❌ 证书申请失败，请检查配置"
    fi
else
    echo "操作已取消"
fi
'''
    
    with open("setup-letsencrypt.sh", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    # 设置执行权限
    os.chmod("setup-letsencrypt.sh", 0o755)
    
    print("✅ 创建Let's Encrypt脚本: setup-letsencrypt.sh")

def create_readme():
    """创建HTTPS配置说明文档"""
    readme_content = '''
# HTTPS配置指南

本项目支持多种HTTPS配置方式，适用于不同的部署环境。

## 🚀 快速开始

### 1. 开发环境（自签名证书）

```bash
# 生成自签名证书
python https_setup.py --dev

# 启动HTTPS服务器
python main_https.py --https
```

访问: https://localhost:8000

⚠️ **注意**: 浏览器会显示安全警告，这是正常的，点击"高级"→"继续访问"即可。

### 2. 生产环境（Let's Encrypt证书）

```bash
# 1. 配置Nginx
sudo cp nginx-https.conf /etc/nginx/sites-available/dream-backend
sudo ln -s /etc/nginx/sites-available/dream-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 2. 申请SSL证书
./setup-letsencrypt.sh

# 3. 启动应用
python main_https.py --port 8000
```

### 3. Docker部署

```bash
# 使用Docker Compose
docker-compose -f docker-compose-https.yml up -d
```

## 📋 配置选项

### 环境变量

```bash
# .env文件
HTTPS_ENABLED=true
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
HTTPS_PORT=8443
```

### 命令行参数

```bash
# 启动HTTPS服务器
python main_https.py --https --port 8443

# 启动HTTP服务器
python main_https.py --port 8000

# 启用热重载
python main_https.py --https --reload
```

## 🔧 高级配置

### 1. 自定义SSL配置

```python
# 在main_https.py中修改SSL配置
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
```

### 2. 反向代理配置

#### Nginx
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Apache
```apache
<VirtualHost *:443>
    ServerName your-domain.com
    
    SSLEngine on
    SSLCertificateFile /path/to/cert.pem
    SSLCertificateKeyFile /path/to/key.pem
    
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
    ProxyPreserveHost On
</VirtualHost>
```

### 3. 负载均衡

```nginx
upstream backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 443 ssl http2;
    
    location / {
        proxy_pass http://backend;
    }
}
```

## 🛡️ 安全最佳实践

1. **使用强密码套件**
2. **启用HSTS**
3. **定期更新证书**
4. **配置安全头**
5. **限制TLS版本**

## 🔍 故障排除

### 常见问题

1. **证书不受信任**
   - 开发环境：正常现象，可以忽略警告
   - 生产环境：检查证书链是否完整

2. **端口被占用**
   ```bash
   # 查看端口占用
   netstat -tlnp | grep :443
   
   # 杀死进程
   sudo kill -9 <PID>
   ```

3. **权限问题**
   ```bash
   # 设置证书文件权限
   sudo chmod 600 /path/to/private.key
   sudo chmod 644 /path/to/certificate.crt
   ```

4. **防火墙设置**
   ```bash
   # Ubuntu/Debian
   sudo ufw allow 443
   
   # CentOS/RHEL
   sudo firewall-cmd --permanent --add-port=443/tcp
   sudo firewall-cmd --reload
   ```

## 📚 相关文档

- [FastAPI HTTPS文档](https://fastapi.tiangolo.com/deployment/https/)
- [Let's Encrypt文档](https://letsencrypt.org/docs/)
- [Nginx SSL配置](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [uvicorn SSL配置](https://www.uvicorn.org/settings/#https)

## 🆘 获取帮助

如果遇到问题，请检查：
1. 证书文件是否存在且有效
2. 端口是否被占用
3. 防火墙设置是否正确
4. DNS解析是否正确（生产环境）
'''
    
    with open("HTTPS_README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ 创建HTTPS配置文档: HTTPS_README.md")

def main():
    parser = argparse.ArgumentParser(description="HTTPS配置工具")
    parser.add_argument("--dev", action="store_true", help="配置开发环境（生成自签名证书）")
    parser.add_argument("--prod", action="store_true", help="配置生产环境")
    parser.add_argument("--config", action="store_true", help="生成配置文件")
    parser.add_argument("--all", action="store_true", help="生成所有配置文件")
    
    args = parser.parse_args()
    
    if args.dev:
        print("🔧 配置开发环境HTTPS...")
        try:
            generate_self_signed_cert()
            create_https_main()
            print("\n✅ 开发环境配置完成！")
            print("\n🚀 启动命令:")
            print("   python main_https.py --https")
            print("\n🌐 访问地址:")
            print("   https://localhost:8000")
        except subprocess.CalledProcessError:
            print("❌ 证书生成失败，请确保已安装OpenSSL")
            print("💡 Windows用户可以安装Git for Windows或使用WSL")
    
    elif args.prod:
        print("🔧 配置生产环境HTTPS...")
        create_https_main()
        create_nginx_config()
        create_lets_encrypt_script()
        create_docker_compose()
        print("\n✅ 生产环境配置完成！")
        print("\n📋 下一步:")
        print("1. 配置域名DNS解析")
        print("2. 配置Nginx: sudo cp nginx-https.conf /etc/nginx/sites-available/")
        print("3. 申请SSL证书: ./setup-letsencrypt.sh")
        print("4. 启动应用: python main_https.py")
    
    elif args.config or args.all:
        print("📝 生成配置文件...")
        create_https_main()
        create_nginx_config()
        create_lets_encrypt_script()
        create_docker_compose()
        create_readme()
        print("\n✅ 所有配置文件生成完成！")
    
    else:
        parser.print_help()
        print("\n💡 使用示例:")
        print("   python https_setup.py --dev     # 开发环境")
        print("   python https_setup.py --prod    # 生产环境")
        print("   python https_setup.py --config  # 生成配置文件")

if __name__ == "__main__":
    main()