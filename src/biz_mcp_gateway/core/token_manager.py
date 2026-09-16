"""Token管理器 - 自动获取和刷新Token"""
import os
import time
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)


class TokenManager:
    def __init__(
        self,
        access_key: str = "",
        access_secret: str = "",
        api_base: str = "",
        token_url: str = "/api/getAccessToken"
    ):
        self.access_key = access_key or os.environ.get("ACCESS_KEY", "")
        self.access_secret = access_secret or os.environ.get("ACCESS_SECRET", "")
        self.api_base = api_base or os.environ.get("API_BASE", "https://ai.inspirvision.cn/s")
        self.token_url = token_url
        
        self._token: Optional[str] = None
        self._expire_time: float = 0
        self._refresh_buffer: int = 300  # 提前5分钟刷新
    
    @property
    def token(self) -> str:
        """获取token，如果过期则自动刷新"""
        if self._token is None or time.time() >= self._expire_time:
            self._refresh_token()
        return self._token or ""
    
    def _refresh_token(self):
        """刷新token"""
        if not self.access_key or not self.access_secret:
            logger.warning("未配置ACCESS_KEY或ACCESS_SECRET，跳过token获取")
            return
        
        try:
            url = f"{self.api_base}{self.token_url}"
            data = {
                "accessKey": self.access_key,
                "accessSecret": self.access_secret,
            }
            
            # 同步请求获取token
            resp = httpx.post(url, data=data, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            
            if "token" in result:
                self._token = result["token"]
                # 假设token有效期2小时，提前5分钟刷新
                expire_in = result.get("expireIn", 7200)
                self._expire_time = time.time() + expire_in - self._refresh_buffer
                logger.info(f"Token获取成功，有效期{expire_in}秒")
            else:
                logger.error(f"Token获取失败: {result}")
        
        except Exception as e:
            logger.error(f"Token获取异常: {e}")
    
    def get_token(self) -> str:
        """获取token（供外部调用）"""
        return self.token


# 全局单例
_token_manager: Optional[TokenManager] = None


def get_token_manager() -> TokenManager:
    """获取Token管理器单例"""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager
