#!/usr/bin/env python3
"""
Redis连接测试脚本
测试Redis服务是否正常运行并可以连接
"""

import redis
from config import settings

def test_redis_connection():
    """测试Redis连接"""
    print("🔍 测试Redis连接...")
    
    try:
        # 创建Redis连接
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        # 测试连接
        redis_client.ping()
        print("✅ Redis连接成功")
        
        # 测试基本操作
        test_key = "test_email_verification"
        test_value = "123456"
        
        # 设置键值
        redis_client.setex(test_key, 60, test_value)
        print(f"✅ 设置测试键值成功: {test_key} = {test_value}")
        
        # 获取键值
        retrieved_value = redis_client.get(test_key)
        if retrieved_value == test_value:
            print(f"✅ 获取键值成功: {retrieved_value}")
        else:
            print(f"❌ 获取键值失败: 期望 {test_value}, 实际 {retrieved_value}")
            return False
        
        # 检查TTL
        ttl = redis_client.ttl(test_key)
        print(f"✅ TTL检查成功: {ttl} 秒")
        
        # 删除测试键
        redis_client.delete(test_key)
        print("✅ 删除测试键成功")
        
        # 验证删除
        if redis_client.get(test_key) is None:
            print("✅ 验证删除成功")
        else:
            print("❌ 删除验证失败")
            return False
        
        print("\n🎉 Redis功能测试全部通过！")
        return True
        
    except redis.ConnectionError as e:
        print(f"❌ Redis连接失败: {e}")
        print("💡 请确保Redis服务正在运行")
        print(f"   配置信息: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        return False
    except Exception as e:
        print(f"❌ Redis测试异常: {e}")
        return False

def show_redis_info():
    """显示Redis配置信息"""
    print("📋 Redis配置信息:")
    print(f"   主机: {settings.REDIS_HOST}")
    print(f"   端口: {settings.REDIS_PORT}")
    print(f"   数据库: {settings.REDIS_DB}")
    print(f"   密码: {'已设置' if settings.REDIS_PASSWORD else '未设置'}")
    print(f"   验证码有效期: {settings.EMAIL_VERIFICATION_EXPIRE_MINUTES} 分钟")

def main():
    """主函数"""
    print("🚀 Redis连接和功能测试")
    print("=" * 40)
    
    show_redis_info()
    print()
    
    if test_redis_connection():
        print("\n✅ Redis服务正常，可以进行邮箱验证功能测试")
    else:
        print("\n❌ Redis服务异常，请先解决Redis连接问题")
        print("\n🔧 解决方案:")
        print("   1. 安装Redis: https://redis.io/download")
        print("   2. 启动Redis服务: redis-server")
        print("   3. 检查防火墙设置")
        print("   4. 验证配置文件中的Redis连接信息")

if __name__ == "__main__":
    main()