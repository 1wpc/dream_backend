from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, Numeric
from decimal import Decimal
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum

class PointTransactionType(enum.Enum):
    """积分交易类型"""
    REGISTER = "register"           # 注册奖励
    LOGIN = "login"                 # 登录奖励
    TASK = "task"                   # 任务奖励
    PURCHASE = "purchase"           # 购买消费
    REFUND = "refund"               # 退款返还
    ADMIN_ADJUST = "admin_adjust"   # 管理员调整
    GIFT = "gift"                   # 赠送
    ACTIVITY = "activity"           # 活动奖励
    IMAGE_GENERATION = "image_generation" # 图片生成消费
    DEEPSEEK_CHAT = "deepseek_chat" # DeepSeek聊天消费
    PAYMENT_REWARD = "payment_reward" # 支付奖励

class OrderStatus(enum.Enum):
    """订单状态"""
    PENDING = "pending"             # 待支付
    PAID = "paid"                   # 已支付
    CANCELLED = "cancelled"         # 已取消
    REFUNDED = "refunded"           # 已退款
    CLOSED = "closed"               # 已关闭

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱")
    hashed_password = Column(String(255), nullable=False, comment="加密后的密码")
    full_name = Column(String(255), nullable=True, comment="真实姓名")
    phone = Column(String(255), nullable=True, comment="手机号")
    avatar = Column(Text, nullable=True, comment="头像URL")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    is_superuser = Column(Boolean, default=False, nullable=False, comment="是否为超级用户")
    
    # 积分相关字段
    points_balance = Column(Numeric(10, 2), default=0, nullable=False, comment="积分余额")
    total_points_earned = Column(Numeric(10, 2), default=0, nullable=False, comment="累计获得积分")
    total_points_spent = Column(Numeric(10, 2), default=0, nullable=False, comment="累计消费积分")
    
    # 认证相关字段
    refresh_token = Column(Text, nullable=True, comment="刷新令牌")
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True, comment="刷新令牌过期时间")
    last_active_at = Column(DateTime(timezone=True), server_default=func.now(), comment="最后活跃时间")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    point_transactions = relationship("PointTransaction", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', points={self.points_balance})>"

class PointTransaction(Base):
    __tablename__ = "point_transactions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    transaction_type = Column(SQLEnum(PointTransactionType), nullable=False, comment="交易类型")
    amount = Column(Numeric(10, 2), nullable=False, comment="积分数量（正数为增加，负数为减少）")
    balance_before = Column(Numeric(10, 2), nullable=False, comment="交易前余额")
    balance_after = Column(Numeric(10, 2), nullable=False, comment="交易后余额")
    description = Column(String(255), nullable=True, comment="交易描述")
    reference_id = Column(String(100), nullable=True, comment="关联ID（如订单ID）")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关系
    user = relationship("User", back_populates="point_transactions")
    
    def __repr__(self):
        return f"<PointTransaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type={self.transaction_type})>"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    out_trade_no = Column(String(100), unique=True, index=True, nullable=False, comment="商户订单号")
    trade_no = Column(String(100), nullable=True, comment="支付宝交易号")
    subject = Column(String(256), nullable=False, comment="订单标题")
    body = Column(Text, nullable=True, comment="订单描述")
    total_amount = Column(Numeric(10, 2), nullable=False, comment="订单金额")
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False, comment="订单状态")
    
    # 支付相关信息
    paid_amount = Column(Numeric(10, 2), default=0, nullable=False, comment="实际支付金额")
    payment_time = Column(DateTime(timezone=True), nullable=True, comment="支付时间")
    
    # 积分奖励相关
    points_awarded = Column(Numeric(10, 2), default=0, nullable=False, comment="已奖励积分")
    points_rate = Column(Numeric(5, 4), default=10, nullable=False, comment="积分奖励比例")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="orders")
    
    def __repr__(self):
        return f"<Order(id={self.id}, out_trade_no='{self.out_trade_no}', user_id={self.user_id}, status={self.status})>"