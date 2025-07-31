#!/usr/bin/env python3
"""
数据库迁移脚本：将用户表的email字段改为可空

使用方法：
1. 确保数据库连接正常
2. 运行此脚本：python migration_email_nullable.py
3. 脚本会自动备份现有数据并执行迁移
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings

def migrate_email_nullable():
    """将email字段改为可空"""
    
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # 开始事务
            trans = connection.begin()
            
            try:
                print(f"[{datetime.now()}] 开始数据库迁移：将email字段改为可空")
                
                # 1. 检查当前表结构
                print("[INFO] 检查当前表结构...")
                result = connection.execute(text("""
                    SELECT COLUMN_NAME, IS_NULLABLE, DATA_TYPE 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'email'
                """))
                
                current_structure = result.fetchone()
                if current_structure:
                    print(f"[INFO] 当前email字段结构: {current_structure}")
                    
                    if current_structure[1] == 'YES':
                        print("[INFO] email字段已经是可空的，无需迁移")
                        return True
                else:
                    print("[ERROR] 未找到email字段")
                    return False
                
                # 2. 备份当前有默认邮箱的用户数据
                print("[INFO] 检查是否有使用默认邮箱的用户...")
                result = connection.execute(text("""
                    SELECT COUNT(*) FROM users WHERE email = 'default@default.com'
                """))
                default_email_count = result.scalar()
                print(f"[INFO] 发现 {default_email_count} 个使用默认邮箱的用户")
                
                # 3. 删除email字段的唯一索引（如果存在）
                print("[INFO] 检查并删除email字段的唯一约束...")
                
                # 查找email字段的唯一约束
                result = connection.execute(text("""
                    SELECT CONSTRAINT_NAME 
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                    WHERE TABLE_NAME = 'users' 
                    AND COLUMN_NAME = 'email' 
                    AND CONSTRAINT_NAME != 'PRIMARY'
                """))
                
                constraints = result.fetchall()
                for constraint in constraints:
                    constraint_name = constraint[0]
                    print(f"[INFO] 删除约束: {constraint_name}")
                    connection.execute(text(f"ALTER TABLE users DROP INDEX {constraint_name}"))
                
                # 4. 将默认邮箱设置为NULL
                if default_email_count > 0:
                    print("[INFO] 将默认邮箱用户的email字段设置为NULL...")
                    connection.execute(text("""
                        UPDATE users SET email = NULL WHERE email = 'default@default.com'
                    """))
                    print(f"[INFO] 已更新 {default_email_count} 个用户的邮箱为NULL")
                
                # 5. 修改字段为可空
                print("[INFO] 修改email字段为可空...")
                connection.execute(text("""
                    ALTER TABLE users MODIFY COLUMN email VARCHAR(100) NULL COMMENT '邮箱'
                """))
                
                # 6. 重新创建唯一索引（允许NULL值）
                print("[INFO] 重新创建email字段的唯一索引...")
                connection.execute(text("""
                    CREATE UNIQUE INDEX ix_users_email ON users (email)
                """))
                
                # 7. 验证迁移结果
                print("[INFO] 验证迁移结果...")
                result = connection.execute(text("""
                    SELECT COLUMN_NAME, IS_NULLABLE, DATA_TYPE 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'email'
                """))
                
                new_structure = result.fetchone()
                if new_structure and new_structure[1] == 'YES':
                    print(f"[SUCCESS] 迁移成功！新的email字段结构: {new_structure}")
                else:
                    raise Exception("迁移验证失败")
                
                # 提交事务
                trans.commit()
                print(f"[{datetime.now()}] 数据库迁移完成！")
                return True
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"[ERROR] 迁移失败，已回滚: {str(e)}")
                return False
                
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("数据库迁移脚本：将email字段改为可空")
    print("=" * 60)
    
    # 确认执行
    confirm = input("确认执行迁移？这将修改数据库结构。(y/N): ")
    if confirm.lower() != 'y':
        print("迁移已取消")
        sys.exit(0)
    
    # 执行迁移
    success = migrate_email_nullable()
    
    if success:
        print("\n✅ 迁移成功完成！")
        print("现在用户可以在短信注册时不提供邮箱，email字段将为NULL")
    else:
        print("\n❌ 迁移失败！")
        sys.exit(1)