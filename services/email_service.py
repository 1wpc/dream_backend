# -*- coding: utf-8 -*-
"""
邮箱验证服务
使用腾讯云SES发送验证码邮件，Redis缓存验证码
"""

import os
import json
import random
import string
from datetime import datetime, timedelta
from typing import Optional

import redis
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ses.v20201002 import ses_client, models

from config import settings

class EmailService:
    """邮箱验证服务"""
    
    def __init__(self):
        # 尝试初始化Redis连接，如果失败则使用内存缓存
        self.use_redis = True
        self.memory_cache = {}  # 内存缓存备选方案
        
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
            print("✅ Redis连接成功")
        except Exception as e:
            print(f"⚠️ Redis连接失败，使用内存缓存: {e}")
            self.use_redis = False
            self.redis_client = None
        
        # 初始化腾讯云SES客户端
        try:
            cred = credential.Credential(
                settings.TENCENTCLOUD_SECRET_ID,
                settings.TENCENTCLOUD_SECRET_KEY
            )
            
            http_profile = HttpProfile()
            http_profile.endpoint = "ses.tencentcloudapi.com"
            
            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile
            
            self.ses_client = ses_client.SesClient(
                cred, 
                settings.TENCENTCLOUD_SES_REGION, 
                client_profile
            )
        except Exception as e:
            print(f"❌ 初始化腾讯云SES客户端失败: {e}")
            self.ses_client = None
    
    def generate_verification_code(self, length: int = 6) -> str:
        """生成验证码"""
        return ''.join(random.choices(string.digits, k=length))
    
    def _get_cache_key(self, email: str, action: str = "register") -> str:
        """获取缓存键名"""
        return f"email_verification:{action}:{email}"
    
    def _set_cache(self, key: str, value: str, expire_seconds: int) -> bool:
        """设置缓存"""
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.setex(key, expire_seconds, value)
            else:
                # 使用内存缓存
                import time
                expire_time = time.time() + expire_seconds
                self.memory_cache[key] = {
                    'value': value,
                    'expire_time': expire_time
                }
            return True
        except Exception as e:
            print(f"❌ 设置缓存失败: {e}")
            return False
    
    def _get_cache(self, key: str) -> Optional[str]:
        """获取缓存"""
        try:
            if self.use_redis and self.redis_client:
                return self.redis_client.get(key)
            else:
                # 使用内存缓存
                import time
                if key in self.memory_cache:
                    cache_item = self.memory_cache[key]
                    if time.time() < cache_item['expire_time']:
                        return cache_item['value']
                    else:
                        # 过期，删除
                        del self.memory_cache[key]
                return None
        except Exception as e:
            print(f"❌ 获取缓存失败: {e}")
            return None
    
    def _delete_cache(self, key: str) -> bool:
        """删除缓存"""
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.delete(key)
            else:
                # 使用内存缓存
                if key in self.memory_cache:
                    del self.memory_cache[key]
            return True
        except Exception as e:
            print(f"❌ 删除缓存失败: {e}")
            return False
    
    def _get_cache_ttl(self, key: str) -> int:
        """获取缓存剩余时间"""
        try:
            if self.use_redis and self.redis_client:
                return self.redis_client.ttl(key)
            else:
                # 使用内存缓存
                import time
                if key in self.memory_cache:
                    cache_item = self.memory_cache[key]
                    remaining = cache_item['expire_time'] - time.time()
                    return int(remaining) if remaining > 0 else -1
                return -1
        except Exception as e:
            print(f"❌ 获取缓存TTL失败: {e}")
            return -1
    
    def send_verification_code(self, email: str, action: str = "register") -> dict:
        """发送验证码邮件"""
        try:
            # 生成验证码
            code = self.generate_verification_code()
            
            # 检查是否频繁发送（1分钟内只能发送一次）
            cache_key = self._get_cache_key(email, action.lower())
            existing_code = self._get_cache(cache_key)
            if existing_code:
                ttl = self._get_cache_ttl(cache_key)
                if ttl > 240:  # 如果还有超过4分钟的有效期，说明刚发送过
                    return {
                        "success": False,
                        "message": "验证码发送过于频繁，请稍后再试",
                        "code": "RATE_LIMIT"
                    }
            
            # 准备邮件模板数据
            current_time = datetime.now()
            # 将action转换为中文显示
            action_display = "注册" if action.lower() == "register" else action
            template_data = {
                "code": code,
                "action": action_display,
                "time": settings.EMAIL_VERIFICATION_EXPIRE_MINUTES,
                "date": current_time.strftime("%Y.%m.%d")
            }
            
            # 发送邮件
            if self.ses_client:
                req = models.SendEmailRequest()
                params = {
                    "FromEmailAddress": settings.TENCENTCLOUD_SES_FROM_EMAIL,
                    "Destination": [email],
                    "Subject": "验证码",
                    "Template": {
                        "TemplateID": settings.TENCENTCLOUD_SES_TEMPLATE_ID,
                        "TemplateData": json.dumps(template_data)
                    }
                }
                req.from_json_string(json.dumps(params))
                
                resp = self.ses_client.SendEmail(req)
                print(f"✅ 邮件发送成功: {resp.to_json_string()}")
            else:
                print(f"⚠️ SES客户端未初始化，模拟发送验证码: {code} 到 {email}")
            
            # 将验证码存储到缓存，设置过期时间
            expire_seconds = settings.EMAIL_VERIFICATION_EXPIRE_MINUTES * 60
            if not self._set_cache(cache_key, code, expire_seconds):
                return {
                    "success": False,
                    "message": "缓存设置失败，请稍后重试",
                    "code": "CACHE_ERROR"
                }
            
            return {
                "success": True,
                "message": f"验证码已发送到 {email}，请在{settings.EMAIL_VERIFICATION_EXPIRE_MINUTES}分钟内使用",
                "code": "SUCCESS"
            }
            
        except TencentCloudSDKException as e:
            print(f"❌ 腾讯云SES发送邮件失败: {e}")
            return {
                "success": False,
                "message": "邮件发送失败，请稍后重试",
                "code": "SES_ERROR"
            }
        except Exception as e:
            print(f"❌ 发送验证码失败: {e}")
            return {
                "success": False,
                "message": "系统错误，请稍后重试",
                "code": "SYSTEM_ERROR"
            }
    
    def verify_code(self, email: str, code: str, action: str = "register") -> dict:
        """验证验证码"""
        try:
            cache_key = self._get_cache_key(email, action.lower())
            stored_code = self._get_cache(cache_key)
            
            if not stored_code:
                return {
                    "success": False,
                    "message": "验证码已过期或不存在",
                    "code": "CODE_EXPIRED"
                }
            
            if stored_code != code:
                return {
                    "success": False,
                    "message": "验证码错误",
                    "code": "CODE_INVALID"
                }
            
            # 验证成功，删除验证码
            self._delete_cache(cache_key)
            
            return {
                "success": True,
                "message": "验证码验证成功",
                "code": "SUCCESS"
            }
            
        except Exception as e:
            print(f"❌ 验证验证码失败: {e}")
            return {
                "success": False,
                "message": "系统错误，请稍后重试",
                "code": "SYSTEM_ERROR"
            }
    
    def get_code_ttl(self, email: str, action: str = "register") -> int:
        """获取验证码剩余有效时间（秒）"""
        try:
            cache_key = self._get_cache_key(email, action.lower())
            return self._get_cache_ttl(cache_key)
        except Exception:
            return -1
    


# 创建全局邮箱服务实例
email_service = EmailService()