from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import User
from schemas import UserCreate, UserUpdate
from auth import get_password_hash
from typing import Optional

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    """创建新用户"""
    # 检查用户名是否已存在
    if get_user_by_username(db, user.username):
        raise ValueError("用户名已存在")
    
    # 检查邮箱是否已存在
    if get_user_by_email(db, user.email):
        raise ValueError("邮箱已存在")
    
    # 创建用户对象
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone=user.phone,
        avatar=user.avatar
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("用户创建失败，用户名或邮箱可能已存在")

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """更新用户信息"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    # 更新用户信息
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("用户更新失败")

def delete_user(db: Session, user_id: int) -> bool:
    """删除用户"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    try:
        db.delete(db_user)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """获取用户列表"""
    return db.query(User).offset(skip).limit(limit).all()

def activate_user(db: Session, user_id: int) -> Optional[User]:
    """激活用户"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    db_user.is_active = True
    db.commit()
    db.refresh(db_user)
    return db_user

def deactivate_user(db: Session, user_id: int) -> Optional[User]:
    """禁用用户"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    db_user.is_active = False
    db.commit()
    db.refresh(db_user)
    return db_user 