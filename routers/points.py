from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from database import get_db
from schemas import (
    PointsBalance, 
    PointsOperation, 
    PointTransactionResponse,
    PointsTransactionList,
    Message,
    User
)
from auth import get_current_active_user
from models import PointTransactionType
import crud

router = APIRouter(
    prefix="/points",
    tags=["积分管理"],
    responses={404: {"description": "Not found"}},
)

@router.get("/balance", response_model=PointsBalance)
async def get_points_balance(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户积分余额"""
    balance = crud.get_user_points_balance(db, current_user.id)
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return balance

@router.get("/transactions", response_model=PointsTransactionList)
async def get_points_transactions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户积分交易记录"""
    skip = (page - 1) * page_size
    transactions = crud.get_user_point_transactions(db, current_user.id, skip, page_size)
    total = crud.count_user_point_transactions(db, current_user.id)
    
    return PointsTransactionList(
        transactions=transactions,
        total=total,
        page=page,
        page_size=page_size
    )

@router.post("/add", response_model=PointTransactionResponse)
async def add_points_to_user(
    target_user_id: int,
    points_op: PointsOperation,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """给指定用户添加积分（仅超级用户）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅超级用户可以操作"
        )
    
    try:
        transaction = crud.add_points(
            db, 
            target_user_id, 
            points_op.amount, 
            points_op.transaction_type,
            points_op.description,
            points_op.reference_id
        )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目标用户不存在"
            )
        
        return transaction
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"添加积分失败: {str(e)}"
        )

@router.post("/deduct", response_model=PointTransactionResponse)
async def deduct_points_from_user(
    target_user_id: int,
    points_op: PointsOperation,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """扣除指定用户积分（仅超级用户）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅超级用户可以操作"
        )
    
    try:
        transaction = crud.deduct_points(
            db, 
            target_user_id, 
            points_op.amount, 
            points_op.transaction_type,
            points_op.description,
            points_op.reference_id
        )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目标用户不存在"
            )
        
        return transaction
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"扣除积分失败: {str(e)}"
        )

@router.post("/transfer", response_model=Message)
async def transfer_points_to_user(
    to_user_id: int,
    amount: Decimal,
    description: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """转移积分给其他用户"""
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="转移积分数量必须大于0"
        )
    
    if to_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能转移积分给自己"
        )
    
    try:
        result = crud.transfer_points(
            db,
            current_user.id,
            to_user_id,
            amount,
            description
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="积分转移失败，请检查目标用户是否存在或余额是否充足"
            )
        
        return Message(message=f"成功转移 {amount} 积分给用户 {to_user_id}")
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"积分转移失败: {str(e)}"
        )

@router.get("/users/{user_id}/balance", response_model=PointsBalance)
async def get_user_points_balance(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取指定用户积分余额（仅超级用户）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅超级用户可以查看其他用户积分"
        )
    
    balance = crud.get_user_points_balance(db, user_id)
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return balance

@router.get("/users/{user_id}/transactions", response_model=PointsTransactionList)
async def get_user_points_transactions(
    user_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取指定用户积分交易记录（仅超级用户）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅超级用户可以查看其他用户积分记录"
        )
    
    skip = (page - 1) * page_size
    transactions = crud.get_user_point_transactions(db, user_id, skip, page_size)
    total = crud.count_user_point_transactions(db, user_id)
    
    return PointsTransactionList(
        transactions=transactions,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/all-transactions", response_model=List[PointTransactionResponse])
async def get_all_points_transactions(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=100, description="限制数量"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取所有用户积分交易记录（仅超级用户）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅超级用户可以查看所有积分记录"
        )
    
    transactions = crud.get_all_point_transactions(db, skip, limit)
    return transactions

@router.post("/login-bonus", response_model=PointTransactionResponse)
async def claim_login_bonus(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """领取登录奖励积分"""
    # 这里可以添加逻辑检查用户今天是否已经领取过登录奖励
    # 为了演示，我们简单地给用户添加10积分
    
    login_bonus = Decimal('10.00')
    transaction = crud.add_points(
        db,
        current_user.id,
        login_bonus,
        PointTransactionType.LOGIN,
        "每日登录奖励"
    )
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="领取登录奖励失败"
        )
    
    return transaction 