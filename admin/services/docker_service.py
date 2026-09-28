"""Docker容器管理服务"""
import os
import subprocess
from pathlib import Path

import docker


MCP_IMAGE = os.environ.get("MCP_IMAGE", "biz-mcp-gateway")
MCP_NETWORK = os.environ.get("MCP_NETWORK", "mcp_default")
NGINX_CONTAINER = os.environ.get("NGINX_CONTAINER", "mcp-nginx-1")


def _get_compose_path() -> str:
    return os.environ.get("COMPOSE_PATH", "/app/docker-compose.yml")


def _run_compose(args: list[str], timeout: int = 120) -> tuple[bool, str]:
    """执行docker-compose命令，返回(success, output)"""
    compose_path = _get_compose_path()
    if not Path(compose_path).exists():
        return False, "docker-compose.yml 不存在"

    cmd = ["docker", "compose", "-f", compose_path] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        output = result.stdout or result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, f"操作超时({timeout}s)"
    except Exception as e:
        return False, str(e)


def _ensure_compose():
    """确保docker-compose.yml存在且最新"""
    from services import compose_service
    compose_service.write_compose()


# ========== 列表/状态 ==========

def list_mcp_containers() -> list[dict]:
    """列出所有MCP相关容器"""
    success, output = _run_compose(["ps", "--format", "json"])
    if not success:
        return []

    containers = []
    import json, re
    # 按 "},{" 分割粘连的JSON，再逐个加回花括号解析
    parts = re.split(r'\}\s*\{', output.strip())
    for part in parts:
        part = part.strip()
        if not part.startswith('{'):
            part = '{' + part
        if not part.endswith('}'):
            part = part + '}'
        try:
            item = json.loads(part)
            containers.append({
                "name": item.get("Name", ""),
                "state": item.get("State", "unknown"),
                "config_name": item.get("Service", ""),
                "cpu_percent": 0,
                "memory_mb": 0,
                "created_at": item.get("CreatedAt", ""),
            })
        except Exception:
            continue
    return containers


def get_container_state(config_name: str) -> str:
    """获取指定配置对应的容器状态"""
    success, output = _run_compose(["ps", "-q", config_name])
    if not success or not output.strip():
        return "not_created"
    # 检查是否在运行
    success2, output2 = _run_compose(["ps", "--format", "{{.State}}", config_name])
    if success2 and output2.strip():
        return output2.strip().splitlines()[0]
    return "stopped"


def get_all_container_states() -> dict[str, str]:
    """一次遍历获取所有配置的容器状态"""
    success, output = _run_compose(["ps", "--format", "json"])
    states = {}
    if not success:
        return states
    import json, re
    parts = re.split(r'\}\s*\{', output.strip())
    for part in parts:
        part = part.strip()
        if not part.startswith('{'):
            part = '{' + part
        if not part.endswith('}'):
            part = part + '}'
        try:
            item = json.loads(part)
            service = item.get("Service", "")
            if service:
                states[service] = item.get("State", "unknown")
        except Exception:
            continue
    return states


# ========== 监控 ==========

def get_container_stats(config_name: str) -> dict:
    """获取单个容器的CPU/内存（慢，按需调用）"""
    try:
        client = docker.from_env()
        # docker-compose容器名格式: {项目名}-{服务名}-{副本}
        # 尝试多种可能的容器名
        compose_project = Path(_get_compose_path()).parent.name
        possible_names = [
            f"{compose_project}-{config_name}-1",
            config_name,
        ]
        container = None
        for name in possible_names:
            try:
                container = client.containers.get(name)
                break
            except docker.errors.NotFound:
                continue
        if not container or container.status != "running":
            return {"cpu_percent": 0, "memory_mb": 0}
        raw = container.stats(stream=False)
        mem = raw["memory_stats"].get("usage", 0) - raw["memory_stats"].get("stats", {}).get("inactive_file", 0)
        memory_mb = round(mem / 1024 / 1024, 2)
        cpu_delta = raw["cpu_stats"]["cpu_usage"]["total_usage"] - raw["precpu_stats"]["cpu_usage"]["total_usage"]
        sys_delta = raw["cpu_stats"]["system_cpu_usage"] - raw["precpu_stats"]["system_cpu_usage"]
        cpu_count = raw["cpu_stats"]["online_cpus"]
        cpu_percent = round((cpu_delta / sys_delta) * cpu_count * 100, 2) if sys_delta > 0 else 0
        return {"cpu_percent": cpu_percent, "memory_mb": memory_mb}
    except Exception:
        return {"cpu_percent": 0, "memory_mb": 0}


# ========== 容器操作 ==========

