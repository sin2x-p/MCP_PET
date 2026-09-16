"""YAML配置加载器"""
import os
import yaml
from pathlib import Path
from typing import Any


class ConfigLoader:
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
    
    def load(self, config_name: str) -> dict:
        """加载指定配置文件"""
        config_path = self.config_dir / f"{config_name}.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # 处理环境变量
        config = self._resolve_env_vars(config)
        return config
    
    def load_all(self) -> dict[str, dict]:
        """加载所有配置文件"""
        configs = {}
        for config_file in self.config_dir.glob("*.yaml"):
            name = config_file.stem
            configs[name] = self.load(name)
        return configs
    
    def _resolve_env_vars(self, obj: Any) -> Any:
        """递归解析环境变量 ${VAR_NAME}"""
        if isinstance(obj, str):
            if obj.startswith("${") and obj.endswith("}"):
                var_name = obj[2:-1]
                return os.environ.get(var_name, "")
            return obj
        elif isinstance(obj, dict):
            return {k: self._resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_vars(item) for item in obj]
        return obj
