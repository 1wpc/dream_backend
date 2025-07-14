from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

class PointTransactionType(str, Enum):
    """积分交易类型"""
    REGISTER = "register"
    LOGIN = "login"
    TASK = "task"
    PURCHASE = "purchase"
    REFUND = "refund"
    ADMIN_ADJUST = "admin_adjust"
    GIFT = "gift"
    ACTIVITY = "activity"
    IMAGE_GENERATION = "image_generation"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None

class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少为6位')
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('用户名长度至少为3位')
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    points_balance: Decimal
    total_points_earned: Decimal
    total_points_spent: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class User(UserInDB):
    pass

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class Message(BaseModel):
    message: str

class UserResponse(BaseModel):
    user: User
    message: str

# 积分相关Schema
class PointTransactionCreate(BaseModel):
    user_id: int
    transaction_type: PointTransactionType
    amount: Decimal
    description: Optional[str] = None
    reference_id: Optional[str] = None

class PointTransactionResponse(BaseModel):
    id: int
    user_id: int
    transaction_type: PointTransactionType
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    description: Optional[str] = None
    reference_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class PointsBalance(BaseModel):
    points_balance: Decimal
    total_points_earned: Decimal
    total_points_spent: Decimal

class PointsOperation(BaseModel):
    amount: Decimal
    transaction_type: PointTransactionType
    description: Optional[str] = None
    reference_id: Optional[str] = None
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('积分数量必须大于0')
        return v

class PointsTransactionList(BaseModel):
    transactions: List[PointTransactionResponse]
    total: int
    page: int
    page_size: int 

# 图片生成相关Schema
class ImageGenerationRequest(BaseModel):
    prompt: str
    width: Optional[int] = 512
    height: Optional[int] = 512
    seed: Optional[int] = -1
    use_sr: Optional[bool] = True
    use_pre_llm: Optional[bool] = True

class ImageGenerationResponse(BaseModel):
    image_url: str
    points_spent: Decimal
    points_remaining: Decimal
    message: str

# 支付相关Schema
class PaymentRequest(BaseModel):
    """支付请求"""
    subject: str  # 商品标题
    body: str  # 商品描述
    total_amount: Decimal  # 支付金额
    out_trade_no: Optional[str] = None  # 商户订单号，如果不提供会自动生成
    
    @field_validator('total_amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('支付金额必须大于0')
        return v
    
    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('商品标题不能为空')
        return v.strip()

class PaymentResponse(BaseModel):
    """支付响应"""
    order_string: str  # 支付宝订单字符串
    out_trade_no: str  # 商户订单号
    total_amount: Decimal  # 支付金额
    subject: str  # 商品标题
    message: str  # 响应消息

class PaymentNotification(BaseModel):
    """支付宝异步通知"""
    out_trade_no: str  # 商户订单号
    trade_no: str  # 支付宝交易号
    trade_status: str  # 交易状态
    total_amount: Decimal  # 交易金额
    buyer_id: str  # 买家支付宝用户号
    seller_id: str  # 卖家支付宝用户号