# services/deepseek_service.py
from openai import OpenAI
from config import settings
from typing import List, Dict, Union, AsyncGenerator

# 初始化DeepSeek客户端
client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

async def generate_chat_completion(messages: List[Dict[str, str]], stream: bool = False) -> Union[str, AsyncGenerator[str, None]]:
    """
    调用DeepSeek API生成聊天回复。

    Args:
        messages: 发送给模型的聊天消息列表。
        stream: 是否使用流式输出。

    Returns:
        如果 stream=False，返回完整的聊天回复字符串。
        如果 stream=True，返回一个异步生成器，逐块产生回复内容。
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=stream,
            max_tokens=2048,
            temperature=0.7,
        )

        if stream:
            async def stream_generator():
                for chunk in response:
                    if chunk.choices[0].delta and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            return stream_generator()
        else:
            return response.choices[0].message.content

    except Exception as e:
        # 在实际应用中，这里应该有更完善的错误日志记录
        print(f"Error calling DeepSeek API: {e}")
        raise 