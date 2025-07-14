#!/usr/bin/env python3
"""
API测试脚本
用于测试用户管理系统的主要功能
"""

import requests
import json
from datetime import datetime
from decimal import Decimal

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

def test_get_points_balance(token):
    """测试获取积分余额"""
    print("\n🔍 测试获取积分余额...")
    
    try:
        response = requests.get(
            f"{API_URL}/points/balance",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            print("✅ 获取积分余额成功")
            balance = response.json()
            print(f"当前积分: {balance['points_balance']}")
            print(f"累计获得: {balance['total_points_earned']}")
            print(f"累计消费: {balance['total_points_spent']}")
            return balance
        else:
            print(f"❌ 获取积分余额失败: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取积分余额请求失败: {e}")
        return None

def test_get_points_transactions(token):
    """测试获取积分交易记录"""
    print("\n🔍 测试获取积分交易记录...")
    
    try:
        response = requests.get(
            f"{API_URL}/points/transactions",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            print("✅ 获取积分交易记录成功")
            data = response.json()
            print(f"交易记录数量: {len(data['transactions'])}")
            print(f"总记录数: {data['total']}")
            return data
        else:
            print(f"❌ 获取积分交易记录失败: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取积分交易记录请求失败: {e}")
        return None

def test_claim_login_bonus(token):
    """测试领取登录奖励"""
    print("\n🔍 测试领取登录奖励...")
    
    try:
        response = requests.post(
            f"{API_URL}/points/login-bonus",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            print("✅ 领取登录奖励成功")
            transaction = response.json()
            print(f"奖励积分: {transaction['amount']}")
            print(f"交易后余额: {transaction['balance_after']}")
            return transaction
        else:
            print(f"❌ 领取登录奖励失败: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 领取登录奖励请求失败: {e}")
        return None

def test_image_generation(token):
    """测试图片生成"""
    print("\n🎨 测试图片生成...")
    
    # 1. 先获取当前积分
    balance_before_res = requests.get(
        f"{API_URL}/points/balance",
        headers={"Authorization": f"Bearer {token}"}
    )
    if balance_before_res.status_code != 200:
        print("❌ 获取初始积分失败，跳过测试")
        return False
    balance_before = Decimal(balance_before_res.json()['points_balance'])
    print(f"  生成前积分: {balance_before}")

    # 2. 检查积分是否足够
    cost = 50 # 与config中设置的成本保持一致
    if balance_before < cost:
        print(f"  积分不足（需要{cost}），跳过图片生成测试")
        return False # 不是测试失败，而是无法测试

    # 3. 发起图片生成请求
    payload = {"prompt": "a cute cat"}
    try:
        response = requests.post(
            f"{API_URL}/generate/image",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            print("✅ 图片生成成功")
            data = response.json()
            print(f"  图片URL: {data['image_url']}")
            print(f"  消耗积分: {data['points_spent']}")
            print(f"  剩余积分: {data['points_remaining']}")
            
            # 验证积分扣除是否正确
            expected_balance = balance_before - Decimal(str(data['points_spent']))
            actual_balance = Decimal(str(data['points_remaining']))
            
            if expected_balance == actual_balance:
                print("✅ 积分扣除正确")
                return True
            else:
                print(f"❌ 积分扣除错误: 期望 {expected_balance}, 实际 {actual_balance}")
                return False
        else:
            print(f"❌ 图片生成失败: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 图片生成请求失败: {e}")
        return False

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
    
    # 测试积分功能
    print("\n" + "="*50)
    print("🎯 开始测试积分功能...")
    
    # 测试获取积分余额
    balance = test_get_points_balance(token)
    
    # 测试获取积分交易记录
    test_get_points_transactions(token)
    
    # 测试领取登录奖励
    test_claim_login_bonus(token)
    
    # 再次查看积分余额
    updated_balance = test_get_points_balance(token)
    
    # 测试图片生成
    test_image_generation(token)

    print("\n🎉 API测试完成!")
    print(f"✅ 测试用户: {user_data['username']}")
    print(f"🔑 访问令牌: {token[:50]}...")
    if updated_balance:
        print(f"💰 最终积分余额: {updated_balance['points_balance']}")

if __name__ == "__main__":
    main() 