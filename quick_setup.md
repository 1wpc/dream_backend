# 🚀 快速设置指南

遇到数据库连接错误？按照以下步骤快速解决：

## 1️⃣ 检查MySQL服务状态

### Windows:
```bash
# 启动MySQL服务
net start mysql

# 或者通过服务管理器启动MySQL服务
services.msc
```

### Linux/Mac:
```bash
# 启动MySQL服务
sudo systemctl start mysql
# 或者
sudo service mysql start
```

## 2️⃣ 验证MySQL连接

```bash
# 测试MySQL连接
mysql -u root -p

# 如果连接成功，你会看到MySQL命令提示符
mysql>
```

## 3️⃣ 检查配置文件

修改 `config.py` 中的数据库配置：

```python
class Settings(BaseSettings):
    # 数据库配置 - 请根据你的实际情况修改
    MYSQL_USER: str = "root"           # 你的MySQL用户名
    MYSQL_PASSWORD: str = "your_password"  # 你的MySQL密码
    MYSQL_HOST: str = "localhost"      # MySQL服务器地址
    MYSQL_PORT: int = 3306            # MySQL端口
    MYSQL_DATABASE: str = "dream_backend"  # 数据库名称
```

## 4️⃣ 运行应用

```bash
# 现在代码会自动创建数据库
python main.py
```

## 🐛 常见问题解决

### 问题1：Access denied for user 'root'@'localhost'
**原因**：密码错误或用户权限不足
**解决**：
1. 检查MySQL密码是否正确
2. 确认用户是否有创建数据库的权限

### 问题2：Can't connect to MySQL server
**原因**：MySQL服务未启动或端口被占用
**解决**：
1. 启动MySQL服务
2. 检查3306端口是否被占用
3. 确认MySQL配置文件中的端口设置

### 问题3：Access denied for user 'root'@'localhost' (using password: YES)
**原因**：MySQL用户配置问题
**解决**：
```sql
# 连接到MySQL
mysql -u root -p

# 创建新用户（如果需要）
CREATE USER 'your_username'@'localhost' IDENTIFIED BY 'your_password';

# 授予权限
GRANT ALL PRIVILEGES ON *.* TO 'your_username'@'localhost';
FLUSH PRIVILEGES;
```

## 🔧 环境变量配置（可选）

创建 `.env` 文件来管理敏感信息：

```env
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=dream_backend
```

## ✅ 验证安装

运行测试脚本验证一切正常：

```bash
# 启动应用
python main.py

# 另开终端运行测试
python test_api.py
```

如果看到 "✅ 健康检查通过" 和其他成功消息，说明系统运行正常！

## 🆘 还有问题？

1. 检查MySQL错误日志
2. 确认防火墙设置
3. 验证网络连接
4. 查看完整的错误堆栈信息

记住：大多数数据库连接问题都是配置问题，仔细检查用户名、密码、主机地址和端口！ 