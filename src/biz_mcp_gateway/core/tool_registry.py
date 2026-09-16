"""动态MCP Tool注册器"""
import logging
from typing import Any, Callable, Optional
from fastmcp import FastMCP

from biz_mcp_gateway.core.http_adapter import HttpAdapter

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self, mcp: FastMCP, http_adapter: HttpAdapter, token_source: str = "both"):
        """
        Args:
            token_source: token来源
                - "env": 只从环境变量读取，不添加token参数
                - "param": 添加token参数（多用户调用）
                - "both": 添加token参数，优先使用传入值（默认）
        """
        self.mcp = mcp
        self.http_adapter = http_adapter
        self.token_source = token_source
    
    def register_from_config(self, config: dict) -> int:
        """从配置注册所有Tool，返回注册数量"""
        tools = config.get("tools", [])
        server_config = config.get("server", {})
        
        for tool_def in tools:
            try:
                self._register_tool(tool_def, server_config)
            except Exception as e:
                logger.error(f"注册Tool [{tool_def.get('name')}] 失败: {e}")
                raise
        
        return len(tools)
    
    def _register_tool(self, tool_def: dict, server_config: dict):
        """注册单个Tool"""
        name = tool_def["name"]
        description = tool_def["description"]
        http_config = tool_def["http"]
        parameters = tool_def.get("parameters", [])
        
        # 使用exec动态创建函数
        func_code = self._generate_function_code(name, description, parameters, http_config, server_config)
        
        # 执行代码创建函数
        namespace = {"http_adapter": self.http_adapter, "Optional": Optional}
        exec(func_code, namespace)
        handler = namespace[name]
        
        # 注册到MCP
        tool = self.mcp.add_tool(handler)
        
        # 添加参数描述
        for p in parameters:
            python_name = p["python_name"]
            if python_name in tool.parameters.get("properties", {}):
                tool.parameters["properties"][python_name]["description"] = p.get("description", "")
        
        # 添加token参数描述
        need_token_param = self.token_source in ("param", "both")
        if need_token_param and "token" in tool.parameters.get("properties", {}):
            tool.parameters["properties"]["token"]["description"] = "本次调用的TOKEN，不传则使用全局TOKEN"
        
        logger.debug(f"注册Tool: {name}")
    
    def _generate_function_code(
        self,
        name: str,
        description: str,
        parameters: list,
        http_config: dict,
        server_config: dict
    ) -> str:
        """生成函数代码"""
        # 构建参数列表
        param_parts = []
        for p in parameters:
            python_name = p["python_name"]
            default = p.get("default", "")
            required = p.get("required", False)
            param_type = p.get("type", "string")
            
            # 映射类型到Python类型
            python_type = self._map_python_type(param_type)
            
            if required:
                param_parts.append(f"{python_name}: {python_type}")
            else:
                # 可选参数，使用默认值
                if param_type == "integer":
                    default_val = int(default) if default != "" else 0
                    param_parts.append(f"{python_name}: {python_type} = {default_val}")
                elif param_type == "number":
                    default_val = float(default) if default != "" else 0.0
                    param_parts.append(f"{python_name}: {python_type} = {default_val}")
                elif param_type == "boolean":
                    default_val = bool(default) if default != "" else False
                    param_parts.append(f"{python_name}: {python_type} = {default_val}")
                else:
                    default_repr = repr(default) if default else '""'
                    param_parts.append(f"{python_name}: {python_type} = {default_repr}")
        
        # 根据token_source决定是否添加token参数
        need_token_param = self.token_source == "both"
        if need_token_param:
            param_parts.append("token: str = \"\"")
        
        params_str = ", ".join(param_parts)
        
        # 构建docstring参数描述
        param_docs = []
        for p in parameters:
            python_name = p["python_name"]
            desc = p.get("description", "")
            param_docs.append(f"    {python_name}: {desc}")
        if need_token_param:
            param_docs.append("    token: 本次调用的TOKEN，不传则使用全局TOKEN")
        
        param_docs_str = "\n".join(param_docs)
        
        # 构建参数映射
        param_mapping = {}
        for p in parameters:
            python_name = p["python_name"]
            http_field = p["http_field"]
            param_mapping[python_name] = http_field
        
        # 构建函数体
        mapping_lines = []
        for python_name, http_field in param_mapping.items():
            mapping_lines.append(f'    if {python_name} is not None:')
            mapping_lines.append(f'        http_params["{http_field}"] = {python_name}')
        
        mapping_str = "\n".join(mapping_lines)
        
        # 调用时传递token
        token_call_arg = ""
        
        # 构建完整函数代码
        func_code = f'''
async def {name}({params_str}) -> dict:
    """
{description}

Args:
{param_docs_str}
"""
    http_params = {{}}
{mapping_str}
    
    return await http_adapter.request(
        method="{http_config['method']}",
        path="{http_config['path']}",
        params=http_params,
        content_type="{http_config.get('content_type', 'form-data')}",
        api_base="{server_config.get('api_base', '')}",
        timeout={server_config.get('timeout', 30)},{token_call_arg}
    )
'''
        
        return func_code
    
    def _map_python_type(self, type_str: str) -> str:
        """映射配置类型到Python类型"""
        type_map = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
        }
        return type_map.get(type_str, "str")
    
    def _map_optional_type(self, type_str: str) -> str:
        """映射配置类型到Optional类型"""
        type_map = {
            "string": "Optional[str]",
            "integer": "Optional[int]",
            "number": "Optional[float]",
            "boolean": "Optional[bool]",
        }
        return type_map.get(type_str, "Optional[str]")
