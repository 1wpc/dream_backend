from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱")
    hashed_password = Column(String(255), nullable=False, comment="加密后的密码")
    full_name = Column(String(100), nullable=True, comment="真实姓名")
    phone = Column(String(20), nullable=True, comment="手机号")
    avatar = Column(Text, nullable=True, comment="头像URL")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    is_superuser = Column(Boolean, default=False, nullable=False, comment="是否为超级用户")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>" 