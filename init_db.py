#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建数据库表和初始超级用户
"""

import sys
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from database import Base, SessionLocal
from models import User
from auth import get_password_hash
from config import settings

def create_tables():
    """创建数据库表"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功")
        return True
    except SQLAlchemyError as e:
        print(f"❌ 数据库表创建失败: {e}")
        return False

def create_superuser():
    """创建初始超级用户"""
    db = SessionLocal()
    try:
        # 检查是否已存在超级用户
        existing_superuser = db.query(User).filter(User.is_superuser == True).first()
        if existing_superuser:
            print("ℹ️  超级用户已存在，跳过创建")
            return True
        
        # 创建超级用户
        print("创建初始超级用户...")
        username = input("请输入超级用户用户名 (默认: admin): ").strip() or "admin"
        email = input("请输入超级用户邮箱 (默认: admin@example.com): ").strip() or "admin@example.com"
        
        while True:
            password = input("请输入超级用户密码 (至少6位): ").strip()
            if len(password) >= 6:
                break
            print("❌ 密码长度至少为6位，请重新输入")
        
        # 检查用户名和邮箱是否已存在
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print("❌ 用户名或邮箱已存在")
            return False
        
        # 创建超级用户
        superuser = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            full_name="系统管理员",
            is_active=True,
            is_superuser=True
        )
        
        db.add(superuser)
        db.commit()
        print(f"✅ 超级用户 '{username}' 创建成功")
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ 创建超级用户失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """主函数"""
    print("🚀 开始初始化数据库...")
    print(f"📊 数据库连接: {settings.DATABASE_URL}")
    
    # 创建数据库表
    if not create_tables():
        sys.exit(1)
    
    # 创建超级用户
    create_superuser_choice = input("\n是否创建初始超级用户? (y/n, 默认: y): ").strip().lower()
    if create_superuser_choice in ['', 'y', 'yes']:
        if not create_superuser():
            print("⚠️  超级用户创建失败，但数据库表已创建成功")
    
    print("\n🎉 数据库初始化完成!")
    print("\n📖 使用说明:")
    print("1. 运行应用: python main.py")
    print("2. 访问API文档: http://localhost:8000/docs")
    print("3. 使用创建的超级用户登录")

if __name__ == "__main__":
    main() 