FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir fastmcp httpx

COPY src/biz_mcp_gateway /app/biz_mcp_gateway

EXPOSE 8000

CMD ["python", "-m", "biz_mcp_gateway.main"]
