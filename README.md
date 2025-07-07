# Dream Backend - 用户管理后端系统

基于FastAPI和MySQL的用户管理后端系统，提供用户注册、登录、JWT认证等功能。

## 功能特性

- 🔐 用户注册和登录
- 🔑 JWT token认证
- 📋 用户信息CRUD操作
- 🛡️ 密码加密存储
- 📊 用户状态管理（激活/禁用）
- 🔒 权限管理（普通用户/超级用户）
- 📚 完整的API文档

## 技术栈

- **FastAPI** - 现代高性能的Python web框架
- **MySQL** - 关系型数据库
- **SQLAlchemy** - ORM框架
- **JWT** - JSON Web Token认证
- **bcrypt** - 密码加密
- **Pydantic** - 数据验证

## 安装和配置

### 1. 环境要求

- Python 3.8+
- MySQL 5.7+

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 数据库配置

**选项1：自动创建数据库（推荐）**

代码会自动检测并创建数据库，你只需要：
1. 确保MySQL服务正在运行
2. 修改`config.py`中的数据库连接信息（用户名、密码等）

**选项2：手动创建数据库**

如果想手动创建数据库，可以在MySQL中执行：

```sql
CREATE DATABASE dream_backend CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 配置文件

复制 `.env.example` 为 `.env` 并修改配置：

```env
# 数据库配置
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=dream_backend

# JWT配置
SECRET_KEY=your-secret-key-change-this-in-production-environment
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API配置
API_VERSION=v1
PROJECT_NAME=Dream Backend

# 调试模式
DEBUG=True
```

### 5. 初始化数据库

```bash
# 运行数据库初始化脚本
python init_db.py
```

该脚本会：
- 创建数据库表
- 创建初始超级用户账号（可选）

### 6. 运行应用

```bash
# 开发模式
python main.py

# 或者使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

应用将在 `http://localhost:8000` 启动。

### 7. 测试API（可选）

```bash
# 运行API测试脚本
python test_api.py
```

该脚本会自动测试：
- 健康检查
- 用户注册
- 用户登录
- 获取用户信息
- 更新用户信息
- 获取用户列表

## API文档

启动应用后，可以通过以下链接查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API接口

### 用户注册

```bash
POST /api/v1/users/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "full_name": "测试用户"
}
```

### 用户登录

```bash
POST /api/v1/users/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}
```

### 获取当前用户信息

```bash
GET /api/v1/users/me
Authorization: Bearer <access_token>
```

### 更新用户信息

```bash
PUT /api/v1/users/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": "新的用户名",
  "phone": "13800138000"
}
```

### 获取用户列表

```bash
GET /api/v1/users/
Authorization: Bearer <access_token>
```

## 数据库表结构

### users 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键，自增 |
| username | VARCHAR(50) | 用户名，唯一 |
| email | VARCHAR(100) | 邮箱，唯一 |
| hashed_password | VARCHAR(255) | 加密后的密码 |
| full_name | VARCHAR(100) | 真实姓名 |
| phone | VARCHAR(20) | 手机号 |
| avatar | TEXT | 头像URL |
| is_active | BOOLEAN | 是否激活 |
| is_superuser | BOOLEAN | 是否为超级用户 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## 项目结构

```
dream_backend/
├── main.py              # 主应用入口
├── config.py            # 配置文件
├── database.py          # 数据库连接
├── models.py            # 数据库模型
├── schemas.py           # Pydantic模型
├── auth.py              # 认证相关
├── crud.py              # CRUD操作
├── init_db.py           # 数据库初始化脚本
├── test_api.py          # API测试脚本
├── requirements.txt     # 项目依赖
├── README.md           # 项目说明
└── routers/            # 路由模块
    ├── __init__.py
    └── user.py         # 用户路由
```

## 开发说明

### 添加新的API路由

1. 在 `routers/` 目录下创建新的路由文件
2. 在 `main.py` 中导入并注册路由
3. 更新相关的模型和schema

### 数据库迁移

当修改数据库模型时：

1. 删除现有数据库表
2. 重新启动应用自动创建新表
3. 或者使用Alembic进行数据库迁移

### 安全注意事项

- 在生产环境中修改默认的SECRET_KEY
- 使用HTTPS
- 限制CORS允许的域名
- 定期更新依赖包
- 配置合适的数据库用户权限

## 许可证

MIT License 