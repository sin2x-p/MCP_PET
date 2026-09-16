FROM python:3.12-slim

WORKDIR /app

# 复制配置和代码
COPY configs/ ./configs/
COPY src/ ./src/
COPY pyproject.toml .

# 安装依赖
RUN pip install --no-cache-dir .

# 环境变量
ENV API_BASE=https://ai.inspirvision.cn/s
ENV LOG_LEVEL=INFO

EXPOSE 8000

# 启动，通过参数指定配置
ENTRYPOINT ["python", "-m", "biz_mcp_gateway.main"]
CMD ["all"]
