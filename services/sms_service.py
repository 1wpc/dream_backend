# -*- coding: utf-8 -*-
"""
短信验证码服务
基于阿里云短信服务实现
"""

import random
import redis
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
from alibabacloud_dysmsapi20170525.client import Client as DysmsapiClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_models
from alibabacloud_tea_util.client import Client as UtilClient
from config import settings

class SMSService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=0,
            decode_responses=True
        )
        self.client = self._create_client()
    
    def _create_client(self) -> DysmsapiClient:
        """
        创建阿里云短信客户端
        """
        config = open_api_models.Config()
        config.access_key_id = settings.ALIYUN_ACCESS_KEY_ID
        config.access_key_secret = settings.ALIYUN_ACCESS_KEY_SECRET
        config.endpoint = 'dysmsapi.aliyuncs.com'
        return DysmsapiClient(config)
    
    def generate_code(self) -> str:
        """
        生成6位数字验证码
        """
        return str(random.randint(100000, 999999))
    
    def send_verification_code(self, phone: str, action: str = "register") -> Dict[str, any]:
        """
        发送短信验证码
        
        Args:
            phone: 手机号
            action: 操作类型 (register/login/reset_password)
        
        Returns:
            Dict: 发送结果
        """
        try:
            # 检查发送频率限制（60秒内只能发送一次）
            rate_limit_key = f"sms_rate_limit:{phone}"
            if self.redis_client.exists(rate_limit_key):
                return {
                    "success": False,
                    "message": "发送过于频繁，请60秒后再试",
                    "code": ""
                }
            
            # 生成验证码
            code = self.generate_code()
            
            # 构建短信请求
            send_req = dysmsapi_models.SendSmsRequest(
                phone_numbers=phone,
                sign_name=settings.SMS_SIGN_NAME,  # 短信签名
                template_code=settings.SMS_TEMPLATE_CODE,  # 短信模板代码
                template_param=json.dumps({"code": code})  # 模板参数
            )
            
            # 发送短信
            send_resp = self.client.send_sms(send_req)
            
            if not UtilClient.equal_string(send_resp.body.code, 'OK'):
                return {
                    "success": False,
                    "message": f"短信发送失败: {send_resp.body.message}",
                    "code": ""
                }
            
            # 存储验证码到Redis（5分钟有效期）
            verification_key = f"sms_verification:{phone}:{action}"
            verification_data = {
                "code": code,
                "phone": phone,
                "action": action,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(minutes=5)).isoformat()
            }
            
            self.redis_client.setex(
                verification_key,
                300,  # 5分钟过期
                json.dumps(verification_data)
            )
            
            # 设置发送频率限制（60秒）
            self.redis_client.setex(rate_limit_key, 60, "1")
            
            return {
                "success": True,
                "message": "短信验证码发送成功",
                "code": code if settings.DEBUG else ""  # 调试模式下返回验证码
            }
            
        except Exception as e:
            print(f"短信发送异常: {e}")
            return {
                "success": False,
                "message": "短信发送失败，请稍后重试",
                "code": ""
            }
    
    def verify_code(self, phone: str, code: str, action: str = "register") -> Dict[str, any]:
        """
        验证短信验证码
        
        Args:
            phone: 手机号
            code: 验证码
            action: 操作类型
        
        Returns:
            Dict: 验证结果
        """
        try:
            verification_key = f"sms_verification:{phone}:{action}"
            stored_data = self.redis_client.get(verification_key)
            
            if not stored_data:
                return {
                    "success": False,
                    "message": "验证码不存在或已过期"
                }
            
            verification_data = json.loads(stored_data)
            stored_code = verification_data.get("code")
            
            if stored_code != code:
                return {
                    "success": False,
                    "message": "验证码错误"
                }
            
            # 验证成功后删除验证码
            self.redis_client.delete(verification_key)
            
            return {
                "success": True,
                "message": "验证码验证成功"
            }
            
        except Exception as e:
            print(f"验证码验证异常: {e}")
            return {
                "success": False,
                "message": "验证码验证失败"
            }
    
    def cleanup_expired_codes(self):
        """
        清理过期的验证码（可选的定时任务）
        """
        try:
            # Redis的TTL机制会自动清理过期数据，这里可以添加额外的清理逻辑
            pass
        except Exception as e:
            print(f"清理过期验证码异常: {e}")

# 创建全局短信服务实例
sms_service = SMSService()