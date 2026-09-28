"""Pydantic数据模型"""
from pydantic import BaseModel, Field
from typing import Any, Optional


class Parameter(BaseModel):
    python_name: str
    http_field: str
    type: str = "string"
    required: bool = False
    default: Any = ""
    description: str = ""
    location: str = "body"


class HttpConfig(BaseModel):
    method: str = "POST"
    path: str
    content_type: str = "form-data"


class Tool(BaseModel):
    name: str
    description: str
    category: str = ""
    http: HttpConfig
    parameters: list[Parameter] = []


class ServerConfig(BaseModel):
    api_base: str = "https://ai.inspirvision.cn/s"
    timeout: int = 30


class Metadata(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str


class MCPConfig(BaseModel):
    metadata: Metadata
    server: ServerConfig = ServerConfig()
    tools: list[Tool] = []


class ConfigListItem(BaseModel):
    name: str
    description: str = ""
    tool_count: int = 0
    nginx_path: str = ""
    container_state: str = "not_created"


class ConfigCreate(BaseModel):
    name: str
    description: str
    api_base: str = "https://ai.inspirvision.cn/s"
    timeout: int = 30
    nginx_path: str = ""


class ContainerStatus(BaseModel):
    name: str
    state: str
    config_name: str
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    nginx_path: str = ""
    created_at: str = ""


class ContainerAction(BaseModel):
    success: bool
    message: str
