"""nginx.conf 自动生成服务"""
import os
import json
from pathlib import Path


CONFIGS_DIR = Path(os.environ.get("CONFIGS_DIR", "/app/configs"))
NGINX_CONF_PATH = Path(os.environ.get("NGINX_CONF_PATH", "/app/nginx.conf"))

# 从配置名推导nginx路径的映射规则
# pet_breed -> /mcp/pet/breed
# bird_detect -> /mcp/bird/detect
# insurance -> /mcp/insurance
# medical_listing -> /mcp/medical/listing
# general -> /mcp/general
# certificate -> /mcp/certificate
# invoice_financial -> /mcp/invoice/financial
# invoice_tax -> /mcp/invoice/tax
# vehicle -> /mcp/vehicle

CATEGORY_MAP = {
    "pet": "pet",
    "bird": "bird",
    "medical": "medical",
    "invoice": "invoice",
}


def config_name_to_nginx_path(name: str) -> str:
    """根据配置名推导nginx路径"""
    parts = name.split("_")

    # 特殊处理: invoice_financial, invoice_tax
    if len(parts) >= 2 and parts[0] == "invoice":
        return f"/mcp/invoice/{parts[1]}"

    # 特殊处理: 医疗类 (medical_listing, medical_record, ...)
    if len(parts) >= 2 and parts[0] == "medical":
        return f"/mcp/medical/{parts[1]}"

    # 通用处理: pet_breed -> /mcp/pet/breed
    if len(parts) >= 2:
        return f"/mcp/{parts[0]}/{parts[1]}"

    # 单个词: insurance, general, certificate, vehicle
    return f"/mcp/{name}"


def generate_nginx_conf() -> str:
    """从configs/目录读取nginx_enabled=true的配置，生成完整nginx.conf"""
    configs = {}
    if CONFIGS_DIR.exists():
        for f in CONFIGS_DIR.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8-sig") as fp:
                    data = json.load(fp)
                    if data.get("nginx_enabled", False):
                        configs[f.stem] = data
            except Exception:
                continue

    locations = []

    # Admin API 路由
    locations.append(
        "        location /mcp/api/ { "
        "set $admin_upstream mcp-admin:9001; "
        "rewrite ^/mcp/api(.*)$ /api$1 break; "
        "proxy_pass http://$admin_upstream; "
        "proxy_set_header Host $host; "
        "proxy_set_header X-Real-IP $remote_addr; "
        "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; }"
    )

    for name in sorted(configs.keys()):
        nginx_path = config_name_to_nginx_path(name)
        location_block = (
            f"        location = {nginx_path} {{ "
            f"set $upstream {name}:8000; "
            f"rewrite ^{nginx_path}$ /mcp break; "
            f"proxy_pass http://$upstream; "
            f"proxy_set_header Host $host; "
            f"proxy_set_header X-Real-IP $remote_addr; "
            f"proxy_http_version 1.1; "
            f"proxy_set_header Upgrade $http_upgrade; "
            f'proxy_set_header Connection "upgrade"; }}'
        )
        locations.append(location_block)

    nginx_conf = f"""events {{
    worker_connections 1024;
}}

http {{
    resolver 127.0.0.11 valid=10s ipv6=off;

    server {{
        listen 80;
{chr(10).join(locations)}
    }}
}}
"""
    return nginx_conf


def write_nginx_conf():
    """生成并写入nginx.conf"""
    content = generate_nginx_conf()
    NGINX_CONF_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(NGINX_CONF_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    return content
