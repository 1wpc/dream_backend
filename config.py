from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # 数据库配置
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "dream_backend"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API配置
    API_VERSION: str = "v1"
    PROJECT_NAME: str = "Dream Backend"
    DEBUG: bool = True
    
    # 图片生成服务配置
    IMAGE_GENERATION_COST: int = 50  # 每次生成图片消耗的积分
    VOLCANO_ENGINE_ACCESS_KEY: str = "your_volcano_access_key_here"
    VOLCANO_ENGINE_SECRET_KEY: str = "your_volcano_secret_key_here"
    VOLCANO_ENGINE_REGION: str = "cn-north-1"
    VOLCANO_ENGINE_SERVICE_NAME: str = "cv"
    
    # DeepSeek API 配置
    DEEPSEEK_API_KEY: str = "your_deepseek_api_key_here"
    DEEPSEEK_CHAT_COST: int = 1 # 每次聊天的积分消耗
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    class Config:
        env_file = ".env"

settings = Settings() 