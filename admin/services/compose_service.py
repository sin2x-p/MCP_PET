"""docker-compose.yml 同步服务"""
import os
import json
from pathlib import Path


CONFIGS_DIR = Path(os.environ.get("CONFIGS_DIR", "/app/configs"))
CONFIGS_HOST_DIR = os.environ.get("CONFIGS_HOST_DIR", str(CONFIGS_DIR))
COMPOSE_PATH = Path(os.environ.get("COMPOSE_PATH", "/app/docker-compose.yml"))


def generate_compose() -> dict:
    """从configs/目录读取所有配置，生成docker-compose内容"""
    configs = {}
    if CONFIGS_DIR.exists():
        for f in CONFIGS_DIR.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8-sig") as fp:
                    configs[f.stem] = json.load(fp)
            except Exception:
                continue

    services = {}
    configs_host = CONFIGS_HOST_DIR

    # nginx
    service_names = sorted(configs.keys())
    services["nginx"] = {
        "image": "nginx",
        "volumes": ["./nginx.conf:/etc/nginx/nginx.conf"],
        "ports": ["8000:80"],
        "depends_on": service_names,
    }

    # MCP服务
    for name in service_names:
        services[name] = {
            "image": "biz-mcp-gateway",
            "container_name": name,
            "privileged": True,
            "security_opt": ["seccomp:unconfined", "apparmor:unconfined"],
            "environment": [
                f"MCP_CONFIG={name}",
                "MCP_MODE=http",
                "TOKEN_SOURCE=header",
            ],
            "volumes": [f"{configs_host}:/app/configs:ro"],
        }

    return {"services": services, "networks": {"default": {"external": True, "name": "mcp_default"}}}


def write_compose():
    """生成并写入docker-compose.yml"""
    try:
        import yaml
        content = generate_compose()
        COMPOSE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(COMPOSE_PATH, "w", encoding="utf-8") as f:
            yaml.dump(content, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return content
    except ImportError:
        # 没有pyyaml时用简单字符串拼接
        return _write_compose_fallback()


def _write_compose_fallback():
    """不依赖pyyaml的简单生成"""
    configs = {}
    if CONFIGS_DIR.exists():
        for f in CONFIGS_DIR.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8-sig") as fp:
                    configs[f.stem] = json.load(fp)
            except Exception:
                continue

    service_names = sorted(configs.keys())
    lines = ["services:"]

    # nginx
    lines.append("  nginx:")
    lines.append("    image: nginx")
    lines.append("    volumes:")
    lines.append("      - ./nginx.conf:/etc/nginx/nginx.conf")
    lines.append("    ports:")
    lines.append('      - "8000:80"')
    lines.append("    depends_on:")
    for sn in service_names:
        lines.append(f"      - {sn}")

    # MCP服务
    for name in service_names:
        lines.append(f"  {name}:")
        lines.append(f"    container_name: {name}")
        lines.append("    image: biz-mcp-gateway")
        lines.append("    privileged: true")
        lines.append("    security_opt:")
        lines.append("      - seccomp:unconfined")
        lines.append("      - apparmor:unconfined")
        lines.append("    environment:")
        lines.append(f'      - MCP_CONFIG={name}')
        lines.append("      - MCP_MODE=http")
        lines.append("      - TOKEN_SOURCE=header")
        lines.append("    volumes:")
        lines.append(f"      - {CONFIGS_HOST_DIR}:/app/configs:ro")

    content = "\n".join(lines) + "\n"
    content += "\nnetworks:\n  default:\n    external: true\n    name: mcp_default\n"
    COMPOSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(COMPOSE_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    return content
