from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
import traceback
from decimal import Decimal

from database import get_db
from schemas import PaymentRequest, PaymentResponse, User
from auth import get_current_active_user
from services.alipay_service import alipay_service
import crud
from datetime import datetime

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
        
        # 创建数据库订单记录
        db_order = crud.create_order(
            db=db,
            user_id=current_user.id,
            out_trade_no=out_trade_no,
            subject=payment_request.subject,
            body=payment_request.body or "",
            total_amount=payment_request.total_amount
        )
        
        if not db_order:
            logger.error(f"创建数据库订单记录失败: {out_trade_no}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建订单记录失败"
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
    根据支付宝官方文档实现完整的异步通知处理流程
    """
    try:
        # 获取POST数据
        form_data = await request.form()
        post_data = dict(form_data)
        
        logger.info(f"收到支付宝异步通知: notify_id={post_data.get('notify_id')}, out_trade_no={post_data.get('out_trade_no')}")
        
        # 1. 验证通知参数的完整性和有效性
        is_valid, error_msg = alipay_service.validate_notify_params(post_data)
        if not is_valid:
            logger.error(f"通知参数验证失败: {error_msg}")
            return "fail"
        
        # 2. 验证签名
        if not alipay_service.verify_notify(post_data):
            logger.error("支付宝通知签名验证失败")
            return "fail"
        
        # 3. 获取关键信息
        notify_data = {
            'notify_id': post_data.get('notify_id'),
            'notify_time': post_data.get('notify_time'),
            'out_trade_no': post_data.get('out_trade_no'),
            'trade_no': post_data.get('trade_no'),
            'trade_status': post_data.get('trade_status'),
            'total_amount': post_data.get('total_amount'),
            'receipt_amount': post_data.get('receipt_amount'),
            'buyer_id': post_data.get('buyer_id'),
            'seller_id': post_data.get('seller_id'),
            'subject': post_data.get('subject'),
            'body': post_data.get('body'),
            'gmt_create': post_data.get('gmt_create'),
            'gmt_payment': post_data.get('gmt_payment')
        }
        
        # 4. 根据交易状态处理业务逻辑
        trade_status = post_data.get('trade_status')
        
        if trade_status == 'TRADE_SUCCESS':
            # 交易支付成功
            success = await _handle_trade_success(notify_data, db)
            if not success:
                logger.error(f"处理支付成功业务逻辑失败: {notify_data['out_trade_no']}")
                return "fail"
                
        elif trade_status == 'TRADE_FINISHED':
            # 交易完成（不可退款）
            success = await _handle_trade_finished(notify_data, db)
            if not success:
                logger.error(f"处理交易完成业务逻辑失败: {notify_data['out_trade_no']}")
                return "fail"
                
        elif trade_status == 'TRADE_CLOSED':
            # 交易关闭（未付款或全额退款）
            success = await _handle_trade_closed(notify_data, db)
            if not success:
                logger.error(f"处理交易关闭业务逻辑失败: {notify_data['out_trade_no']}")
                return "fail"
                
        else:
            logger.warning(f"未处理的交易状态: {trade_status}, 订单号: {notify_data['out_trade_no']}")
        
        # 5. 返回success告诉支付宝处理成功
        logger.info(f"异步通知处理成功: {notify_data['out_trade_no']}")
        return "success"
        
    except Exception as e:
        logger.error(f"处理支付宝异步通知失败: {str(e)}")
        logger.error(traceback.format_exc())
        return "fail"

async def _handle_trade_success(notify_data: dict, db: Session) -> bool:
    """
    处理交易支付成功的业务逻辑
    
    Args:
        notify_data: 通知数据
        db: 数据库会话
        
    Returns:
        bool: 处理是否成功
    """
    try:
        out_trade_no = notify_data['out_trade_no']
        trade_no = notify_data['trade_no']
        total_amount = Decimal(notify_data['total_amount'])
        gmt_payment = notify_data.get('gmt_payment')
        
        logger.info(f"处理支付成功: 订单号={out_trade_no}, 交易号={trade_no}, 金额={total_amount}")
        
        # 1. 根据订单号获取订单信息
        order = crud.get_order_by_out_trade_no(db, out_trade_no)
        if not order:
            logger.error(f"订单不存在: {out_trade_no}")
            return False
        
        # 2. 检查订单是否已经处理过（防止重复通知）
        if order.status.value == 'PAID':
            logger.info(f"订单已处理过: {out_trade_no}")
            return True
        
        # 3. 解析支付时间
        payment_time = None
        if gmt_payment:
            try:
                payment_time = datetime.strptime(gmt_payment, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                logger.warning(f"支付时间格式错误: {gmt_payment}")
                payment_time = datetime.now()
        
        # 4. 更新订单状态为已支付
        updated_order = crud.update_order_payment_success(
            db=db,
            out_trade_no=out_trade_no,
            trade_no=trade_no,
            paid_amount=total_amount,
            payment_time=payment_time
        )
        
        if not updated_order:
            logger.error(f"更新订单状态失败: {out_trade_no}")
            return False
        
        # 5. 计算并奖励积分
        points_to_award = total_amount * updated_order.points_rate
        
        if points_to_award > 0:
            result = crud.award_points_for_order(
                db=db,
                order_id=updated_order.id,
                points_amount=points_to_award
            )
            
            if result:
                order, transaction = result
                logger.info(f"积分奖励成功: 用户ID={order.user_id}, 订单号={out_trade_no}, 奖励积分={points_to_award}")
            else:
                logger.error(f"积分奖励失败: 订单号={out_trade_no}")
                # 积分奖励失败不影响支付成功的处理
        
        logger.info(f"支付成功处理完成: {out_trade_no}")
        return True
        
    except Exception as e:
        logger.error(f"处理支付成功业务逻辑失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False

async def _handle_trade_finished(notify_data: dict, db: Session) -> bool:
    """
    处理交易完成的业务逻辑（交易不可退款）
    
    Args:
        notify_data: 通知数据
        db: 数据库会话
        
    Returns:
        bool: 处理是否成功
    """
    try:
        out_trade_no = notify_data['out_trade_no']
        trade_no = notify_data['trade_no']
        
        logger.info(f"处理交易完成: 订单号={out_trade_no}, 交易号={trade_no}")
        
        # TODO: 实现具体的业务逻辑
        # 1. 更新订单状态为已完成
        # 2. 清理临时数据
        # 3. 生成交易完成报告
        
        return True
        
    except Exception as e:
        logger.error(f"处理交易完成业务逻辑失败: {str(e)}")
        return False

async def _handle_trade_closed(notify_data: dict, db: Session) -> bool:
    """
    处理交易关闭的业务逻辑（未付款或全额退款）
    
    Args:
        notify_data: 通知数据
        db: 数据库会话
        
    Returns:
        bool: 处理是否成功
    """
    try:
        out_trade_no = notify_data['out_trade_no']
        trade_no = notify_data['trade_no']
        
        logger.info(f"处理交易关闭: 订单号={out_trade_no}, 交易号={trade_no}")
        
        # TODO: 实现具体的业务逻辑
        # 1. 更新订单状态为已关闭
        # 2. 释放库存（如果有）
        # 3. 处理退款逻辑（如果是退款导致的关闭）
        # 4. 发送交易关闭通知
        
        return True
        
    except Exception as e:
        logger.error(f"处理交易关闭业务逻辑失败: {str(e)}")
        return False

@router.get("/test")
async def test_payment():
    """
    测试接口，用于验证支付模块是否正常工作
    """
    return {
        "message": "支付模块工作正常",
        "alipay_configured": True
    }

@router.get("/notify-test")
async def test_notify_format():
    """
    测试异步通知数据格式
    
    返回支付宝异步通知的标准数据格式示例
    """
    return {
        "message": "支付宝异步通知标准格式",
        "example_data": {
            "notify_time": "2023-12-27 06:20:30",
            "notify_type": "trade_status_sync",
            "notify_id": "ac05099524730693a8b330c5ecf72da9786",
            "app_id": "2014072300007148",
            "trade_no": "20213112011001004330000121536",
            "out_trade_no": "6823789339978248",
            "trade_status": "TRADE_SUCCESS",
            "total_amount": "20.00",
            "receipt_amount": "15.00",
            "buyer_id": "2088101106499364",
            "seller_id": "2088101106499364",
            "subject": "测试商品",
            "body": "测试商品描述",
            "gmt_create": "2015-04-27 15:45:57",
            "gmt_payment": "2015-04-27 15:45:57"
        },
        "supported_trade_status": [
            "TRADE_SUCCESS",  # 交易支付成功
            "TRADE_FINISHED", # 交易完成
            "TRADE_CLOSED"    # 交易关闭
        ]
    }