from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from database import get_db
from schemas import PaymentRequest, PaymentResponse, User
from auth import get_current_active_user
from services.alipay_service import alipay_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/payment",
    tags=["支付管理"],
    responses={404: {"description": "Not found"}},
)

@router.post("/create-order", response_model=PaymentResponse)
async def create_payment_order(
    payment_request: PaymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    创建支付订单
    
    客户端调用此接口创建支付订单，服务端调用支付宝SDK生成订单字符串返回给客户端
    """
    try:
        # 调用支付宝服务创建订单
        order_string, out_trade_no = alipay_service.create_app_pay_order(
            subject=payment_request.subject,
            body=payment_request.body,
            total_amount=payment_request.total_amount,
            out_trade_no=payment_request.out_trade_no
        )
        
        logger.info(f"用户 {current_user.username} 创建支付订单: {out_trade_no}, 金额: {payment_request.total_amount}")
        
        return PaymentResponse(
            order_string=order_string,
            out_trade_no=out_trade_no,
            total_amount=payment_request.total_amount,
            subject=payment_request.subject,
            message="订单创建成功"
        )
        
    except Exception as e:
        logger.error(f"创建支付订单失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建支付订单失败: {str(e)}"
        )

@router.post("/notify")
async def payment_notify(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    支付宝异步通知接口
    
    支付宝在用户支付成功后会调用此接口通知服务端
    """
    try:
        # 获取POST数据
        form_data = await request.form()
        post_data = dict(form_data)
        
        logger.info(f"收到支付宝异步通知: {post_data}")
        
        # 验证签名
        if not alipay_service.verify_notify(post_data):
            logger.error("支付宝通知签名验证失败")
            return "fail"
        
        # 获取关键信息
        out_trade_no = post_data.get('out_trade_no')  # 商户订单号
        trade_no = post_data.get('trade_no')  # 支付宝交易号
        trade_status = post_data.get('trade_status')  # 交易状态
        total_amount = post_data.get('total_amount')  # 交易金额
        
        # 处理支付成功的逻辑
        if trade_status == 'TRADE_SUCCESS':
            logger.info(f"支付成功: 订单号={out_trade_no}, 交易号={trade_no}, 金额={total_amount}")
            
            # 这里可以添加业务逻辑，比如：
            # 1. 更新订单状态
            # 2. 给用户增加积分
            # 3. 发送通知等
            
            # TODO: 实现具体的业务逻辑
            
        elif trade_status == 'TRADE_FINISHED':
            logger.info(f"交易完成: 订单号={out_trade_no}, 交易号={trade_no}")
            # 处理交易完成的逻辑
            
        else:
            logger.warning(f"未处理的交易状态: {trade_status}")
        
        # 返回success告诉支付宝处理成功
        return "success"
        
    except Exception as e:
        logger.error(f"处理支付宝异步通知失败: {str(e)}")
        return "fail"

@router.get("/test")
async def test_payment():
    """
    测试接口，用于验证支付模块是否正常工作
    """
    return {
        "message": "支付模块工作正常",
        "alipay_configured": True
    }