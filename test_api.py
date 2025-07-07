#!/usr/bin/env python3
"""
API测试脚本
用于测试用户管理系统的主要功能
"""

import requests
import json
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

def test_health_check():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_user_registration():
    """测试用户注册"""
    print("\n🔍 测试用户注册...")
    
    # 生成测试用户数据
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_user = {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "password123",
        "full_name": "测试用户"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/users/register",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            print("✅ 用户注册成功")
            return test_user, response.json()
        else:
            print(f"❌ 用户注册失败: {response.status_code}")
            print(f"错误信息: {response.json()}")
            return None, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 注册请求失败: {e}")
        return None, None

def test_user_login(user_data):
    """测试用户登录"""
    print("\n🔍 测试用户登录...")
    
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    
    try:
        response = requests.post(
            f"{API_URL}/users/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ 用户登录成功")
            token_data = response.json()
            return token_data["access_token"]
        else:
            print(f"❌ 用户登录失败: {response.status_code}")
            print(f"错误信息: {response.json()}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 登录请求失败: {e}")
        return None

def test_get_current_user(token):
    """测试获取当前用户信息"""
    print("\n🔍 测试获取当前用户信息...")
    
    try:
        response = requests.get(
            f"{API_URL}/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            print("✅ 获取用户信息成功")
            user_info = response.json()
            print(f"用户信息: {user_info['username']} ({user_info['email']})")
            return user_info
        else:
            print(f"❌ 获取用户信息失败: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取用户信息请求失败: {e}")
        return None

def test_update_user(token):
    """测试更新用户信息"""
    print("\n🔍 测试更新用户信息...")
    
    update_data = {
        "full_name": "更新的用户名",
        "phone": "13800138000"
    }
    
    try:
        response = requests.put(
            f"{API_URL}/users/me",
            json=update_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            print("✅ 更新用户信息成功")
            return True
        else:
            print(f"❌ 更新用户信息失败: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 更新用户信息请求失败: {e}")
        return False

def test_get_users_list(token):
    """测试获取用户列表"""
    print("\n🔍 测试获取用户列表...")
    
    try:
        response = requests.get(
            f"{API_URL}/users/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            print("✅ 获取用户列表成功")
            users = response.json()
            print(f"用户数量: {len(users)}")
            return users
        else:
            print(f"❌ 获取用户列表失败: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取用户列表请求失败: {e}")
        return None

def main():
    """主函数"""
    print("🚀 开始API测试...")
    print(f"📍 测试地址: {BASE_URL}")
    
    # 测试健康检查
    if not test_health_check():
        print("❌ 应用未运行，请先启动应用")
        return
    
    # 测试用户注册
    user_data, register_response = test_user_registration()
    if not user_data:
        print("❌ 用户注册失败，停止测试")
        return
    
    # 测试用户登录
    token = test_user_login(user_data)
    if not token:
        print("❌ 用户登录失败，停止测试")
        return
    
    # 测试获取用户信息
    user_info = test_get_current_user(token)
    if not user_info:
        print("❌ 获取用户信息失败")
        return
    
    # 测试更新用户信息
    test_update_user(token)
    
    # 测试获取用户列表
    test_get_users_list(token)
    
    print("\n🎉 API测试完成!")
    print(f"✅ 测试用户: {user_data['username']}")
    print(f"🔑 访问令牌: {token[:50]}...")

if __name__ == "__main__":
    main() 