#!/usr/bin/env python3
"""
测试积分奖励比例功能
验证充值时获得充值金额十倍积分的功能
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
    username = f"test_user_{datetime.now().strftime('%H%M%S')}"
    email = f"test_{datetime.now().strftime('%H%M%S')}@example.com"
    
    user = User(
        username=username,
        email=email,
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

def test_points_rate_10x(db: Session, user: User):
    """测试10倍积分奖励率"""
    print("\n🧪 测试10倍积分奖励率...")
    
    # 测试不同金额的充值
    test_amounts = [Decimal('1.00'), Decimal('10.00'), Decimal('50.00'), Decimal('100.00')]
    
    for amount in test_amounts:
        print(f"\n💰 测试充值金额: {amount} 元")
        
        # 1. 创建订单（使用默认积分奖励率）
        out_trade_no = f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        order = crud.create_order(
            db=db,
            user_id=user.id,
            out_trade_no=out_trade_no,
            subject=f"充值{amount}元",
            body="测试充值订单",
            total_amount=amount
            # 不传递 points_rate 参数，使用默认值 10
        )
        
        if not order:
            print(f"❌ 创建订单失败")
            return False
        
        print(f"✅ 创建订单成功: {out_trade_no}")
        print(f"   订单金额: {order.total_amount}")
        print(f"   积分奖励率: {order.points_rate}")
        
        # 2. 模拟支付成功
        trade_no = f"ALIPAY_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        updated_order = crud.update_order_payment_success(
            db=db,
            out_trade_no=out_trade_no,
            trade_no=trade_no,
            paid_amount=amount,
            payment_time=datetime.now()
        )
        
        if not updated_order:
            print(f"❌ 更新订单状态失败")
            return False
        
        print(f"✅ 订单支付成功: {trade_no}")
        
        # 3. 计算预期积分
        expected_points = amount * updated_order.points_rate
        print(f"   预期奖励积分: {expected_points}")
        
        # 4. 奖励积分
        result = crud.award_points_for_order(
            db=db,
            order_id=updated_order.id,
            points_amount=expected_points
        )
        
        if not result:
            print(f"❌ 积分奖励失败")
            return False
        
        order, transaction = result
        print(f"✅ 积分奖励成功: {transaction.amount} 积分")
        
        # 5. 验证积分是否为充值金额的10倍
        expected_10x_points = amount * 10
        if transaction.amount == expected_10x_points:
            print(f"✅ 积分验证通过: 充值{amount}元获得{transaction.amount}积分 (10倍)")
        else:
            print(f"❌ 积分验证失败: 充值{amount}元获得{transaction.amount}积分，预期{expected_10x_points}积分")
            return False
    
    # 6. 验证用户总积分
    db.refresh(user)
    total_charged = sum(test_amounts)
    expected_total_points = total_charged * 10
    
    print(f"\n📊 最终验证:")
    print(f"   总充值金额: {total_charged} 元")
    print(f"   用户积分余额: {user.points_balance}")
    print(f"   预期总积分: {expected_total_points}")
    
    if user.points_balance == expected_total_points:
        print(f"✅ 总积分验证通过: 充值{total_charged}元获得{user.points_balance}积分 (10倍)")
        return True
    else:
        print(f"❌ 总积分验证失败")
        return False

def main():
    """主函数"""
    print("🚀 开始测试积分奖励比例功能...")
    
    db = SessionLocal()
    try:
        # 创建测试用户
        user = create_test_user(db)
        
        # 测试10倍积分奖励率
        if not test_points_rate_10x(db, user):
            print("\n❌ 测试失败！")
            sys.exit(1)
        
        print("\n🎉 所有测试通过！积分奖励比例功能正常工作")
        print("💡 用户充值时将获得充值金额十倍的积分")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()