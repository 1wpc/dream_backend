#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import traceback
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradeAppPayModel import AlipayTradeAppPayModel
from alipay.aop.api.request.AlipayTradeAppPayRequest import AlipayTradeAppPayRequest
from alipay.aop.api.util.SignatureUtils import verify_with_rsa
import urllib.parse

from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    filemode='a',
)
logger = logging.getLogger(__name__)

class AlipayService:
    """支付宝支付服务"""
    
    def __init__(self):
        """初始化支付宝客户端"""
        # 支付宝客户端配置
        alipay_client_config = AlipayClientConfig()
        alipay_client_config.server_url = 'https://openapi.alipay.com/gateway.do'  # 正式环境
        # alipay_client_config.server_url = 'https://openapi.alipaydev.com/gateway.do'  # 沙箱环境
        alipay_client_config.app_id = settings.ALIPAY_APP_ID
        
        # 处理私钥格式
        app_private_key = self._format_private_key(settings.ALIPAY_APP_PRIVATE_KEY)
        alipay_public_key = self._format_public_key(settings.ALIPAY_PUBLIC_KEY)
        
        alipay_client_config.app_private_key = app_private_key
        alipay_client_config.alipay_public_key = alipay_public_key
        alipay_client_config.sign_type = 'RSA2'
        
        # 创建客户端实例
        self.client = DefaultAlipayClient(alipay_client_config=alipay_client_config)
    
    def create_app_pay_order(self, 
                           subject: str, 
                           body: str, 
                           total_amount: Decimal,
                           out_trade_no: Optional[str] = None) -> tuple[str, str]:
        """
        创建APP支付订单
        
        Args:
            subject: 商品标题
            body: 商品描述
            total_amount: 支付金额
            out_trade_no: 商户订单号，如果不提供会自动生成
            
        Returns:
            tuple[str, str]: (支付宝订单字符串, 商户订单号)
            
        Raises:
            Exception: 创建订单失败时抛出异常
        """
        try:
            # 如果没有提供订单号，自动生成
            if not out_trade_no:
                out_trade_no = self._generate_order_no()
            
            # 构造请求参数
            model = AlipayTradeAppPayModel()
            model.timeout_express = "30m"  # 订单超时时间
            model.total_amount = str(total_amount)  # 支付金额
            model.seller_id = settings.ALIPAY_SELLER_ID  # 卖家支付宝用户ID
            model.product_code = "QUICK_MSECURITY_PAY"  # 产品码，固定值
            model.body = body  # 商品描述
            model.subject = subject  # 商品标题
            model.out_trade_no = out_trade_no  # 商户订单号
            
            # 创建请求对象
            request = AlipayTradeAppPayRequest(biz_model=model)
            
            # 设置异步通知URL
            if settings.ALIPAY_NOTIFY_URL:
                request.notify_url = settings.ALIPAY_NOTIFY_URL
                logger.info(f"设置异步通知URL: {settings.ALIPAY_NOTIFY_URL}")
            
            # 执行请求，获取订单字符串
            response = self.client.sdk_execute(request)
            
            logger.info(f"支付宝订单创建成功: {out_trade_no}")
            return response, out_trade_no
            
        except Exception as e:
            logger.error(f"创建支付宝订单失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise Exception(f"创建支付订单失败: {str(e)}")
    
    def _generate_order_no(self) -> str:
        """
        生成商户订单号
        格式: 时间戳 + UUID后8位
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        uuid_suffix = str(uuid.uuid4()).replace('-', '')[-8:]
        return f"{timestamp}{uuid_suffix}"
    
    def _format_private_key(self, private_key: str) -> str:
        """
        格式化私钥，确保包含正确的头尾标识
        
        Args:
            private_key: 原始私钥字符串
            
        Returns:
            str: 格式化后的私钥
        """
        # 移除所有空白字符和换行符
        key = private_key.strip().replace('\n', '').replace('\r', '').replace(' ', '')
        
        # 移除可能存在的头尾标识
        key = key.replace('-----BEGIN RSA PRIVATE KEY-----', '')
        key = key.replace('-----END RSA PRIVATE KEY-----', '')
        key = key.replace('-----BEGIN PRIVATE KEY-----', '')
        key = key.replace('-----END PRIVATE KEY-----', '')
        
        # 添加正确的头尾标识和换行符
        formatted_key = f"-----BEGIN RSA PRIVATE KEY-----\n"
        # 每64个字符添加一个换行符
        for i in range(0, len(key), 64):
            formatted_key += key[i:i+64] + "\n"
        formatted_key += "-----END RSA PRIVATE KEY-----"
        
        return formatted_key
    
    def _format_public_key(self, public_key: str) -> str:
        """
        格式化公钥，确保包含正确的头尾标识
        
        Args:
            public_key: 原始公钥字符串
            
        Returns:
            str: 格式化后的公钥
        """
        # 移除所有空白字符和换行符
        key = public_key.strip().replace('\n', '').replace('\r', '').replace(' ', '')
        
        # 移除可能存在的头尾标识
        key = key.replace('-----BEGIN PUBLIC KEY-----', '')
        key = key.replace('-----END PUBLIC KEY-----', '')
        
        # 添加正确的头尾标识和换行符
        formatted_key = f"-----BEGIN PUBLIC KEY-----\n"
        # 每64个字符添加一个换行符
        for i in range(0, len(key), 64):
            formatted_key += key[i:i+64] + "\n"
        formatted_key += "-----END PUBLIC KEY-----"
        
        return formatted_key
    
    def verify_notify(self, post_data: dict) -> bool:
        """
        验证支付宝异步通知签名
        
        Args:
            post_data: 支付宝POST过来的数据
            
        Returns:
            bool: 验证结果
        """
        try:
            # 获取签名
            sign = post_data.get('sign')
            if not sign:
                logger.error("异步通知中缺少签名")
                return False
            
            # 移除sign和sign_type参数
            params = {k: v for k, v in post_data.items() if k not in ['sign', 'sign_type']}
            
            # 构造待签名字符串
            sign_content = self._build_sign_content(params)
            
            # 验证签名
            alipay_public_key = self._format_public_key(settings.ALIPAY_PUBLIC_KEY)
            is_valid = verify_with_rsa(alipay_public_key, sign_content, sign, 'utf-8')
            
            if is_valid:
                logger.info("支付宝异步通知签名验证成功")
            else:
                logger.error("支付宝异步通知签名验证失败")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"验证支付宝通知签名失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _build_sign_content(self, params: dict) -> str:
        """
        构造待签名字符串
        
        Args:
            params: 参数字典
            
        Returns:
            str: 待签名字符串
        """
        # 过滤空值参数
        filtered_params = {k: v for k, v in params.items() if v is not None and v != ''}
        
        # 按参数名ASCII码从小到大排序
        sorted_params = sorted(filtered_params.items())
        
        # 构造待签名字符串
        sign_content = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        logger.debug(f"待签名字符串: {sign_content}")
        return sign_content
    
    def validate_notify_params(self, post_data: dict) -> tuple[bool, str]:
        """
        验证异步通知参数的完整性和有效性
        
        Args:
            post_data: 支付宝POST过来的数据
            
        Returns:
            tuple[bool, str]: (验证结果, 错误信息)
        """
        try:
            # 检查必要参数
            required_params = [
                'notify_time', 'notify_type', 'notify_id', 'app_id',
                'trade_no', 'out_trade_no', 'trade_status', 'total_amount'
            ]
            
            missing_params = []
            for param in required_params:
                if param not in post_data or not post_data[param]:
                    missing_params.append(param)
            
            if missing_params:
                error_msg = f"缺少必要参数: {', '.join(missing_params)}"
                logger.error(error_msg)
                return False, error_msg
            
            # 验证app_id
            if post_data.get('app_id') != settings.ALIPAY_APP_ID:
                error_msg = f"app_id不匹配: 期望={settings.ALIPAY_APP_ID}, 实际={post_data.get('app_id')}"
                logger.error(error_msg)
                return False, error_msg
            
            # 验证通知类型
            if post_data.get('notify_type') != 'trade_status_sync':
                error_msg = f"不支持的通知类型: {post_data.get('notify_type')}"
                logger.error(error_msg)
                return False, error_msg
            
            return True, ""
            
        except Exception as e:
            error_msg = f"验证通知参数失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

# 创建全局实例
alipay_service = AlipayService()