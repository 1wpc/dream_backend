from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from database import get_db
from schemas import ImageGenerationRequest, ImageGenerationResponse, User
from auth import get_current_active_user
from services.image_generator import image_service
from config import settings
import crud
from models import PointTransactionType

router = APIRouter(
    prefix="/generate",
    tags=["内容生成"],
    responses={404: {"description": "Not found"}},
)

@router.post("/image", response_model=ImageGenerationResponse)
async def generate_image_endpoint(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    生成图片端点。
    - 检查用户积分是否足够。
    - 扣除积分。
    - 调用图片生成服务。
    - 如果生成失败，则回滚积分。
    - 返回图片URL和用户剩余积分。
    """
    cost = Decimal(settings.IMAGE_GENERATION_COST)

    # 1. 检查积分是否足够
    if current_user.points_balance < cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"积分不足，生成图片需要 {cost} 积分，您当前拥有 {current_user.points_balance} 积分。"
        )

    # 2. 扣除积分
    try:
        transaction = crud.deduct_points(
            db=db,
            user_id=current_user.id,
            amount=cost,
            transaction_type=PointTransactionType.IMAGE_GENERATION,
            description=f"生成图片: {request.prompt[:50]}...",
            reference_id=f"prompt_{request.prompt[:20]}" # 可以用更复杂的ID
        )
        if not transaction:
            raise HTTPException(status_code=500, detail="积分扣除失败")
    except ValueError as e:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


    # 3. 调用图片生成服务
    try:
        image_url = await image_service.generate_image(
            prompt=request.prompt,
            width=request.width,
            height=request.height,
            seed=request.seed,
            use_sr=request.use_sr,
            use_pre_llm=request.use_pre_llm
        )
    except Exception as e:
        # 4. 如果生成失败，回滚积分
        print(f"图片生成失败，正在回滚积分: {e}")
        crud.add_points(
            db=db,
            user_id=current_user.id,
            amount=cost,
            transaction_type=PointTransactionType.REFUND,
            description=f"图片生成失败退款: {request.prompt[:50]}...",
            reference_id=transaction.reference_id
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"图片生成服务暂时不可用，您的积分已退还。错误: {e}"
        )

    # 5. 成功返回
    db.refresh(current_user)

    return ImageGenerationResponse(
        image_url=image_url,
        points_spent=cost,
        points_remaining=current_user.points_balance,
        message="图片生成成功！"
    ) 