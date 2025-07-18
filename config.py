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
    IMAGE_GENERATION_COST: int = 5  # 每次生成图片消耗的积分
    VOLCANO_ENGINE_ACCESS_KEY: str = "your_volcano_access_key_here"
    VOLCANO_ENGINE_SECRET_KEY: str = "your_volcano_secret_key_here"
    VOLCANO_ENGINE_REGION: str = "cn-north-1"
    VOLCANO_ENGINE_SERVICE_NAME: str = "cv"
    
    # DeepSeek API 配置
    DEEPSEEK_API_KEY: str = "your_deepseek_api_key_here"
    DEEPSEEK_CHAT_COST: int = 1 # 每次聊天的积分消耗
    
    # 支付宝配置
    ALIPAY_APP_ID: str = "your_alipay_app_id_here"
    ALIPAY_APP_PRIVATE_KEY: str = "your_alipay_app_private_key_here"
    ALIPAY_PUBLIC_KEY: str = "your_alipay_public_key_here"
    ALIPAY_SELLER_ID: str = "your_alipay_seller_id_here"
    ALIPAY_NOTIFY_URL: str = "https://your-domain.com/api/v1/payment/notify"  # 异步通知地址
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # 邮箱验证配置
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 5  # 验证码有效期（分钟）
    TENCENTCLOUD_SECRET_ID: str = "your_tencentcloud_secret_id_here"
    TENCENTCLOUD_SECRET_KEY: str = "your_tencentcloud_secret_key_here"
    TENCENTCLOUD_SES_REGION: str = "ap-hongkong"
    TENCENTCLOUD_SES_FROM_EMAIL: str = "mijiutech@bot.mijiu.ltd"
    TENCENTCLOUD_SES_TEMPLATE_ID: int = 144111
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    class Config:
        env_file = ".env"

settings = Settings()