import hashlib
import hmac
import json
from datetime import datetime
from urllib.parse import urlencode

import httpx

from config import settings

# V4签名常量
ALGORITHM = "HMAC-SHA256"
SERVICE = settings.VOLCANO_ENGINE_SERVICE_NAME
REGION = settings.VOLCANO_ENGINE_REGION
REQUEST_TYPE = "request"
SIGNED_HEADERS = "content-type;host;x-content-sha256;x-date"

def sign(key, msg):
    """HMAC-SHA256签名"""
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def get_signature_key(key, date_stamp, region_name, service_name):
    """生成签名密钥"""
    k_date = sign(key.encode("utf-8"), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    k_signing = sign(k_service, REQUEST_TYPE)
    return k_signing

class ImageGenerator:
    """
    图片生成服务，手动实现火山引擎API签名和HTTP请求。
    """
    def __init__(self, access_key: str, secret_key: str, region: str, service: str):
        if not access_key or "your_volcano_access_key" in access_key:
            raise ValueError("火山引擎的Access Key未配置。请在 .env 文件或环境变量中设置 VOLCANO_ENGINE_ACCESS_KEY。")
        if not secret_key or "your_volcano_secret_key" in secret_key:
            raise ValueError("火山引擎的Secret Key未配置。请在 .env 文件或环境变量中设置 VOLCANO_ENGINE_SECRET_KEY。")

        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.service = service
        self.host = "visual.volcengineapi.com"
        self.endpoint = f"https://{self.host}"
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate_image(
        self,
        prompt: str,
        width: int,
        height: int,
        seed: int,
        use_sr: bool,
        use_pre_llm: bool,
    ) -> str:
        # 1. 准备请求组件
        method = "POST"
        canonical_uri = "/"
        
        query = {"Action": "CVProcess", "Version": "2022-08-31"}
        canonical_querystring = urlencode(query)

        request_body = json.dumps({
            "req_key": "jimeng_high_aes_general_v21_L",
            "prompt": prompt,
            "width": width,
            "height": height,
            "seed": seed,
            "use_sr": use_sr,
            "use_pre_llm": use_pre_llm,
            "return_url": True,
        })
        
        t = datetime.utcnow()
        amz_date = t.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = t.strftime("%Y%m%d")

        # 2. 创建规范请求 (Canonical Request)
        payload_hash = hashlib.sha256(request_body.encode("utf-8")).hexdigest()
        canonical_headers = (
            f"content-type:application/json\n"
            f"host:{self.host}\n"
            f"x-content-sha256:{payload_hash}\n"
            f"x-date:{amz_date}\n"
        )
        canonical_request = (
            f"{method}\n{canonical_uri}\n{canonical_querystring}\n"
            f"{canonical_headers}\n{SIGNED_HEADERS}\n{payload_hash}"
        )

        # 3. 创建待签名的字符串 (String to Sign)
        credential_scope = f"{date_stamp}/{self.region}/{self.service}/{REQUEST_TYPE}"
        string_to_sign = (
            f"{ALGORITHM}\n{amz_date}\n{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )

        # 4. 计算签名
        signing_key = get_signature_key(self.secret_key, date_stamp, self.region, self.service)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        # 5. 构建Authorization头
        authorization_header = (
            f"{ALGORITHM} Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={SIGNED_HEADERS}, Signature={signature}"
        )

        # 6. 构建最终的请求头和URL
        headers = {
            "Content-Type": "application/json",
            "Host": self.host,
            "X-Date": amz_date,
            "X-Content-Sha256": payload_hash,
            "Authorization": authorization_header,
        }
        request_url = f"{self.endpoint}{canonical_uri}?{canonical_querystring}"

        # 7. 发送请求
        try:
            resp = await self.client.post(request_url, content=request_body, headers=headers)
            resp.raise_for_status()
            
            resp_json = resp.json()
            if resp_json.get("code") != 10000:
                error_message = resp_json.get("message", "未知API错误")
                raise ValueError(f"火山引擎API错误: {error_message}")

            image_urls = resp_json.get("data", {}).get("image_urls")
            if not image_urls:
                raise ValueError("API响应中未找到有效的图片URL")
            
            return image_urls[0]
        except httpx.HTTPStatusError as e:
            print(f"API请求失败: {e.response.text}")
            raise Exception(f"API请求失败: {e.response.text}")
        except Exception as e:
            print(f"调用火山引擎API时发生异常: {e}")
            raise Exception(f"图片生成服务调用失败: {e}")


# 创建服务实例
image_service = ImageGenerator(
    access_key=settings.VOLCANO_ENGINE_ACCESS_KEY,
    secret_key=settings.VOLCANO_ENGINE_SECRET_KEY,
    region=settings.VOLCANO_ENGINE_REGION,
    service=settings.VOLCANO_ENGINE_SERVICE_NAME
) 