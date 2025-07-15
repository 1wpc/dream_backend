#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
支付宝密钥格式验证工具

使用方法：
1. 直接运行脚本，会读取 .env 文件中的密钥进行验证
2. 或者修改脚本中的密钥字符串进行验证
"""

import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dotenv import load_dotenv

def format_private_key(private_key: str) -> str:
    """
    格式化私钥，确保包含正确的头尾标识
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

def format_public_key(public_key: str) -> str:
    """
    格式化公钥，确保包含正确的头尾标识
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

def validate_private_key(private_key_str: str) -> bool:
    """
    验证私钥格式是否正确
    """
    try:
        # 尝试格式化私钥
        formatted_key = format_private_key(private_key_str)
        
        # 尝试加载私钥
        private_key = serialization.load_pem_private_key(
            formatted_key.encode(),
            password=None
        )
        
        # 检查是否为RSA私钥
        if isinstance(private_key, rsa.RSAPrivateKey):
            print("✅ 私钥格式正确，是有效的RSA私钥")
            print(f"   密钥长度: {private_key.key_size} bits")
            return True
        else:
            print("❌ 私钥不是RSA格式")
            return False
            
    except Exception as e:
        print(f"❌ 私钥格式错误: {e}")
        return False

def validate_public_key(public_key_str: str) -> bool:
    """
    验证公钥格式是否正确
    """
    try:
        # 尝试格式化公钥
        formatted_key = format_public_key(public_key_str)
        
        # 尝试加载公钥
        public_key = serialization.load_pem_public_key(
            formatted_key.encode()
        )
        
        # 检查是否为RSA公钥
        if isinstance(public_key, rsa.RSAPublicKey):
            print("✅ 公钥格式正确，是有效的RSA公钥")
            print(f"   密钥长度: {public_key.key_size} bits")
            return True
        else:
            print("❌ 公钥不是RSA格式")
            return False
            
    except Exception as e:
        print(f"❌ 公钥格式错误: {e}")
        return False

def main():
    """
    主函数：验证支付宝密钥配置
    """
    print("=" * 50)
    print("支付宝密钥格式验证工具")
    print("=" * 50)
    
    # 加载环境变量
    load_dotenv()
    
    # 获取配置
    app_id = os.getenv('ALIPAY_APP_ID', '')
    app_private_key = os.getenv('ALIPAY_APP_PRIVATE_KEY', '')
    alipay_public_key = os.getenv('ALIPAY_PUBLIC_KEY', '')
    seller_id = os.getenv('ALIPAY_SELLER_ID', '')
    
    print(f"\n📋 配置信息:")
    print(f"   APP ID: {app_id[:10]}..." if app_id else "   APP ID: 未配置")
    print(f"   卖家ID: {seller_id[:10]}..." if seller_id else "   卖家ID: 未配置")
    
    # 验证应用私钥
    print(f"\n🔐 验证应用私钥:")
    if app_private_key:
        if app_private_key == 'your_alipay_app_private_key_here':
            print("❌ 请配置真实的应用私钥")
        else:
            validate_private_key(app_private_key)
    else:
        print("❌ 应用私钥未配置")
    
    # 验证支付宝公钥
    print(f"\n🔑 验证支付宝公钥:")
    if alipay_public_key:
        if alipay_public_key == 'your_alipay_public_key_here':
            print("❌ 请配置真实的支付宝公钥")
        else:
            validate_public_key(alipay_public_key)
    else:
        print("❌ 支付宝公钥未配置")
    
    print(f"\n💡 提示:")
    print(f"   1. 确保在 .env 文件中正确配置了所有支付宝参数")
    print(f"   2. 私钥和公钥必须是从支付宝开放平台获取的")
    print(f"   3. 如果验证失败，请检查密钥格式是否正确")
    print(f"   4. 参考 alipay_error_troubleshooting.md 获取更多帮助")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        if "cryptography" in str(e):
            print("❌ 缺少 cryptography 库，请安装:")
            print("   pip install cryptography")
        elif "dotenv" in str(e):
            print("❌ 缺少 python-dotenv 库，请安装:")
            print("   pip install python-dotenv")
        else:
            print(f"❌ 导入错误: {e}")
    except Exception as e:
        print(f"❌ 运行错误: {e}")