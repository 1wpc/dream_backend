# routers/chat.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal

import crud
import schemas
import models
from database import get_db
from auth import get_current_active_user
from config import settings
from services import deepseek_service

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

class ChatRequest(schemas.BaseModel):
    messages: List[Dict[str, str]]
    stream: bool = False

@router.post("/completions")
async def create_chat_completion(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    接收聊天请求，调用DeepSeek API，并扣除用户积分。
    - **messages**: 聊天消息列表，遵循OpenAI格式 `[{"role": "user", "content": "Hello"}]`。
    - **stream**: 是否以流式方式返回响应。
    """
    cost = settings.DEEPSEEK_CHAT_COST

    # 1. 检查积分是否充足
    if current_user.points_balance < cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"积分不足。当前余额: {current_user.points_balance}, 本次消耗: {cost}",
        )

    # 2. 扣除积分
    transaction = None
    try:
        transaction = crud.deduct_points(
            db=db,
            user_id=current_user.id,
            amount=Decimal(cost),
            transaction_type=models.PointTransactionType.DEEPSEEK_CHAT,
            description=f"DeepSeek聊天消耗",
        )
        if not transaction:
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建积分交易失败，但未触发异常",
            )
    except ValueError as e: # 捕获积分不足的错误
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e),
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建积分交易失败: {e}",
        )

    # 3. 调用DeepSeek服务
    try:
        response_generator = await deepseek_service.generate_chat_completion(
            messages=request.messages,
            stream=request.stream
        )

        # 4. 处理响应
        if request.stream:
            # 流式响应
            async def content_stream():
                try:
                    async for content in response_generator:
                        yield content
                except Exception as api_error:
                    # API在流式传输中出错，尝试退款
                    print(f"DeepSeek API stream error, attempting to refund points: {api_error}")
                    crud.add_points(
                        db=db, 
                        user_id=current_user.id, 
                        amount=Decimal(cost),
                        transaction_type=models.PointTransactionType.REFUND,
                        description=f"DeepSeek聊天失败退款",
                        reference_id=str(transaction.id)
                    )

            return StreamingResponse(content_stream(), media_type="text/plain")
        else:
            # 非流式响应
            return {"response": response_generator}

    except Exception as api_error:
        # 非流式API调用失败或流式启动前失败，退款
        db.rollback() # 回滚未提交的事务
        crud.add_points(
            db=db, 
            user_id=current_user.id, 
            amount=Decimal(cost),
            transaction_type=models.PointTransactionType.REFUND,
            description=f"DeepSeek聊天失败退款",
            reference_id=str(transaction.id)
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"调用DeepSeek API失败: {api_error}",
        ) 