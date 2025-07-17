#!/usr/bin/env python3
"""
更新数据库枚举字段
"""

from database import SessionLocal
from sqlalchemy import text

def update_enum():
    db = SessionLocal()
    try:
        # 更新 transaction_type 枚举，添加 PAYMENT_REWARD
        sql = """
        ALTER TABLE point_transactions 
        MODIFY COLUMN transaction_type 
        ENUM('REGISTER','LOGIN','TASK','PURCHASE','REFUND','ADMIN_ADJUST','GIFT','ACTIVITY','IMAGE_GENERATION','DEEPSEEK_CHAT','PAYMENT_REWARD')
        """
        
        db.execute(text(sql))
        db.commit()
        print('✅ 数据库表结构更新成功，已添加 PAYMENT_REWARD 枚举值')
        
    except Exception as e:
        print(f'❌ 更新失败: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_enum()