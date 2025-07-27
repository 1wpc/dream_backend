from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from database import get_db
from schemas import (
    UserCreate, User, UserLogin, UserUpdate, UserResponse, Token, Message,
    EmailVerificationRequest, EmailVerificationResponse, EmailCodeVerifyRequest,
    UserCreateWithVerification, EmailLoginRequest, UserRegisterResponse,
    SMSVerificationRequest, SMSVerificationResponse, SMSCodeVerifyRequest,
    SMSLoginRequest, UserCreateWithSMSVerification, RefreshTokenRequest, AccessTokenResponse
)
from auth import (
    authenticate_user, 
    create_token_pair, 
    get_current_active_user,
    get_current_user,
    verify_password,
    refresh_access_token
)
from config import settings
import crud
from services.email_service import email_service
from services.sms_service import sms_service

router = APIRouter(
    prefix="/users",
    tags=["用户管理"],
    responses={404: {"description": "Not found"}},
)

@router.post("/send-verification-code", response_model=EmailVerificationResponse)
async def send_verification_code(request: EmailVerificationRequest):
    """发送邮箱验证码"""
    result = email_service.send_verification_code(request.email, request.action)
    
    if not result["success"]:
        if result["code"] == "RATE_LIMIT":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=result["message"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
    
    return EmailVerificationResponse(**result)

@router.post("/verify-email-code", response_model=EmailVerificationResponse)
async def verify_email_code(request: EmailCodeVerifyRequest):
    """验证邮箱验证码"""
    result = email_service.verify_code(request.email, request.code, request.action)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return EmailVerificationResponse(**result)

# 原始注册接口已删除，现在只支持邮箱验证码注册和短信验证码注册

@router.post("/register-with-verification", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_with_verification(user: UserCreateWithVerification, db: Session = Depends(get_db)):
    """用户注册（需要邮箱验证码）"""
    try:
        # 验证邮箱验证码
        verification_result = email_service.verify_code(user.email, user.verification_code, "register")
        if not verification_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verification_result["message"]
            )
        
        # 创建用户对象（不包含验证码字段）
        user_create = UserCreate(
            username=user.username,
            email=user.email,
            password=user.password,
            full_name=user.full_name,
            phone=user.phone,
            avatar=user.avatar
        )
        
        # 创建用户
        db_user = crud.create_user(db=db, user=user_create)
        
        # 使用双token机制
        token_response = create_token_pair(db_user, db)
        
        return UserRegisterResponse(
            user=User.model_validate(db_user),
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token,
            token_type="bearer",
            expires_in=token_response.expires_in,
            message="用户注册成功，邮箱验证通过，已自动登录"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        # 检查是否是邮箱格式，如果是邮箱但用户不存在，提示需要先注册
        if "@" in user_credentials.username:
            existing_user = crud.get_user_by_email(db, user_credentials.username)
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="该邮箱尚未注册，请先注册账号"
                )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账号已被禁用"
        )
    
    # 使用双token机制
    token_response = create_token_pair(user, db)
    
    return token_response

@router.post("/login-with-email-verification", response_model=Token)
async def login_with_email_verification(login_request: EmailLoginRequest, db: Session = Depends(get_db)):
    """邮箱验证码登录（无需密码）"""
    try:
        # 1. 验证邮箱验证码
        verification_result = email_service.verify_code(login_request.email, login_request.verification_code, "login")
        if not verification_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verification_result["message"]
            )
        
        # 2. 检查用户是否存在
        user = crud.get_user_by_email(db, login_request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="该邮箱尚未注册，请先注册账号"
            )
        
        # 3. 检查用户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户账号已被禁用"
            )
        
        # 4. 使用双token机制
        token_response = create_token_pair(user, db)
        
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )

@router.post("/refresh-token", response_model=AccessTokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """刷新访问令牌（滑动窗口机制）"""
    try:
        token_response = refresh_access_token(request.refresh_token, db)
        return token_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新令牌失败，请重新登录"
        )

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    try:
        updated_user = crud.update_user(db=db, user_id=current_user.id, user_update=user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return UserResponse(
            user=User.model_validate(updated_user),
            message="用户信息更新成功"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户列表（需要登录）"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """根据ID获取用户信息"""
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return db_user

@router.delete("/{user_id}", response_model=Message)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除用户（需要是超级用户）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    success = crud.delete_user(db=db, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return Message(message="用户删除成功")

@router.post("/{user_id}/activate", response_model=Message)
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """激活用户（需要是超级用户）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    user = crud.activate_user(db=db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return Message(message="用户激活成功")

@router.post("/{user_id}/deactivate", response_model=Message)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """禁用用户（需要是超级用户）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    user = crud.deactivate_user(db=db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return Message(message="用户禁用成功")

# 短信验证码相关接口
@router.post("/send-sms-verification-code", response_model=SMSVerificationResponse)
async def send_sms_verification_code(request: SMSVerificationRequest):
    """发送短信验证码"""
    result = sms_service.send_verification_code(request.phone, request.action)
    
    if not result["success"]:
        if "频繁" in result["message"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=result["message"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
    
    return SMSVerificationResponse(**result)

@router.post("/verify-sms-code", response_model=SMSVerificationResponse)
async def verify_sms_code(request: SMSCodeVerifyRequest):
    """验证短信验证码"""
    result = sms_service.verify_code(request.phone, request.code, request.action)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return SMSVerificationResponse(**result)

@router.post("/register-with-sms-verification", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_with_sms_verification(user: UserCreateWithSMSVerification, db: Session = Depends(get_db)):
    """用户注册（需要短信验证码）"""
    try:
        # 验证短信验证码
        verification_result = sms_service.verify_code(user.phone, user.verification_code, "register")
        if not verification_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verification_result["message"]
            )
        
        # 检查手机号是否已注册
        existing_user = crud.get_user_by_phone(db, user.phone)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该手机号已注册，请直接登录"
            )
        
        # 如果邮箱为空，使用默认邮箱
        email = user.email if user.email else "default@default.com"
        
        # 创建用户对象（不包含验证码字段）
        user_create = UserCreate(
            username=user.username,
            email=email,
            password=user.password,
            full_name=user.full_name,
            phone=user.phone,
            avatar=user.avatar
        )
        
        # 创建用户
        db_user = crud.create_user(db=db, user=user_create)
        
        # 使用双token机制
        token_response = create_token_pair(db_user, db)
        
        return UserRegisterResponse(
            user=User.model_validate(db_user),
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token,
            token_type="bearer",
            expires_in=token_response.expires_in,
            message="用户注册成功，短信验证通过，已自动登录"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )

@router.post("/login-with-sms-verification", response_model=Token)
async def login_with_sms_verification(login_request: SMSLoginRequest, db: Session = Depends(get_db)):
    """短信验证码登录（无需密码）"""
    try:
        # 1. 验证短信验证码
        verification_result = sms_service.verify_code(login_request.phone, login_request.verification_code, "login")
        if not verification_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verification_result["message"]
            )
        
        # 2. 检查用户是否存在
        user = crud.get_user_by_phone(db, login_request.phone)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="该手机号尚未注册，请先注册账号"
            )
        
        # 3. 检查用户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户账号已被禁用"
            )
        
        # 4. 使用双token机制
        token_response = create_token_pair(user, db)
        
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )