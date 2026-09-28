"""Tool CRUD路由"""
from fastapi import APIRouter, HTTPException

from services import config_service, docker_service

router = APIRouter(prefix="/api/configs/{config_name}/tools", tags=["tools"])


@router.get("")
async def list_tools(config_name: str):
    """获取配置内所有Tool"""
    if not config_service.config_exists(config_name):
        raise HTTPException(status_code=404, detail=f"配置 {config_name} 不存在")
    return config_service.get_tools(config_name)


@router.post("")
async def add_tool(config_name: str, tool: dict):
    """添加Tool"""
    if not config_service.config_exists(config_name):
        raise HTTPException(status_code=404, detail=f"配置 {config_name} 不存在")

    if not tool.get("name"):
        raise HTTPException(status_code=400, detail="Tool name 不能为空")
    if not tool.get("http") or not tool["http"].get("path"):
        raise HTTPException(status_code=400, detail="Tool http.path 不能为空")

    existing = config_service.get_tool(config_name, tool["name"])
    if existing:
        raise HTTPException(status_code=400, detail=f"Tool {tool['name']} 已存在")

    if "parameters" not in tool:
        tool["parameters"] = []

    config_service.add_tool(config_name, tool)

    result = docker_service.restart_container(config_name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return {"success": True, "message": f"Tool {tool['name']} 已添加，容器已重启"}


@router.put("/{tool_name}")
async def update_tool(config_name: str, tool_name: str, tool: dict):
    """更新Tool"""
    if not config_service.config_exists(config_name):
        raise HTTPException(status_code=404, detail=f"配置 {config_name} 不存在")

    existing = config_service.get_tool(config_name, tool_name)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} 不存在")

    config_service.update_tool(config_name, tool_name, tool)

    result = docker_service.restart_container(config_name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return {"success": True, "message": f"Tool {tool_name} 已更新，容器已重启"}


@router.delete("/{tool_name}")
async def delete_tool(config_name: str, tool_name: str):
    """删除Tool"""
    if not config_service.config_exists(config_name):
        raise HTTPException(status_code=404, detail=f"配置 {config_name} 不存在")

    existing = config_service.get_tool(config_name, tool_name)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} 不存在")

    config_service.delete_tool(config_name, tool_name)

    result = docker_service.restart_container(config_name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return {"success": True, "message": f"Tool {tool_name} 已删除，容器已重启"}


@router.post("/{tool_name}/move")
async def move_tool(config_name: str, tool_name: str, body: dict):
    """移动Tool到另一个MCP服务"""
    target = body.get("target_config")
    if not target:
        raise HTTPException(status_code=400, detail="target_config 不能为空")
    if not config_service.config_exists(config_name):
        raise HTTPException(status_code=404, detail=f"源配置 {config_name} 不存在")
    if not config_service.config_exists(target):
        raise HTTPException(status_code=404, detail=f"目标配置 {target} 不存在")
    if config_name == target:
        raise HTTPException(status_code=400, detail="源和目标相同")

    tool = config_service.get_tool(config_name, tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} 不存在")

    existing = config_service.get_tool(target, tool_name)
    if existing:
        raise HTTPException(status_code=400, detail=f"目标配置中已存在 Tool {tool_name}")

    config_service.add_tool(target, tool)
    config_service.delete_tool(config_name, tool_name)

    docker_service.restart_container(config_name)
    docker_service.restart_container(target)

    return {"success": True, "message": f"Tool {tool_name} 已从 {config_name} 移动到 {target}"}
