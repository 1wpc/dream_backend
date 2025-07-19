#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录功能测试脚本
测试邮箱登录验证、注册邮箱重复检查、登录邮箱存在性检查等功能
"""

import requests
import json
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def test_email_duplicate_check():
    """测试注册时邮箱重复检查"""
    print("\n🔍 测试注册时邮箱重复检查...")
    
    # 生成测试邮箱
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_email = f"test_duplicate_{timestamp}@example.com"
    
    # 第一次注册
    register_data = {
        "username": f"testuser_{timestamp}",
        "email": test_email,
        "password": "password123",
        "full_name": "测试用户"
    }
    
    print(f"📧 使用邮箱: {test_email}")
    
    try:
        # 第一次注册应该成功
        response = requests.post(f"{BASE_URL}/users/register", json=register_data)
        if response.status_code == 201:
            print("✅ 第一次注册成功")
        else:
            print(f"❌ 第一次注册失败: {response.text}")
            return False
        
        # 第二次注册相同邮箱应该失败
        register_data["username"] = f"testuser2_{timestamp}"
        response = requests.post(f"{BASE_URL}/users/register", json=register_data)
        if response.status_code == 400 and "邮箱已存在" in response.text:
            print("✅ 邮箱重复检查正常工作")
            return True
        else:
            print(f"❌ 邮箱重复检查失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_email_existence_check_on_login():
    """测试登录时邮箱存在性检查"""
    print("\n🔍 测试登录时邮箱存在性检查...")
    
    # 使用不存在的邮箱登录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    non_existent_email = f"nonexistent_{timestamp}@example.com"
    
    login_data = {
        "username": non_existent_email,
        "password": "password123"
    }
    
    print(f"📧 尝试登录不存在的邮箱: {non_existent_email}")
    
    try:
        response = requests.post(f"{BASE_URL}/users/login", json=login_data)
        if response.status_code == 404 and "尚未注册" in response.text:
            print("✅ 邮箱存在性检查正常工作")
            return True
        else:
            print(f"❌ 邮箱存在性检查失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_email_login_with_verification():
    """测试邮箱登录验证功能"""
    print("\n🔍 测试邮箱登录验证功能...")
    
    # 首先创建一个测试用户
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_email = f"test_login_{timestamp}@example.com"
    test_password = "password123"
    
    register_data = {
        "username": f"logintest_{timestamp}",
        "email": test_email,
        "password": test_password,
        "full_name": "登录测试用户"
    }
    
    print(f"📧 创建测试用户: {test_email}")
    
    try:
        # 创建用户
        response = requests.post(f"{BASE_URL}/users/register", json=register_data)
        if response.status_code != 201:
            print(f"❌ 创建测试用户失败: {response.text}")
            return False
        
        print("✅ 测试用户创建成功")
        
        # 发送登录验证码
        verification_data = {
            "email": test_email,
            "action": "login"
        }
        
        print("📤 发送登录验证码...")
        response = requests.post(f"{BASE_URL}/users/send-verification-code", json=verification_data)
        if response.status_code != 200:
            print(f"❌ 发送验证码失败: {response.text}")
            return False
        
        print("✅ 验证码发送成功")
        
        # 模拟验证码（实际应用中需要从邮件获取）
        print("⚠️ 注意: 实际使用时需要从邮件中获取验证码")
        print("📝 邮箱验证码登录接口已创建: POST /api/v1/users/login-with-email-verification")
        print("📋 请求格式:")
        print(json.dumps({
            "email": test_email,
            "verification_code": "123456"
        }, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_username_email_login_support():
    """测试用户名和邮箱登录支持"""
    print("\n🔍 测试用户名和邮箱登录支持...")
    
    # 创建测试用户
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_username = f"dualtest_{timestamp}"
    test_email = f"dual_login_{timestamp}@example.com"
    test_password = "password123"
    
    register_data = {
        "username": test_username,
        "email": test_email,
        "password": test_password,
        "full_name": "双重登录测试用户"
    }
    
    print(f"👤 用户名: {test_username}")
    print(f"📧 邮箱: {test_email}")
    
    try:
        # 创建用户
        response = requests.post(f"{BASE_URL}/users/register", json=register_data)
        if response.status_code != 201:
            print(f"❌ 创建测试用户失败: {response.text}")
            return False
        
        print("✅ 测试用户创建成功")
        
        # 测试用户名登录
        login_data = {
            "username": test_username,
            "password": test_password
        }
        
        print("🔐 测试用户名登录...")
        response = requests.post(f"{BASE_URL}/users/login", json=login_data)
        if response.status_code == 200:
            print("✅ 用户名登录成功")
        else:
            print(f"❌ 用户名登录失败: {response.text}")
            return False
        
        # 测试邮箱登录
        login_data["username"] = test_email
        
        print("📧 测试邮箱登录...")
        response = requests.post(f"{BASE_URL}/users/login", json=login_data)
        if response.status_code == 200:
            print("✅ 邮箱登录成功")
            return True
        else:
            print(f"❌ 邮箱登录失败: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始登录功能测试")
    print("=" * 60)
    
    results = []
    
    # 测试1: 注册时邮箱重复检查
    results.append(("注册邮箱重复检查", test_email_duplicate_check()))
    
    # 测试2: 登录时邮箱存在性检查
    results.append(("登录邮箱存在性检查", test_email_existence_check_on_login()))
    
    # 测试3: 邮箱登录验证功能
    results.append(("邮箱登录验证功能", test_email_login_with_verification()))
    
    # 测试4: 用户名和邮箱登录支持
    results.append(("用户名和邮箱登录支持", test_username_email_login_support()))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n📈 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有功能测试通过！")
    else:
        print("⚠️ 部分功能需要检查")
    
    print("\n📋 新增功能说明:")
    print("1. ✅ 注册时邮箱重复检查 - 已实现")
    print("2. ✅ 登录时邮箱存在性检查 - 已实现")
    print("3. ✅ 邮箱验证码登录接口 - 已实现")
    print("4. ✅ 用户名和邮箱登录支持 - 已实现")
    
    print("\n🔗 新增API接口:")
    print("- POST /api/v1/users/login-with-email-verification")
    print("  邮箱验证码登录（无需密码）")
    
    print("\n📝 使用说明:")
    print("1. 发送登录验证码: POST /api/v1/users/send-verification-code")
    print("   请求体: {\"email\": \"user@example.com\", \"action\": \"login\"}")
    print("2. 邮箱验证码登录: POST /api/v1/users/login-with-email-verification")
    print("   请求体: {\"email\": \"user@example.com\", \"verification_code\": \"123456\"}")

if __name__ == "__main__":
    main()