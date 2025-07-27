from datetime import datetime, timedelta
from typing import Optional
import secrets
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import User
from schemas import TokenData, Token, AccessTokenResponse
from config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT认证方案
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # 添加随机字符串增强安全性
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_urlsafe(32)  # JWT ID
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_token_pair(username: str, db: Session) -> Token:
    """创建access token和refresh token对"""
    # 创建access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    
    # 创建refresh token
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": username}, expires_delta=refresh_token_expires
    )
    
    # 更新用户的refresh token和过期时间
    user = db.query(User).filter(User.username == username).first()
    if user:
        user.refresh_token = refresh_token
        user.refresh_token_expires_at = datetime.utcnow() + refresh_token_expires
        user.last_active_at = datetime.utcnow()
        db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

def verify_token(token: str, expected_type: str = "access") -> TokenData:
    """验证JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token无效",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token类型错误，期望{expected_type}类型",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = TokenData(username=username, token_type=token_type)
        return token_data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_refresh_token(refresh_token: str, db: Session) -> User:
    """验证refresh token并检查数据库中的记录"""
    try:
        # 验证JWT格式和签名
        token_data = verify_token(refresh_token, "refresh")
        
        # 从数据库获取用户
        user = db.query(User).filter(User.username == token_data.username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
        
        # 检查数据库中存储的refresh token是否匹配
        if user.refresh_token != refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token无效"
            )
        
        # 检查refresh token是否过期
        if user.refresh_token_expires_at and user.refresh_token_expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token已过期"
            )
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token无效"
        )

def refresh_access_token(refresh_token: str, db: Session) -> AccessTokenResponse:
    """使用refresh token刷新access token（滑动窗口机制）"""
    user = verify_refresh_token(refresh_token, db)
    
    # 检查是否需要延长refresh token（滑动窗口）
    now = datetime.utcnow()
    sliding_window = timedelta(days=settings.REFRESH_TOKEN_SLIDING_WINDOW_DAYS)
    
    # 如果refresh token在滑动窗口期内，延长其有效期
    if user.refresh_token_expires_at and (user.refresh_token_expires_at - now) <= sliding_window:
        new_refresh_token_expires = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        user.refresh_token_expires_at = new_refresh_token_expires
    
    # 更新用户最后活跃时间
    user.last_active_at = now
    db.commit()
    
    # 创建新的access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return AccessTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户身份（支持用户名或邮箱登录）"""
    # 先尝试用户名登录
    user = db.query(User).filter(User.username == username).first()
    
    # 如果用户名不存在且输入包含@符号，尝试邮箱登录
    if not user and "@" in username:
        user = db.query(User).filter(User.email == username).first()
    
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    token = credentials.credentials
    token_data = verify_token(token)
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前激活的用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账号已被禁用"
        )
    return current_user