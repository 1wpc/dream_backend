# 邮箱验证功能使用指南

## 功能概述

本系统新增了邮箱验证功能，用户注册时需要通过邮箱验证码验证。系统使用腾讯云SES发送邮件，Redis缓存验证码，验证码有效期为5分钟。

## 功能特性

- ✅ 邮箱验证码发送（腾讯云SES）
- ✅ 验证码缓存（Redis，5分钟有效期）
- ✅ 频率限制（1分钟内只能发送一次）
- ✅ 验证码验证
- ✅ 带验证码的用户注册
- ✅ 向后兼容（保留原有注册接口）

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

新增的依赖包：
- `redis==5.0.1` - Redis客户端
- `tencentcloud-sdk-python==3.0.1125` - 腾讯云SDK

### 2. Redis配置

确保Redis服务正在运行：

```bash
# 安装Redis（Windows）
# 下载并安装Redis for Windows

# 启动Redis服务
redis-server

# 测试Redis连接
redis-cli ping
```

### 3. 环境变量配置

在 `.env` 文件中添加以下配置：

```env
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # 如果有密码则填写
REDIS_DB=0

# 邮箱验证配置
EMAIL_VERIFICATION_EXPIRE_MINUTES=5
TENCENTCLOUD_SECRET_ID=your_secret_id_here
TENCENTCLOUD_SECRET_KEY=your_secret_key_here
TENCENTCLOUD_SES_REGION=ap-hongkong
TENCENTCLOUD_SES_FROM_EMAIL=mijiutech@bot.mijiu.ltd
TENCENTCLOUD_SES_TEMPLATE_ID=144111
```

### 4. 腾讯云SES配置

1. 登录腾讯云控制台
2. 开通邮件推送服务（SES）
3. 配置发送域名和邮箱地址
4. 创建邮件模板（模板ID: 144111）
5. 获取API密钥（SecretId和SecretKey）

## API接口说明

### 1. 发送验证码

**接口**: `POST /api/v1/users/send-verification-code`

**请求体**:
```json
{
  "email": "user@example.com",
  "action": "注册"
}
```

**响应**:
```json
{
  "success": true,
  "message": "验证码已发送到 user@example.com，请在5分钟内使用",
  "code": "SUCCESS"
}
```

**错误响应**:
- `429 Too Many Requests`: 发送过于频繁
- `500 Internal Server Error`: 邮件发送失败

### 2. 验证验证码

**接口**: `POST /api/v1/users/verify-email-code`

**请求体**:
```json
{
  "email": "user@example.com",
  "code": "123456",
  "action": "register"
}
```

**响应**:
```json
{
  "success": true,
  "message": "验证码验证成功",
  "code": "SUCCESS"
}
```

**错误响应**:
- `400 Bad Request`: 验证码错误或已过期

### 3. 带验证码注册

**接口**: `POST /api/v1/users/register-with-verification`

**请求体**:
```json
{
  "username": "testuser",
  "email": "user@example.com",
  "password": "password123",
  "full_name": "测试用户",
  "verification_code": "123456"
}
```

**响应**:
```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "user@example.com",
    "full_name": "测试用户",
    "is_active": true,
    "points_balance": "0.00",
    "created_at": "2025-01-17T10:00:00"
  },
  "message": "用户注册成功，邮箱验证通过"
}
```

### 4. 传统注册（向后兼容）

**接口**: `POST /api/v1/users/register`

原有的注册接口保持不变，无需验证码即可注册。

## 使用流程

### 前端集成示例

```javascript
// 1. 发送验证码
async function sendVerificationCode(email) {
  const response = await fetch('/api/v1/users/send-verification-code', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      action: '注册'
    })
  });
  
  const result = await response.json();
  if (response.ok) {
    alert(result.message);
  } else {
    alert(result.detail);
  }
}

// 2. 用户注册
async function registerWithVerification(userData) {
  const response = await fetch('/api/v1/users/register-with-verification', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData)
  });
  
  const result = await response.json();
  if (response.ok) {
    alert('注册成功！');
    // 跳转到登录页面或自动登录
  } else {
    alert(result.detail);
  }
}
```

## 测试

### 1. Redis连接测试

```bash
python test_redis_connection.py
```

### 2. 邮箱验证功能测试

```bash
# 启动服务
uvicorn main:app --reload

# 运行测试
python test_email_verification.py
```

### 3. 手动测试

使用Postman或curl测试API接口：

```bash
# 发送验证码
curl -X POST "http://localhost:8000/api/v1/users/send-verification-code" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "action": "注册"}'

# 验证验证码
curl -X POST "http://localhost:8000/api/v1/users/verify-email-code" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "code": "123456", "action": "register"}'
```

## 安全考虑

1. **频率限制**: 1分钟内只能发送一次验证码
2. **验证码有效期**: 5分钟自动过期
3. **一次性使用**: 验证码验证成功后立即删除
4. **密钥安全**: 腾讯云密钥通过环境变量配置
5. **输入验证**: 严格验证邮箱格式和验证码格式

## 故障排除

### 常见问题

1. **Redis连接失败**
   - 检查Redis服务是否启动
   - 验证连接配置（主机、端口、密码）
   - 检查防火墙设置

2. **邮件发送失败**
   - 检查腾讯云SES配置
   - 验证API密钥是否正确
   - 确认发送邮箱地址已验证
   - 检查邮件模板ID是否正确

3. **验证码验证失败**
   - 确认验证码未过期（5分钟）
   - 检查邮箱地址是否一致
   - 验证Redis中是否存储了验证码

### 调试方法

1. 查看服务日志
2. 使用Redis CLI检查缓存数据
3. 运行测试脚本诊断问题
4. 检查腾讯云SES控制台的发送记录

## 生产环境部署

1. **环境变量**: 确保所有敏感配置通过环境变量设置
2. **Redis集群**: 考虑使用Redis集群提高可用性
3. **监控告警**: 设置邮件发送失败和Redis连接异常的监控
4. **日志记录**: 记录验证码发送和验证的关键操作
5. **备用方案**: 考虑短信验证作为邮箱验证的备用方案

## 扩展功能

未来可以考虑添加的功能：

- 短信验证码支持
- 验证码重发次数限制
- 邮件模板自定义
- 多语言支持
- 验证码统计和分析
- 邮箱验证状态管理