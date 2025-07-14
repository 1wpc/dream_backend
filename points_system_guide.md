# 💰 积分系统使用指南

## 🎯 系统概述

积分系统是Dream Backend的核心功能之一，提供完整的积分管理功能，包括：

- 💰 积分余额管理
- 📊 积分交易记录
- 🎁 自动奖励机制
- 🔄 积分转移功能
- 🛡️ 安全的权限控制

## 🏗️ 系统架构

### 数据模型

```
User (用户)
├── points_balance (当前积分余额)
├── total_points_earned (累计获得积分)
└── total_points_spent (累计消费积分)

PointTransaction (积分交易)
├── user_id (用户ID)
├── transaction_type (交易类型)
├── amount (积分数量)
├── balance_before (交易前余额)
├── balance_after (交易后余额)
├── description (交易描述)
└── reference_id (关联订单ID等)
```

### 交易类型

| 类型 | 代码 | 描述 | 示例 |
|------|------|------|------|
| 注册奖励 | `register` | 新用户注册时自动获得 | +100积分 |
| 登录奖励 | `login` | 每日登录奖励 | +10积分 |
| 任务奖励 | `task` | 完成任务获得 | +50积分 |
| 购买消费 | `purchase` | 购买商品消费 | -200积分 |
| 退款返还 | `refund` | 退款时返还积分 | +200积分 |
| 管理员调整 | `admin_adjust` | 管理员手动调整 | ±任意积分 |
| 赠送转移 | `gift` | 用户间转移积分 | ±任意积分 |
| 活动奖励 | `activity` | 活动奖励 | +积分 |

## 🚀 快速开始

### 1. 用户注册自动获得积分

```python
# 用户注册时自动获得100积分
POST /api/v1/users/register
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123"
}

# 注册成功后，用户自动获得100积分的注册奖励
```

### 2. 查看积分余额

```python
GET /api/v1/points/balance
Authorization: Bearer <token>

# 响应
{
  "points_balance": "110.00",
  "total_points_earned": "110.00",
  "total_points_spent": "0.00"
}
```

### 3. 查看积分交易记录

```python
GET /api/v1/points/transactions?page=1&page_size=10
Authorization: Bearer <token>

# 响应
{
  "transactions": [
    {
      "id": 1,
      "user_id": 1,
      "transaction_type": "register",
      "amount": "100.00",
      "balance_before": "0.00",
      "balance_after": "100.00",
      "description": "注册奖励积分",
      "created_at": "2023-12-01T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

## 🎁 积分获得方式

### 1. 注册奖励

```python
# 新用户注册时自动获得100积分
# 无需额外操作，注册成功后自动添加
```

### 2. 登录奖励

```python
POST /api/v1/points/login-bonus
Authorization: Bearer <token>

# 响应
{
  "id": 2,
  "user_id": 1,
  "transaction_type": "login",
  "amount": "10.00",
  "balance_before": "100.00",
  "balance_after": "110.00",
  "description": "每日登录奖励",
  "created_at": "2023-12-01T10:30:00Z"
}
```

### 3. 管理员奖励

```python
# 仅超级用户可以操作
POST /api/v1/points/add
Authorization: Bearer <admin_token>
{
  "target_user_id": 1,
  "amount": 50.00,
  "transaction_type": "task",
  "description": "完成任务奖励"
}
```

## 🔄 积分转移

### 用户间转移积分

```python
POST /api/v1/points/transfer
Authorization: Bearer <token>
{
  "to_user_id": 2,
  "amount": 30.00,
  "description": "转移积分给朋友"
}

# 响应
{
  "message": "成功转移 30.00 积分给用户 2"
}
```

### 转移规则

- ✅ 只能转移给其他用户，不能转给自己
- ✅ 转移金额必须大于0
- ✅ 必须有足够的积分余额
- ✅ 会同时创建两条交易记录（转出和转入）

## 👑 管理员功能

### 1. 查看任意用户积分

```python
GET /api/v1/points/users/{user_id}/balance
Authorization: Bearer <admin_token>
```

### 2. 查看任意用户交易记录

```python
GET /api/v1/points/users/{user_id}/transactions
Authorization: Bearer <admin_token>
```

### 3. 给用户添加积分

```python
POST /api/v1/points/add
Authorization: Bearer <admin_token>
{
  "target_user_id": 1,
  "amount": 100.00,
  "transaction_type": "admin_adjust",
  "description": "管理员奖励"
}
```

### 4. 扣除用户积分

```python
POST /api/v1/points/deduct
Authorization: Bearer <admin_token>
{
  "target_user_id": 1,
  "amount": 50.00,
  "transaction_type": "admin_adjust",
  "description": "管理员扣除"
}
```

### 5. 查看所有交易记录

```python
GET /api/v1/points/all-transactions?skip=0&limit=50
Authorization: Bearer <admin_token>
```

## 💡 使用场景示例

### 场景1: 电商系统

```python
# 用户购买商品，扣除积分
POST /api/v1/points/deduct
{
  "target_user_id": 1,
  "amount": 200.00,
  "transaction_type": "purchase",
  "description": "购买商品：iPhone 15",
  "reference_id": "order_123456"
}

