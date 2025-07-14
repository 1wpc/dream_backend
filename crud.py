from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
from models import User, PointTransaction, PointTransactionType
from schemas import UserCreate, UserUpdate, PointTransactionCreate
from auth import get_password_hash
from typing import Optional, List
from decimal import Decimal

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
        avatar=user.avatar,
        points_balance=Decimal('0.00'),
        total_points_earned=Decimal('0.00'),
        total_points_spent=Decimal('0.00')
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # 给新用户赠送注册积分
        register_points = Decimal('100.00')  # 注册赠送100积分
        add_points(
            db, 
            db_user.id, 
            register_points, 
            PointTransactionType.REGISTER,
            "注册奖励积分"
        )
        
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

# 积分相关操作
def add_points(
    db: Session, 
    user_id: int, 
    amount: Decimal, 
    transaction_type: PointTransactionType, 
    description: Optional[str] = None,
    reference_id: Optional[str] = None
) -> Optional[PointTransaction]:
    """给用户添加积分"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    try:
        # 记录交易前余额
        balance_before = db_user.points_balance
        balance_after = balance_before + amount
        
        # 创建积分交易记录
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            reference_id=reference_id
        )
        
        # 更新用户积分
        db_user.points_balance = balance_after
        db_user.total_points_earned += amount
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
        
    except Exception:
        db.rollback()
        return None

def deduct_points(
    db: Session, 
    user_id: int, 
    amount: Decimal, 
    transaction_type: PointTransactionType, 
    description: Optional[str] = None,
    reference_id: Optional[str] = None
) -> Optional[PointTransaction]:
    """扣除用户积分"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    # 检查积分是否足够
    if db_user.points_balance < amount:
        raise ValueError("积分余额不足")
    
    try:
        # 记录交易前余额
        balance_before = db_user.points_balance
        balance_after = balance_before - amount
        
        # 创建积分交易记录
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=-amount,  # 负数表示扣除
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            reference_id=reference_id
        )
        
        # 更新用户积分
        db_user.points_balance = balance_after
        db_user.total_points_spent += amount
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
        
    except Exception:
        db.rollback()
        return None

def get_user_points_balance(db: Session, user_id: int) -> Optional[dict]:
    """获取用户积分余额"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    return {
        "points_balance": db_user.points_balance,
        "total_points_earned": db_user.total_points_earned,
        "total_points_spent": db_user.total_points_spent
    }

def get_user_point_transactions(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 50
) -> List[PointTransaction]:
    """获取用户积分交易记录"""
    return db.query(PointTransaction).filter(
        PointTransaction.user_id == user_id
    ).order_by(desc(PointTransaction.created_at)).offset(skip).limit(limit).all()

def get_point_transaction_by_id(db: Session, transaction_id: int) -> Optional[PointTransaction]:
    """根据ID获取积分交易记录"""
    return db.query(PointTransaction).filter(PointTransaction.id == transaction_id).first()

def get_all_point_transactions(
    db: Session, 
    skip: int = 0, 
    limit: int = 50
) -> List[PointTransaction]:
    """获取所有积分交易记录（管理员用）"""
    return db.query(PointTransaction).order_by(
        desc(PointTransaction.created_at)
    ).offset(skip).limit(limit).all()

def count_user_point_transactions(db: Session, user_id: int) -> int:
    """统计用户积分交易记录数量"""
    return db.query(PointTransaction).filter(PointTransaction.user_id == user_id).count()

def transfer_points(
    db: Session,
    from_user_id: int,
    to_user_id: int,
    amount: Decimal,
    description: Optional[str] = None,
    reference_id: Optional[str] = None
) -> Optional[tuple]:
    """积分转移（从一个用户转移到另一个用户）"""
    try:
        # 扣除转出用户的积分
        deduct_transaction = deduct_points(
            db, from_user_id, amount, PointTransactionType.GIFT,
            f"转出给用户{to_user_id}: {description}" if description else f"转出给用户{to_user_id}",
            reference_id
        )
        
        if not deduct_transaction:
            return None
        
        # 添加转入用户的积分
        add_transaction = add_points(
            db, to_user_id, amount, PointTransactionType.GIFT,
            f"来自用户{from_user_id}: {description}" if description else f"来自用户{from_user_id}",
            reference_id
        )
        
        if not add_transaction:
            # 如果转入失败，需要回滚转出操作
            db.rollback()
            return None
        
        return (deduct_transaction, add_transaction)
        
    except Exception:
        db.rollback()
        return None 