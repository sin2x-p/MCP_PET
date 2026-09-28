"""MCP管理平台 - FastAPI入口"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# 加载.env配置
_env_file = Path(__file__).parent / ".env.current"
env = _env_file.read_text().strip() if _env_file.exists() else "dev"
env_file = Path(__file__).parent / f".env.{env}"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[Admin] 加载配置: {env_file.name}")
else:
    print(f"[Admin] 警告: {env_file} 不存在，使用系统环境变量")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import configs, tools, parameters, containers
from services import nginx_service, compose_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化"""
    print("[Admin] 生成 nginx.conf ...")
    nginx_service.write_nginx_conf()
    print("[Admin] 同步 docker-compose.yml ...")
    compose_service.write_compose()
    print("[Admin] 初始化完成")
    yield
    print("[Admin] 关闭")


app = FastAPI(
    title="MCP 管理平台",
    description="MCP服务配置管理、Tool管理、参数管理、容器生命周期管理",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(configs.router)
app.include_router(tools.router)
app.include_router(parameters.router)
app.include_router(containers.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("ADMIN_PORT", "9001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
