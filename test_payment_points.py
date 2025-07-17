#!/usr/bin/env python3
"""
支付积分奖励功能测试脚本
用于测试支付成功后自动奖励积分的完整流程
"""

import sys
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User, Order, PointTransaction, OrderStatus, PointTransactionType
import crud
from auth import get_password_hash

def create_test_user(db: Session) -> User:
    """创建测试用户"""
    # 检查是否已存在测试用户
    existing_user = db.query(User).filter(User.username == "test_user").first()
    if existing_user:
        print(f"测试用户已存在: {existing_user.username}")
        return existing_user
    
    # 创建新的测试用户
    user = User(
        username="test_user",
        email="test@example.com",
        hashed_password=get_password_hash("test123"),
        full_name="测试用户",
        is_active=True,
        points_balance=Decimal('0'),
        total_points_earned=Decimal('0'),
        total_points_spent=Decimal('0')
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"✅ 创建测试用户: {user.username} (ID: {user.id})")
    return user

def test_payment_flow(db: Session, user: User):
    """测试完整的支付积分奖励流程"""
    print("\n🧪 开始测试支付积分奖励流程...")
    
    # 1. 创建订单
    out_trade_no = f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    total_amount = Decimal('100.00')
    
    order = crud.create_order(
        db=db,
        user_id=user.id,
        out_trade_no=out_trade_no,
        subject="测试商品",
        body="这是一个测试订单",
        total_amount=total_amount,
        points_rate=Decimal('0.01')  # 1%积分奖励率
    )
    
    if not order:
        print("❌ 创建订单失败")
        return False
    
    print(f"✅ 创建订单成功: {out_trade_no}, 金额: {total_amount}")
    
    # 2. 模拟支付成功，更新订单状态
    trade_no = f"ALIPAY_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    updated_order = crud.update_order_payment_success(
        db=db,
        out_trade_no=out_trade_no,
        trade_no=trade_no,
        paid_amount=total_amount,
        payment_time=datetime.now()
    )
    
    if not updated_order:
        print("❌ 更新订单状态失败")
        return False
    
    print(f"✅ 订单支付成功: {trade_no}")
    
    # 3. 奖励积分
    points_to_award = total_amount * updated_order.points_rate
    print(f"准备奖励积分: {points_to_award}")
    
    try:
        result = crud.award_points_for_order(
            db=db,
            order_id=updated_order.id,
            points_amount=points_to_award
        )
        
        if not result:
            print("❌ 积分奖励失败")
            return False
        
        order, transaction = result
        print(f"✅ 积分奖励成功: {points_to_award} 积分")
    except Exception as e:
        print(f"❌ 积分奖励过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 验证结果
    # 刷新用户信息
    db.refresh(user)
    
    print(f"\n📊 测试结果:")
    print(f"   用户积分余额: {user.points_balance}")
    print(f"   累计获得积分: {user.total_points_earned}")
    print(f"   订单状态: {order.status.value}")
    print(f"   订单奖励积分: {order.points_awarded}")
    print(f"   积分交易类型: {transaction.transaction_type.value}")
    print(f"   积分交易描述: {transaction.description}")
    
    # 验证积分是否正确
    expected_points = total_amount * Decimal('0.01')
    if user.points_balance == expected_points and order.points_awarded == expected_points:
        print("\n🎉 测试通过！支付积分奖励功能正常工作")
        return True
    else:
        print("\n❌ 测试失败！积分计算不正确")
        return False

def test_duplicate_notification(db: Session, user: User):
    """测试重复通知处理"""
    print("\n🧪 测试重复通知处理...")
    
    # 获取已支付的订单
    paid_order = db.query(Order).filter(
        Order.user_id == user.id,
        Order.status == OrderStatus.PAID
    ).first()
    
    if not paid_order:
        print("❌ 没有找到已支付的订单")
        return False
    
    # 尝试再次奖励积分（应该失败）
    result = crud.award_points_for_order(
        db=db,
        order_id=paid_order.id,
        points_amount=Decimal('10.00')
    )
    
    if result is None:
        print("✅ 重复通知处理正确：已奖励过积分的订单不会重复奖励")
        return True
    else:
        print("❌ 重复通知处理失败：订单被重复奖励积分")
        return False

def main():
    """主函数"""
    print("🚀 开始支付积分奖励功能测试...")
    
    db = SessionLocal()
    try:
        # 创建测试用户
        user = create_test_user(db)
        
        # 测试支付流程
        if not test_payment_flow(db, user):
            sys.exit(1)
        
        # 测试重复通知处理
        if not test_duplicate_notification(db, user):
            sys.exit(1)
        
        print("\n🎉 所有测试通过！支付积分奖励功能完全正常")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()