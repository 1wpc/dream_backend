from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from database import engine, Base
from routers import user
from config import settings

# 数据库初始化
def create_tables():
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建数据库表
    create_tables()
    print("数据库表创建成功")
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
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 