# 用户退款，返还积分
POST /api/v1/points/add
{
  "target_user_id": 1,
  "amount": 200.00,
  "transaction_type": "refund",
  "description": "退款：iPhone 15",
  "reference_id": "order_123456"
}
```

### 场景2: 任务系统

```python
# 用户完成任务，获得积分
POST /api/v1/points/add
{
  "target_user_id": 1,
  "amount": 50.00,
  "transaction_type": "task",
  "description": "完成每日签到任务",
  "reference_id": "task_daily_checkin"
}
```

### 场景3: 活动奖励

```python
# 活动期间，给所有用户发放积分
POST /api/v1/points/add
{
  "target_user_id": 1,
  "amount": 100.00,
  "transaction_type": "activity",
  "description": "双十一活动奖励",
  "reference_id": "activity_1111"
}
```

## 🛡️ 安全机制

### 1. 权限控制

- 普通用户只能查看自己的积分信息
- 只有超级用户可以管理其他用户的积分
- 所有操作都需要JWT token认证

### 2. 数据一致性

- 使用数据库事务确保积分操作的原子性
- 每次积分变动都会记录详细的交易记录
- 余额不足时会阻止扣除操作

### 3. 操作审计

- 所有积分操作都有完整的审计日志
- 记录操作时间、操作类型、操作金额
- 支持通过reference_id关联业务订单

## 📊 数据统计

### 用户积分概览

```python
# 获取用户积分统计
GET /api/v1/points/balance

# 返回数据包含：
# - 当前积分余额
# - 累计获得积分
# - 累计消费积分
```

### 交易记录分析

```python
# 分页查询交易记录
GET /api/v1/points/transactions?page=1&page_size=20

# 支持按时间、类型等条件筛选
# 可以用于生成积分报表
```

## 🔧 开发集成

### 1. 在业务代码中集成积分系统

```python
from crud import add_points, deduct_points
from models import PointTransactionType
from decimal import Decimal

# 给用户添加积分
def reward_user(db, user_id, amount, description):
    return add_points(
        db, user_id, Decimal(str(amount)), 
        PointTransactionType.TASK, description
    )

# 扣除用户积分
def consume_points(db, user_id, amount, description):
    return deduct_points(
        db, user_id, Decimal(str(amount)), 
        PointTransactionType.PURCHASE, description
    )
```

### 2. 自定义积分规则

```python
# 可以在config.py中配置积分规则
POINTS_RULES = {
    "register_bonus": 100,      # 注册奖励
    "login_bonus": 10,          # 登录奖励
    "daily_task": 50,           # 每日任务
    "weekly_task": 200,         # 每周任务
}
```

## 📈 性能优化

### 1. 数据库索引

```sql
-- 为积分交易表添加索引
CREATE INDEX idx_user_id ON point_transactions(user_id);
CREATE INDEX idx_created_at ON point_transactions(created_at);
CREATE INDEX idx_transaction_type ON point_transactions(transaction_type);
```

### 2. 缓存策略

```python
# 可以使用Redis缓存用户积分余额
# 减少数据库查询压力
```

## 🚨 常见问题

### Q1: 积分操作失败怎么办？

**A**: 系统使用数据库事务，操作失败会自动回滚，不会产生数据不一致。

### Q2: 如何防止积分被恶意刷取？

**A**: 
- 所有积分操作都需要认证
- 管理员操作需要超级用户权限
- 可以在业务层添加频率限制

### Q3: 积分精度如何控制？

**A**: 使用DECIMAL(10,2)类型，支持最大8位整数和2位小数。

### Q4: 如何批量操作积分？

**A**: 可以在业务层循环调用积分API，或者开发批量操作接口。

## 📝 总结

积分系统提供了完整的积分管理功能，支持：

- ✅ 灵活的积分获得方式
- ✅ 安全的积分转移机制
- ✅ 完善的权限控制
- ✅ 详细的交易记录
- ✅ 强大的管理员功能

通过合理使用积分系统，可以有效提升用户粘性和活跃度！🎉 