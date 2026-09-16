FROM python:3.12-slim

WORKDIR /app

# 复制配置和代码
COPY configs/ ./configs/
COPY src/ ./src/
COPY pyproject.toml .

# 安装依赖
RUN pip install --no-cache-dir .

# 默认环境变量
ENV LOG_LEVEL=INFO
ENV MCP_CONFIG=all
ENV MCP_MODE=http
ENV TOKEN_SOURCE=header

EXPOSE 8000

# 启动
ENTRYPOINT ["python", "-m", "biz_mcp_gateway.main"]
