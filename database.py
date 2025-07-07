from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
import pymysql
from config import settings

def create_database_if_not_exists():
    """如果数据库不存在则创建数据库"""
    try:
        # 连接到MySQL服务器（不指定数据库）
        server_url = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/"
        temp_engine = create_engine(server_url)
        
        with temp_engine.connect() as conn:
            # 检查数据库是否存在
            result = conn.execute(text(f"SHOW DATABASES LIKE '{settings.MYSQL_DATABASE}'"))
            if not result.fetchone():
                # 创建数据库
                conn.execute(text(f"CREATE DATABASE {settings.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                conn.commit()
                print(f"✅ 数据库 '{settings.MYSQL_DATABASE}' 创建成功")
            else:
                print(f"ℹ️  数据库 '{settings.MYSQL_DATABASE}' 已存在")
                
    except Exception as e:
        print(f"❌ 创建数据库时发生错误: {e}")
        raise

# 先尝试创建数据库
create_database_if_not_exists()

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,  # 在开发环境中打印SQL语句
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 获取数据库会话的依赖函数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 