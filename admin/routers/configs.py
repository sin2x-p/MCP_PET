"""配置文件CRUD路由"""
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.schemas import MCPConfig, Metadata, ServerConfig, Tool, ConfigListItem, ConfigCreate
from services import config_service, docker_service, nginx_service, compose_service

router = APIRouter(prefix="/api/configs", tags=["configs"])


@router.get("")
async def list_configs():
    """列出所有配置"""
    configs = config_service.list_all_configs()
    states = docker_service.get_all_container_states()
    compose_path = os.environ.get("COMPOSE_PATH", "/app/docker-compose.yml")
    project_name = Path(compose_path).parent.name
    result = []
    for name, config in sorted(configs.items()):
        nginx_path = nginx_service.config_name_to_nginx_path(name)
        result.append({
            "name": name,
            "description": config.get("metadata", {}).get("description", ""),
            "tool_count": len(config.get("tools", [])),
            "nginx_path": nginx_path,
            "container_state": states.get(name, "not_created"),
            "container_name": f"{project_name}-{name}-1",
            "nginx_enabled": config.get("nginx_enabled", False),
        })
    return result


@router.get("/{name}")
async def get_config(name: str):
    """获取单个配置"""
    config = config_service.get_config(name)
    if not config:
        raise HTTPException(status_code=404, detail=f"配置 {name} 不存在")
    return config


@router.post("")
async def create_config(body: ConfigCreate):
    """新增配置"""
    reserved = ["nginx", "admin", "mcp", "all"]
    if body.name in reserved:
        raise HTTPException(status_code=400, detail=f"{body.name} 是保留名，不能使用")

    if config_service.config_exists(body.name):
        raise HTTPException(status_code=400, detail=f"配置 {body.name} 已存在")

    config = {
        "metadata": {
            "name": body.name,
            "version": "1.0.0",
            "description": body.description,
        },
        "server": {
            "api_base": body.api_base,
            "timeout": body.timeout,
        },
        "tools": [],
    }

    config_service.save_config(body.name, config)
    compose_service.write_compose()

    return {"success": True, "message": f"配置 {body.name} 已创建，容器未启动"}


@router.post("/batch/nginx/enable")
async def batch_enable_nginx(names: list[str]):
    """批量添加到nginx"""
    for name in names:
        config_service.set_nginx_enabled(name, True)
    nginx_service.write_nginx_conf()
    result = docker_service.reload_nginx()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return {"success": True, "message": f"已将 {len(names)} 个服务添加到nginx"}


@router.post("/batch/nginx/disable")
async def batch_disable_nginx(names: list[str]):
    """批量从nginx移除"""
    for name in names:
        config_service.set_nginx_enabled(name, False)
    nginx_service.write_nginx_conf()
    result = docker_service.reload_nginx()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return {"success": True, "message": f"已将 {len(names)} 个服务从nginx移除"}


@router.put("/{name}")
async def update_config(name: str, config: dict):
    """更新配置"""
    if not config_service.config_exists(name):
        raise HTTPException(status_code=404, detail=f"配置 {name} 不存在")

    config_service.save_config(name, config)
    result = docker_service.restart_container(name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return {"success": True, "message": f"配置 {name} 已更新，容器已重启"}


@router.delete("/{name}")
async def delete_config(name: str):
    """删除配置"""
    if not config_service.config_exists(name):
        raise HTTPException(status_code=404, detail=f"配置 {name} 不存在")

    config_service.set_nginx_enabled(name, False)
    nginx_service.write_nginx_conf()

    docker_service.stop_container(name)
    docker_service.remove_container(name)

    config_service.delete_config(name)
    compose_service.write_compose()

    docker_service.reload_nginx()

    return {"success": True, "message": f"配置 {name} 已删除，容器已停止"}


@router.post("/{name}/restart")
async def restart_config(name: str):
    """重启容器"""
    if not config_service.config_exists(name):
        raise HTTPException(status_code=404, detail=f"配置 {name} 不存在")

    result = docker_service.restart_container(name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return result


@router.post("/{name}/nginx/enable")
async def enable_nginx(name: str):
    """将服务添加到nginx路由"""
    if not config_service.config_exists(name):
        raise HTTPException(status_code=404, detail=f"配置 {name} 不存在")

    config_service.set_nginx_enabled(name, True)
    nginx_service.write_nginx_conf()
    result = docker_service.reload_nginx()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return {"success": True, "message": f"服务 {name} 已添加到nginx路由"}


@router.post("/{name}/nginx/disable")
async def disable_nginx(name: str):
    """从nginx路由移除服务"""
    if not config_service.config_exists(name):
        raise HTTPException(status_code=404, detail=f"配置 {name} 不存在")

    config_service.set_nginx_enabled(name, False)
    nginx_service.write_nginx_conf()
    result = docker_service.reload_nginx()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return {"success": True, "message": f"服务 {name} 已从nginx路由移除"}


@router.get("/{name}/logs")
async def get_logs(name: str, tail: int = 100):
    """查看容器日志"""
    logs = docker_service.get_logs(name, tail=tail)
    return {"logs": logs}
