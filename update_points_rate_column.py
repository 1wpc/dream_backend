#!/usr/bin/env python3
"""
更新 orders 表的 points_rate 字段类型
将 decimal(5,4) 改为 decimal(10,2) 以支持更大的积分奖励率
"""

from database import SessionLocal
from sqlalchemy import text

def update_points_rate_column():
    """更新 points_rate 字段类型"""
    db = SessionLocal()
    try:
        print("🔧 开始更新 points_rate 字段类型...")
        
        # 修改字段类型
        sql = "ALTER TABLE orders MODIFY COLUMN points_rate DECIMAL(10,2) NOT NULL DEFAULT 10.00 COMMENT '积分奖励比例'"
        
        db.execute(text(sql))
        db.commit()
        
        print("✅ points_rate 字段类型更新成功")
        
        # 验证更新结果
        result = db.execute(text("DESCRIBE orders"))
        for row in result.fetchall():
            if row[0] == 'points_rate':
                print(f"   新的字段类型: {row[1]}")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ 更新字段类型失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if update_points_rate_column():
        print("\n🎉 数据库表结构更新完成！")
        print("💡 现在可以支持更大的积分奖励率值")
    else:
        print("\n❌ 数据库表结构更新失败！")
        exit(1)