def create_and_start(config_name: str) -> dict:
    """用docker-compose创建并启动容器"""
    _ensure_compose()
    success, output = _run_compose(["up", "-d", config_name], timeout=120)
    if success:
        return {"success": True, "message": f"容器 {config_name} 已创建并启动"}
    return {"success": False, "message": output}


def stop_container(config_name: str) -> dict:
    """停止容器"""
    success, output = _run_compose(["stop", config_name])
    if success:
        return {"success": True, "message": f"容器 {config_name} 已停止"}
    return {"success": False, "message": output}


def remove_container(config_name: str) -> dict:
    """删除容器"""
    success, output = _run_compose(["rm", "-f", config_name])
    if success:
        return {"success": True, "message": f"容器 {config_name} 已删除"}
    return {"success": False, "message": output}


def restart_container(config_name: str) -> dict:
    """重启容器"""
    success, output = _run_compose(["restart", config_name])
    if success:
        return {"success": True, "message": f"容器 {config_name} 已重启"}
    return {"success": False, "message": output}


def batch_compose(names: list[str], action: str) -> dict:
    """批量操作容器: up/stop/restart"""
    _ensure_compose()
    cmd_args = [action]
    if action == "up":
        cmd_args.append("-d")
    cmd_args.extend(names)
    success, output = _run_compose(cmd_args, timeout=300)
    if success:
        return {"success": True, "message": "操作完成"}
    return {"success": False, "message": output}


def get_logs(config_name: str, tail: int = 100) -> str:
    """获取容器日志"""
    success, output = _run_compose(["logs", "--tail", str(tail), config_name])
    if success:
        return output
    return f"获取日志失败: {output}"


# ========== Nginx管理（保持Docker SDK） ==========

def get_client():
    return docker.from_env()


def remove_from_nginx(config_name: str):
    """从nginx配置中移除服务"""
    from services import nginx_service
    nginx_service.write_nginx_conf()


def reload_nginx() -> dict:
    """重载nginx配置，如果nginx没启动则先启动"""
    client = get_client()
    try:
        nginx = client.containers.get(NGINX_CONTAINER)
        if nginx.status != "running":
            nginx.start()
        nginx.exec_run("nginx -s reload")
        return {"success": True, "message": "nginx 已重载"}
    except docker.errors.NotFound:
        return _create_nginx(client)
    except Exception as e:
        return {"success": False, "message": f"nginx重载失败: {str(e)}"}


def _create_nginx(client) -> dict:
    """创建nginx容器"""
    try:
        nginx_conf_host = os.environ.get("NGINX_CONF_HOST", "")
        volumes = {}
        if nginx_conf_host and Path(nginx_conf_host).exists():
            volumes[nginx_conf_host] = {"bind": "/etc/nginx/nginx.conf", "mode": "ro"}

        container = client.containers.run(
            "nginx",
            name=NGINX_CONTAINER,
            ports={"80/tcp": 8000},
            volumes=volumes if volumes else None,
            network=MCP_NETWORK,
            detach=True,
            restart_policy={"Name": "unless-stopped"},
        )
        return {"success": True, "message": "nginx 容器已创建并启动"}
    except docker.errors.Conflict:
        try:
            nginx = client.containers.get(NGINX_CONTAINER)
            if nginx.status != "running":
                nginx.start()
            return {"success": True, "message": "nginx 容器已存在，已启动"}
        except Exception as e:
            return {"success": False, "message": f"nginx启动失败: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"nginx创建失败: {str(e)}"}


def get_nginx_status() -> dict:
    """获取nginx状态"""
    client = get_client()
    try:
        nginx = client.containers.get(NGINX_CONTAINER)
        return {"exists": True, "state": nginx.status, "name": nginx.name}
    except docker.errors.NotFound:
        return {"exists": False, "state": "not_created", "name": NGINX_CONTAINER}


def start_nginx() -> dict:
    """启动nginx"""
    client = get_client()
    try:
        nginx = client.containers.get(NGINX_CONTAINER)
        if nginx.status == "running":
            return {"success": True, "message": "nginx 已在运行"}
        nginx.start()
        return {"success": True, "message": "nginx 已启动"}
    except docker.errors.NotFound:
        return _create_nginx(client)


def stop_nginx() -> dict:
    """停止nginx"""
    client = get_client()
    try:
        nginx = client.containers.get(NGINX_CONTAINER)
        if nginx.status != "running":
            return {"success": True, "message": "nginx 未运行"}
        nginx.stop(timeout=5)
        return {"success": True, "message": "nginx 已停止"}
    except docker.errors.NotFound:
        return {"success": True, "message": "nginx 不存在"}
