# HTTPS配置使用指南

本指南说明如何为Dream Backend API配置HTTPS支持。

## 🚀 快速配置

### 方式一：命令行参数（推荐）

```bash
# 启动HTTPS服务器，指定证书路径
python main.py --https --ssl-cert /path/to/your/certificate.pem --ssl-key /path/to/your/private-key.pem

# 指定端口
python main.py --https --port 8443 --ssl-cert /path/to/cert.pem --ssl-key /path/to/key.pem
```

### 方式二：环境变量

1. **设置环境变量**
   ```bash
   # Windows
   set SSL_CERT_PATH=C:\path\to\your\certificate.pem
   set SSL_KEY_PATH=C:\path\to\your\private-key.pem
   
   # Linux/Mac
   export SSL_CERT_PATH=/path/to/your/certificate.pem
   export SSL_KEY_PATH=/path/to/your/private-key.pem
   ```

2. **启动服务器**
   ```bash
   python main.py --https
   ```

### 方式三：配置文件

1. **复制配置文件**
   ```bash
   cp .env.example .env
   ```

2. **编辑 .env 文件**
   ```bash
   SSL_CERT_PATH=/path/to/your/certificate.pem
   SSL_KEY_PATH=/path/to/your/private-key.pem
   ```

3. **启动服务器**
   ```bash
   python main.py --https
   ```

### 方式四：默认路径

将证书文件放在默认位置：
- `certs/server.crt` - SSL证书文件
- `certs/server.key` - SSL私钥文件

```bash
# 创建证书目录
mkdir certs

# 将你的证书文件复制到默认位置
copy your-certificate.pem certs/server.crt
copy your-private-key.pem certs/server.key

# 启动HTTPS服务器
python main.py --https
```

## 📋 命令行选项

```bash
# 基本HTTPS启动
python main.py --https

# 指定端口
python main.py --https --port 8443

# 指定绑定地址
python main.py --https --host 0.0.0.0 --port 8443

# 启用热重载（开发时使用）
python main.py --https --reload

# 指定证书文件
python main.py --https --ssl-cert /path/to/cert.pem --ssl-key /path/to/key.pem

# 启动HTTP服务器（默认）
python main.py --port 8000
```

## 🔧 证书获取方式

### 1. 自签名证书（开发环境）

```bash
# 生成私钥
openssl genrsa -out certs/server.key 2048

# 生成证书签名请求
openssl req -new -key certs/server.key -out certs/server.csr

# 生成自签名证书
openssl x509 -req -days 365 -in certs/server.csr -signkey certs/server.key -out certs/server.crt
```

### 2. Let's Encrypt证书（免费）

```bash
# 安装certbot
sudo apt install certbot  # Ubuntu/Debian
# 或
brew install certbot      # macOS

# 申请证书
sudo certbot certonly --standalone -d your-domain.com

# 证书位置
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

### 3. 商业证书

从证书颁发机构（如阿里云、腾讯云等）购买SSL证书，下载后使用。

## 🛡️ 客户端配置

### JavaScript/前端

```javascript
// 生产环境
const api = axios.create({
  baseURL: 'https://your-domain.com:8443/api/v1'
});

// 开发环境（自签名证书）
const api = axios.create({
  baseURL: 'https://localhost:8443/api/v1',
  // 注意：生产环境不要使用 rejectUnauthorized: false
});
```

### Python客户端

```python
import requests

# 生产环境
response = requests.post(
    'https://your-domain.com:8443/api/v1/users/register',
    json=user_data
)

# 开发环境（自签名证书）
response = requests.post(
    'https://localhost:8443/api/v1/users/register',
    json=user_data,
    verify=False  # 仅开发环境使用
)
```

## 🔍 故障排除

### 常见错误

1. **证书文件不存在**
   ```
   ❌ SSL证书文件不存在
   📁 证书路径: /path/to/cert.pem
   🔑 私钥路径: /path/to/key.pem
   ```
   **解决方案**：确保证书文件存在于指定路径

2. **权限问题**
   ```bash
   # 设置正确的文件权限
   chmod 600 /path/to/private-key.pem
   chmod 644 /path/to/certificate.pem
   ```

3. **端口被占用**
   ```bash
   # 检查端口占用
   netstat -tlnp | grep :8443
   
   # 使用其他端口
   python main.py --https --port 9443
   ```

4. **防火墙问题**
   ```bash
   # 开放HTTPS端口
   sudo ufw allow 8443
   ```

### 测试HTTPS连接

```bash
# 测试HTTPS连接
curl -k https://localhost:8443/health

# 检查证书信息
openssl x509 -in /path/to/certificate.pem -text -noout

# 测试SSL握手
openssl s_client -connect localhost:8443 -servername localhost
```

## 📝 配置优先级

程序按以下优先级查找SSL证书：

1. **命令行参数** `--ssl-cert` 和 `--ssl-key`
2. **环境变量** `SSL_CERT_PATH` 和 `SSL_KEY_PATH`
3. **默认路径** `certs/server.crt` 和 `certs/server.key`

## 🚀 部署建议

### 开发环境
- 使用自签名证书
- 放在默认路径 `certs/` 目录
- 启用热重载：`python main.py --https --reload`

### 生产环境
- 使用Let's Encrypt或商业证书
- 通过环境变量配置证书路径
- 使用反向代理（Nginx/Apache）
- 配置自动证书更新

### 示例部署脚本

```bash
#!/bin/bash
# 生产环境启动脚本

# 设置证书路径
export SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
export SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem

# 启动HTTPS服务器
python main.py --https --host 0.0.0.0 --port 8443
```

这样配置后，你只需要将证书文件放在指定位置，或通过命令行参数/环境变量指定证书路径即可启用HTTPS。