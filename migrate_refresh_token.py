#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加refresh token相关字段
用于为User表添加refresh_token、refresh_token_expires_at和last_active_at字段
"""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config import settings

def migrate_database():
    """执行数据库迁移"""
    try:
        # 创建数据库引擎
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as connection:
            # 开始事务
            trans = connection.begin()
            
            try:
                print("开始数据库迁移...")
                
                # 添加refresh_token字段
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN refresh_token TEXT NULL
                """))
                print("✓ 添加refresh_token字段")
                
                # 添加refresh_token_expires_at字段
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN refresh_token_expires_at DATETIME NULL
                """))
                print("✓ 添加refresh_token_expires_at字段")
                
                # 添加last_active_at字段
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN last_active_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP
                """))
                print("✓ 添加last_active_at字段")
                
                # 为现有用户设置last_active_at为当前时间
                connection.execute(text("""
                    UPDATE users 
                    SET last_active_at = CURRENT_TIMESTAMP 
                    WHERE last_active_at IS NULL
                """))
                print("✓ 更新现有用户的last_active_at字段")
                
                # 提交事务
                trans.commit()
                print("\n数据库迁移完成！")
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                raise e
                
    except SQLAlchemyError as e:
        print(f"数据库迁移失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"迁移过程中发生错误: {e}")
        sys.exit(1)

def check_migration_needed():
    """检查是否需要迁移"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as connection:
            # 检查refresh_token字段是否存在
            result = connection.execute(text("""
                SELECT COUNT(*) as count
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'refresh_token'
            """))
            
            count = result.fetchone()[0]
            return count == 0
            
    except Exception as e:
        print(f"检查迁移状态失败: {e}")
        return True  # 如果检查失败，假设需要迁移

if __name__ == "__main__":
    print("=== 数据库迁移工具 - Refresh Token 字段 ===")
    print(f"数据库URL: {settings.DATABASE_URL}")
    
    if check_migration_needed():
        print("检测到需要迁移，开始执行...")
        migrate_database()
    else:
        print("数据库已经是最新版本，无需迁移。")