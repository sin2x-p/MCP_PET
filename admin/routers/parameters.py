"""参数CRUD路由"""
from fastapi import APIRouter, HTTPException

from services import config_service, docker_service

router = APIRouter(
    prefix="/api/configs/{config_name}/tools/{tool_name}/params",
    tags=["parameters"],
)


@router.get("")
async def list_params(config_name: str, tool_name: str):
    """获取Tool所有参数"""
    if not config_service.config_exists(config_name):
        raise HTTPException(status_code=404, detail=f"配置 {config_name} 不存在")
    tool = config_service.get_tool(config_name, tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} 不存在")
    return tool.get("parameters", [])


@router.post("")
async def add_param(config_name: str, tool_name: str, param: dict):
    """添加参数"""
    if not config_service.config_exists(config_name):
        raise HTTPException(status_code=404, detail=f"配置 {config_name} 不存在")
    tool = config_service.get_tool(config_name, tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} 不存在")

    if not param.get("python_name"):
        raise HTTPException(status_code=400, detail="python_name 不能为空")
    if not param.get("http_field"):
        raise HTTPException(status_code=400, detail="http_field 不能为空")

    for p in tool.get("parameters", []):
        if p["python_name"] == param["python_name"]:
            raise HTTPException(status_code=400, detail=f"参数 {param['python_name']} 已存在")

    config_service.add_parameter(config_name, tool_name, param)

    result = docker_service.restart_container(config_name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return {"success": True, "message": f"参数 {param['python_name']} 已添加，容器已重启"}


@router.put("/{param_name}")
async def update_param(config_name: str, tool_name: str, param_name: str, param: dict):
    """更新参数"""
    if not config_service.config_exists(config_name):
        raise HTTPException(status_code=404, detail=f"配置 {config_name} 不存在")
    tool = config_service.get_tool(config_name, tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} 不存在")

    found = False
    for p in tool.get("parameters", []):
        if p["python_name"] == param_name:
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail=f"参数 {param_name} 不存在")

    config_service.update_parameter(config_name, tool_name, param_name, param)

    result = docker_service.restart_container(config_name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return {"success": True, "message": f"参数 {param_name} 已更新，容器已重启"}


@router.delete("/{param_name}")
async def delete_param(config_name: str, tool_name: str, param_name: str):
    """删除参数"""
    if not config_service.config_exists(config_name):
        raise HTTPException(status_code=404, detail=f"配置 {config_name} 不存在")
    tool = config_service.get_tool(config_name, tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} 不存在")

    result = config_service.delete_parameter(config_name, tool_name, param_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"参数 {param_name} 不存在")

    restart_result = docker_service.restart_container(config_name)
    if not restart_result["success"]:
        raise HTTPException(status_code=500, detail=restart_result["message"])

    return {"success": True, "message": f"参数 {param_name} 已删除，容器已重启"}
