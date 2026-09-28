"""JSON配置文件读写服务"""
import json
import os
from pathlib import Path
from typing import Any

from models.schemas import MCPConfig, Tool, Parameter


CONFIGS_DIR = Path(os.environ.get("CONFIGS_DIR", "/app/configs"))


def list_all_configs() -> dict[str, dict]:
    """读取configs目录下所有JSON配置"""
    configs = {}
    if not CONFIGS_DIR.exists():
        return configs
    for f in CONFIGS_DIR.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8-sig") as fp:
                configs[f.stem] = json.load(fp)
        except Exception:
            continue
    return configs


def get_config(name: str) -> dict | None:
    """读取单个配置文件"""
    config_path = CONFIGS_DIR / f"{name}.json"
    if not config_path.exists():
        return None
    with open(config_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_config(name: str, config: dict):
    """写入配置文件"""
    CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    config_path = CONFIGS_DIR / f"{name}.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def delete_config(name: str) -> bool:
    """删除配置文件"""
    config_path = CONFIGS_DIR / f"{name}.json"
    if config_path.exists():
        config_path.unlink()
        return True
    return False


def config_exists(name: str) -> bool:
    """检查配置是否存在"""
    return (CONFIGS_DIR / f"{name}.json").exists()


def set_nginx_enabled(name: str, enabled: bool) -> bool:
    """设置nginx启用状态"""
    config = get_config(name)
    if not config:
        return False
    config["nginx_enabled"] = enabled
    save_config(name, config)
    return True


def get_nginx_enabled_configs() -> list[str]:
    """获取所有nginx_enabled=true的配置名"""
    result = []
    for name, config in list_all_configs().items():
        if config.get("nginx_enabled", False):
            result.append(name)
    return result


# ---- Tool 操作 ----

def get_tools(name: str) -> list[dict]:
    """获取配置内所有Tool"""
    config = get_config(name)
    if not config:
        return []
    return config.get("tools", [])


def get_tool(config_name: str, tool_name: str) -> dict | None:
    """获取单个Tool"""
    config = get_config(config_name)
    if not config:
        return None
    for tool in config.get("tools", []):
        if tool["name"] == tool_name:
            return tool
    return None


def add_tool(config_name: str, tool: dict) -> bool:
    """添加Tool到配置"""
    config = get_config(config_name)
    if not config:
        return False
    if "tools" not in config:
        config["tools"] = []
    config["tools"].append(tool)
    save_config(config_name, config)
    return True


def update_tool(config_name: str, tool_name: str, tool: dict) -> bool:
    """更新Tool"""
    config = get_config(config_name)
    if not config:
        return False
    for i, t in enumerate(config.get("tools", [])):
        if t["name"] == tool_name:
            config["tools"][i] = tool
            save_config(config_name, config)
            return True
    return False


def delete_tool(config_name: str, tool_name: str) -> bool:
    """删除Tool"""
    config = get_config(config_name)
    if not config:
        return False
    tools = config.get("tools", [])
    new_tools = [t for t in tools if t["name"] != tool_name]
    if len(new_tools) == len(tools):
        return False
    config["tools"] = new_tools
    save_config(config_name, config)
    return True


# ---- 参数操作 ----

def get_parameters(config_name: str, tool_name: str) -> list[dict]:
    """获取Tool所有参数"""
    tool = get_tool(config_name, tool_name)
    if not tool:
        return []
    return tool.get("parameters", [])


def add_parameter(config_name: str, tool_name: str, param: dict) -> bool:
    """添加参数"""
    config = get_config(config_name)
    if not config:
        return False
    for tool in config.get("tools", []):
        if tool["name"] == tool_name:
            if "parameters" not in tool:
                tool["parameters"] = []
            tool["parameters"].append(param)
            save_config(config_name, config)
            return True
    return False


def update_parameter(config_name: str, tool_name: str, param_name: str, param: dict) -> bool:
    """更新参数"""
    config = get_config(config_name)
    if not config:
        return False
    for tool in config.get("tools", []):
        if tool["name"] == tool_name:
            for i, p in enumerate(tool.get("parameters", [])):
                if p["python_name"] == param_name:
                    tool["parameters"][i] = param
                    save_config(config_name, config)
                    return True
    return False


def delete_parameter(config_name: str, tool_name: str, param_name: str) -> bool:
    """删除参数"""
    config = get_config(config_name)
    if not config:
        return False
    for tool in config.get("tools", []):
        if tool["name"] == tool_name:
            params = tool.get("parameters", [])
            new_params = [p for p in params if p["python_name"] != param_name]
            if len(new_params) == len(params):
                return False
            tool["parameters"] = new_params
            save_config(config_name, config)
            return True
    return False
