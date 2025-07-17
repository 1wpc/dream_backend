#!/usr/bin/env python3
"""
简单的积分奖励测试
"""

import sys
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User, Order, PointTransaction, OrderStatus, PointTransactionType
import crud
from auth import get_password_hash

def main():
    print("🚀 开始简单积分奖励测试...")
    
    db = SessionLocal()
    try:
        # 1. 创建测试用户
        user = User(
            username=f"test_user_{datetime.now().strftime('%H%M%S')}",
            email=f"test_{datetime.now().strftime('%H%M%S')}@example.com",
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
        
        # 2. 创建订单
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
        
        print(f"✅ 创建订单成功: {out_trade_no}, 金额: {total_amount}")
        
        # 3. 模拟支付成功
        trade_no = f"ALIPAY_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        updated_order = crud.update_order_payment_success(
            db=db,
            out_trade_no=out_trade_no,
            trade_no=trade_no,
            paid_amount=total_amount,
            payment_time=datetime.now()
        )
        
        print(f"✅ 订单支付成功: {trade_no}")
        
        # 4. 奖励积分
        points_to_award = total_amount * updated_order.points_rate
        print(f"准备奖励积分: {points_to_award}")
        
        result = crud.award_points_for_order(
            db=db,
            order_id=updated_order.id,
            points_amount=points_to_award
        )
        
        if result:
            order, transaction = result
            print(f"✅ 积分奖励成功: {points_to_award} 积分")
            
            # 刷新用户信息
            db.refresh(user)
            
            print(f"\n📊 测试结果:")
            print(f"   用户积分余额: {user.points_balance}")
            print(f"   累计获得积分: {user.total_points_earned}")
            print(f"   订单状态: {order.status.value}")
            print(f"   订单奖励积分: {order.points_awarded}")
            print(f"   积分交易类型: {transaction.transaction_type.value}")
            print(f"   积分交易描述: {transaction.description}")
            
            print("\n🎉 积分奖励功能测试成功！")
        else:
            print("❌ 积分奖励失败")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()