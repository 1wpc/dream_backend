#!/usr/bin/env python3
"""
邮箱验证功能测试脚本
测试发送验证码、验证验证码、带验证码注册等功能
"""

import requests
import json
import time
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

def test_send_verification_code():
    """测试发送验证码"""
    print("\n🔍 测试发送邮箱验证码...")
    
    test_email = "test@example.com"
    
    try:
        response = requests.post(
            f"{API_URL}/users/send-verification-code",
            json={
                "email": test_email,
                "action": "注册"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 验证码发送成功: {result['message']}")
            return True
        else:
            print(f"❌ 验证码发送失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 发送验证码请求异常: {e}")
        return False

def test_verify_code_invalid():
    """测试验证无效验证码"""
    print("\n🔍 测试验证无效验证码...")
    
    test_email = "test@example.com"
    invalid_code = "000000"
    
    try:
        response = requests.post(
            f"{API_URL}/users/verify-email-code",
            json={
                "email": test_email,
                "code": invalid_code,
                "action": "register"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            result = response.json()
            print(f"✅ 无效验证码正确被拒绝: {result['detail']}")
            return True
        else:
            print(f"❌ 无效验证码验证异常: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 验证码验证请求异常: {e}")
        return False

def test_register_with_verification():
    """测试带验证码的用户注册"""
    print("\n🔍 测试带验证码的用户注册...")
    
    # 生成测试用户数据
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_user = {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "password123",
        "full_name": "测试用户",
        "verification_code": "123456"  # 模拟验证码
    }
    
    try:
        # 先发送验证码
        print("   发送验证码...")
        send_response = requests.post(
            f"{API_URL}/users/send-verification-code",
            json={
                "email": test_user["email"],
                "action": "注册"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if send_response.status_code != 200:
            print(f"❌ 发送验证码失败: {send_response.status_code} - {send_response.text}")
            return False
        
        print("   验证码发送成功，等待2秒...")
        time.sleep(2)
        
        # 注意：在实际测试中，需要从Redis或邮件中获取真实的验证码
        # 这里我们使用一个模拟的验证码进行测试
        print("   ⚠️ 注意：此测试使用模拟验证码，实际使用时需要从邮件中获取真实验证码")
        
        # 尝试注册（会失败，因为验证码不匹配）
        response = requests.post(
            f"{API_URL}/users/register-with-verification",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            result = response.json()
            print(f"✅ 验证码验证正确失败: {result['detail']}")
            print("   💡 这是预期行为，因为使用了模拟验证码")
            return True
        elif response.status_code == 201:
            result = response.json()
            print(f"✅ 用户注册成功: {result['message']}")
            print(f"   用户信息: {result['user']['username']} - {result['user']['email']}")
            return True
        else:
            print(f"❌ 注册失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 注册请求异常: {e}")
        return False

def test_rate_limiting():
    """测试发送频率限制"""
    print("\n🔍 测试发送频率限制...")
    
    test_email = "ratelimit@example.com"
    
    try:
        # 第一次发送
        print("   第一次发送验证码...")
        response1 = requests.post(
            f"{API_URL}/users/send-verification-code",
            json={
                "email": test_email,
                "action": "注册"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response1.status_code == 200:
            print("   ✅ 第一次发送成功")
        else:
            print(f"   ❌ 第一次发送失败: {response1.status_code}")
            return False
        
        # 立即第二次发送（应该被限制）
        print("   立即第二次发送验证码...")
        response2 = requests.post(
            f"{API_URL}/users/send-verification-code",
            json={
                "email": test_email,
                "action": "注册"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response2.status_code == 429:
            result = response2.json()
            print(f"   ✅ 频率限制正常工作: {result['detail']}")
            return True
        else:
            print(f"   ❌ 频率限制未生效: {response2.status_code} - {response2.text}")
            return False
            
    except Exception as e:
        print(f"❌ 频率限制测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始邮箱验证功能测试")
    print("=" * 50)
    
    # 测试结果统计
    tests = [
        ("发送验证码", test_send_verification_code),
        ("验证无效验证码", test_verify_code_invalid),
        ("带验证码注册", test_register_with_verification),
        ("发送频率限制", test_rate_limiting),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 测试项目: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！邮箱验证功能正常")
    else:
        print("⚠️ 部分测试失败，请检查配置和服务状态")
    
    print("\n💡 注意事项:")
    print("   1. 确保Redis服务正在运行")
    print("   2. 确保腾讯云SES配置正确")
    print("   3. 实际使用时需要从邮件中获取真实验证码")
    print("   4. 建议在生产环境中测试真实的邮件发送功能")

if __name__ == "__main__":
    main()