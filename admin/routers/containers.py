"""容器管理路由"""
from fastapi import APIRouter, HTTPException

from services import docker_service, nginx_service
from services.config_service import set_nginx_enabled

router = APIRouter(prefix="/api/containers", tags=["containers"])


# ---- nginx管理 ----

@router.get("/nginx/status")
async def nginx_status():
    """nginx状态"""
    return docker_service.get_nginx_status()


@router.post("/nginx/start")
async def nginx_start():
    """启动nginx"""
    result = docker_service.start_nginx()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.post("/nginx/stop")
async def nginx_stop():
    """停止nginx"""
    result = docker_service.stop_nginx()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.post("/nginx/reload")
async def nginx_reload():
    """重载nginx配置"""
    result = docker_service.reload_nginx()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result


# ---- 批量操作 ----

@router.post("/batch/start")
async def batch_start(names: list[str]):
    """批量启动容器"""
    result = docker_service.batch_compose(names, "up")
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    for name in names:
        set_nginx_enabled(name, True)
    nginx_service.write_nginx_conf()
    docker_service.reload_nginx()
    result["message"] += "，已自动配置nginx"
    return result


@router.post("/batch/stop")
async def batch_stop(names: list[str]):
    """批量停止容器"""
    from services.config_service import get_config, save_config
    for name in names:
        config = get_config(name)
        if config and config.get("nginx_enabled", False):
            config["nginx_enabled"] = False
            save_config(name, config)
            docker_service.remove_from_nginx(name)
    result = docker_service.batch_compose(names, "stop")
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    docker_service.reload_nginx()
    return result


@router.post("/batch/restart")
async def batch_restart(names: list[str]):
    """批量重启容器"""
    result = docker_service.batch_compose(names, "restart")
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result


# ---- MCP容器管理 ----

@router.get("")
async def list_containers():
    """列出所有MCP容器"""
    containers = docker_service.list_mcp_containers()
    return containers


@router.post("/{config_name}/start")
async def start_container(config_name: str):
    """启动容器"""
    result = docker_service.create_and_start(config_name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    set_nginx_enabled(config_name, True)
    nginx_service.write_nginx_conf()
    docker_service.reload_nginx()
    result["message"] += "，已自动配置nginx"
    return result


@router.post("/{config_name}/stop")
async def stop_container(config_name: str):
    """停止容器"""
    from services.config_service import get_config, save_config
    config = get_config(config_name)
    need_nginx_remove = config is not None and config.get("nginx_enabled", False)
    result = docker_service.stop_container(config_name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    if need_nginx_remove:
        config["nginx_enabled"] = False
        save_config(config_name, config)
        docker_service.remove_from_nginx(config_name)
        docker_service.reload_nginx()
        result["message"] += "，已从nginx移除"
    return result


@router.post("/{config_name}/restart")
async def restart_container(config_name: str):
    """重启容器"""
    result = docker_service.restart_container(config_name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.post("/{config_name}/delete")
async def delete_container(config_name: str):
    """删除容器"""
    from services.config_service import get_config, save_config
    config = get_config(config_name)
    need_nginx_remove = config is not None and config.get("nginx_enabled", False)
    result = docker_service.remove_container(config_name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    if need_nginx_remove:
        config["nginx_enabled"] = False
        save_config(config_name, config)
        docker_service.remove_from_nginx(config_name)
        docker_service.reload_nginx()
        result["message"] += "，已从nginx移除"
    return result


@router.get("/{config_name}/logs")
async def get_logs(config_name: str, tail: int = 100):
    """查看容器日志"""
    logs = docker_service.get_logs(config_name, tail=tail)
    return {"logs": logs}
