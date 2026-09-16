"""MCP Server入口"""
import os
import sys
import logging
from fastmcp import FastMCP

from biz_mcp_gateway.core.config_loader import ConfigLoader
from biz_mcp_gateway.core.tool_registry import ToolRegistry
from biz_mcp_gateway.core.http_adapter import HttpAdapter
from biz_mcp_gateway.utils.logger import setup_logging

logger = logging.getLogger(__name__)


def parse_args():
    """解析命令行参数，支持环境变量"""
    args = {
        "config_name": os.environ.get("MCP_CONFIG", "all"),
        "mode": os.environ.get("MCP_MODE", "stdio"),
        "token_source": os.environ.get("TOKEN_SOURCE", "header"),
    }
    
    for arg in sys.argv[1:]:
        if arg == "http":
            args["mode"] = "http"
        elif arg.startswith("--token-source="):
            args["token_source"] = arg.split("=", 1)[1]
        elif not arg.startswith("-"):
            args["config_name"] = arg
    
    return args


def main():
    """主入口"""
    # 解析参数
    args = parse_args()
    config_name = args["config_name"]
    mode = args["mode"]
    token_source = args["token_source"]
    
    # 设置默认环境变量（如果未设置）
    if not os.environ.get("API_BASE"):
        os.environ["API_BASE"] = "https://ai.inspirvision.cn/s"
    
    # 配置日志
    setup_logging(os.environ.get("LOG_LEVEL", "INFO"))
    
    logger.info(f"Config: {config_name}, Mode: {mode}, Token Source: {token_source}")
    
    # 初始化组件
    mcp = FastMCP(
        name=os.environ.get("MCP_NAME", "biz-mcp-gateway"),
        version=os.environ.get("MCP_VERSION", "1.0.0")
    )
    http_adapter = HttpAdapter(token_source=token_source)
    config_loader = ConfigLoader()
    tool_registry = ToolRegistry(mcp, http_adapter, token_source=token_source)
    
    # 加载配置并注册Tool
    if config_name == "all":
        configs = config_loader.load_all()
    else:
        configs = {config_name: config_loader.load(config_name)}
    
    total_tools = 0
    for name, config in configs.items():
        count = tool_registry.register_from_config(config)
        total_tools += count
        logger.info(f"注册配置 [{name}]: {count} 个Tool")
    
    logger.info(f"共注册 {total_tools} 个Tool")
    
    # 启动服务
    if mode == "http":
        # http 模式：本地部署或自有服务器
        logger.info("Starting biz-mcp-gateway (http mode) ...")
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=8000,
            path="/mcp",
        )
    else:
        # stdio 模式：魔搭等云平台托管
        logger.info("Starting biz-mcp-gateway (stdio mode) ...")
        mcp.run()


if __name__ == "__main__":
    main()
