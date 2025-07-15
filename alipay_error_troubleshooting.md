# 支付宝集成错误排查指南

## 错误描述

```
request sign failed. int() argument must be a string, a bytes-like object or a real number, not 'Sequence'
```

## 错误原因

这个错误通常是由于支付宝私钥格式不正确导致的。支付宝SDK在进行RSA签名时，需要私钥具有特定的格式，包括：

1. **正确的头尾标识**：`-----BEGIN RSA PRIVATE KEY-----` 和 `-----END RSA PRIVATE KEY-----`
2. **正确的换行格式**：每64个字符一行
3. **无多余的空格或特殊字符**

## 解决方案

### 1. 私钥格式修复

我们已经在 `services/alipay_service.py` 中添加了自动格式化功能：

- `_format_private_key()` 方法：自动格式化应用私钥
- `_format_public_key()` 方法：自动格式化支付宝公钥

### 2. 正确的私钥格式示例

**正确的私钥格式：**
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890abcdef1234567890abcdef1234567890abcdef
1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
...
-----END RSA PRIVATE KEY-----
```

**错误的格式（常见问题）：**
```
# 缺少头尾标识
MIIEpAIBAAKCAQEA1234567890abcdef...

# 格式混乱
-----BEGIN RSA PRIVATE KEY-----MIIEpAIBAAKCAQEA1234567890abcdef...-----END RSA PRIVATE KEY-----

# 包含多余空格
-----BEGIN RSA PRIVATE KEY-----
 MIIEpAIBAAKCAQEA1234567890abcdef 
-----END RSA PRIVATE KEY-----
```

### 3. 环境变量配置

在 `.env` 文件中正确配置支付宝参数：

```env
# 支付宝配置
ALIPAY_APP_ID=你的应用ID
ALIPAY_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"
ALIPAY_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
MIIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...
-----END PUBLIC KEY-----"
ALIPAY_SELLER_ID=你的卖家ID
ALIPAY_NOTIFY_URL=https://your-domain.com/api/v1/payment/notify
```

### 4. 测试验证

使用以下命令测试支付接口：

```bash
# 启动服务
uvicorn main:app --reload

# 测试支付接口
curl -X POST "http://localhost:8000/api/v1/payment/test" \
  -H "Content-Type: application/json"
```

## 常见问题

### Q1: 如何获取正确格式的私钥？

**A:** 从支付宝开放平台下载的私钥文件通常是正确格式的。如果你的私钥是一行字符串，需要：

1. 每64个字符添加一个换行符
2. 在开头添加 `-----BEGIN RSA PRIVATE KEY-----`
3. 在结尾添加 `-----END RSA PRIVATE KEY-----`

### Q2: 沙箱环境和生产环境的区别？

**A:** 在 `services/alipay_service.py` 中切换：

```python
# 生产环境
alipay_client_config.server_url = 'https://openapi.alipay.com/gateway.do'

# 沙箱环境
alipay_client_config.server_url = 'https://openapi.alipaydev.com/gateway.do'
```

### Q3: 如何验证私钥格式是否正确？

**A:** 可以使用以下Python代码验证：

```python
from cryptography.hazmat.primitives import serialization

def validate_private_key(private_key_str):
    try:
        private_key = serialization.load_pem_private_key(
            private_key_str.encode(),
            password=None
        )
        print("私钥格式正确")
        return True
    except Exception as e:
        print(f"私钥格式错误: {e}")
        return False
```

## 安全注意事项

1. **私钥保护**：私钥绝对不能泄露，不要提交到代码仓库
2. **环境变量**：使用环境变量存储敏感信息
3. **权限控制**：确保只有必要的人员能访问私钥
4. **定期更换**：建议定期更换密钥对

## 相关文档

- [支付宝开放平台文档](https://opendocs.alipay.com/)
- [RSA密钥生成工具](https://opendocs.alipay.com/common/02kipl)
- [支付宝SDK文档](https://github.com/alipay/alipay-sdk-python-all)

## 联系支持

如果问题仍然存在，请检查：

1. 支付宝应用配置是否正确
2. 私钥是否与应用匹配
3. 网络连接是否正常
4. SDK版本是否兼容