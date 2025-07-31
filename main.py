from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from database import engine, Base
from routers import user, points, generation, chat, payment
from config import settings

# 数据库初始化
def create_tables():
    """创建数据库表"""
    # Base.metadata.create_all会检查表是否存在，只创建不存在的表。
    # 这在生产环境中是安全的，不会删除现有数据。
    # 如需进行表结构变更，请使用Alembic等数据库迁移工具。
    try:
        print("🚀 正在检查并创建数据库表...")
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表检查和创建完成")
    except Exception as e:
        print(f"❌ 数据库表操作失败: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建数据库表
    create_tables()
    yield
    # 关闭时的清理操作
    print("应用关闭")

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="用户管理后端API系统",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含用户路由
app.include_router(user.router, prefix="/api/v1")
# 包含积分路由
app.include_router(points.router, prefix="/api/v1")
# 包含内容生成路由
app.include_router(generation.router, prefix="/api/v1")
# 包含聊天路由
app.include_router(chat.router, prefix="/api/v1")
# 包含支付路由
app.include_router(payment.router, prefix="/api/v1")

# 根路径
@app.get("/")
async def root():
    """根路径信息"""
    return {
        "message": "欢迎使用用户管理后端API",
        "version": settings.API_VERSION,
        "project": settings.PROJECT_NAME
    }

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "message": "服务运行正常"}

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "message": str(exc) if settings.DEBUG else "Internal server error"
        }
    )

if __name__ == "__main__":
    import argparse
    import ssl
    from pathlib import Path
    import os
    
    parser = argparse.ArgumentParser(description="启动Dream Backend API服务器")
    parser.add_argument("--https", action="store_true", help="启用HTTPS")
    parser.add_argument("--host", default="0.0.0.0", help="绑定主机地址")
    parser.add_argument("--port", type=int, default=8000, help="端口号")
    parser.add_argument("--reload", action="store_true", help="启用热重载")
    parser.add_argument("--ssl-cert", help="SSL证书文件路径")
    parser.add_argument("--ssl-key", help="SSL私钥文件路径")
    
    args = parser.parse_args()
    
    if args.https:
        # 获取SSL证书路径（优先级：命令行参数 > 环境变量 > 默认路径）
        ssl_cert_path = (
            args.ssl_cert or 
            os.getenv('SSL_CERT_PATH') or 
            'certs/server.crt'
        )
        ssl_key_path = (
            args.ssl_key or 
            os.getenv('SSL_KEY_PATH') or 
            'certs/server.key'
        )
        
        cert_file = Path(ssl_cert_path)
        key_file = Path(ssl_key_path)
        
        if not cert_file.exists() or not key_file.exists():
            print("❌ SSL证书文件不存在")
            print(f"📁 证书路径: {cert_file.absolute()}")
            print(f"🔑 私钥路径: {key_file.absolute()}")
            print("💡 请确保证书文件存在，或通过以下方式指定：")
            print("   1. 命令行参数: --ssl-cert /path/to/cert.pem --ssl-key /path/to/key.pem")
            print("   2. 环境变量: SSL_CERT_PATH=/path/to/cert.pem SSL_KEY_PATH=/path/to/key.pem")
            print("   3. 默认路径: certs/server.crt 和 certs/server.key")
            exit(1)
        
        print(f"🔒 启动HTTPS服务器: https://{args.host}:{args.port}")
        print(f"📜 使用证书: {cert_file.absolute()}")
        print(f"🔑 使用私钥: {key_file.absolute()}")
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            ssl_keyfile=str(key_file),
            ssl_certfile=str(cert_file),
            log_level="info"
        )
    else:
        print(f"🌐 启动HTTP服务器: http://{args.host}:{args.port}")
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )