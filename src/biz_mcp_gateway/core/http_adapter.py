"""统一HTTP调用适配器"""
import os
import logging
import httpx
from typing import Optional

from fastmcp.server.dependencies import get_http_headers

logger = logging.getLogger(__name__)


class HttpAdapter:
    def __init__(self, token_source: str = "both"):
        """
        Args:
            token_source: token来源
                - "env": 只从环境变量TOKEN读取
                - "header": 从请求头Authorization读取
                - "both": 优先请求头，其次环境变量
        """
        self.client = None
        self.token_source = token_source

    def _get_token(self, param_token: Optional[str] = None) -> str:
        """根据token_source获取token"""
        env_token = os.environ.get("TOKEN", "")

        if self.token_source == "env":
            return env_token
        elif self.token_source == "header":
            return self._get_token_from_header()
        else:
            return self._get_token_from_header() or env_token
    
    def _get_token_from_header(self) -> str:
        """从请求头Authorization获取token"""
        try:
            headers = get_http_headers(include={"authorization"})
            auth = headers.get("authorization", "")
            # 去掉 Bearer 前缀
            if auth.startswith("Bearer "):
                auth = auth[7:]
            return auth
        except Exception:
            return ""

    async def request(
        self,
        method: str,
        path: str,
        params: dict,
        content_type: str,
        api_base: str,
        timeout: int = 30,
    ) -> dict:
        """统一HTTP请求"""
        url = f"{api_base}{path}"

        # 根据token_source获取token
        final_token = self._get_token()
        if final_token:
            params["token"] = final_token

        logger.info(f"[REQUEST] {method} {path}")
        logger.info(f"  token_source={self.token_source}, final_token={final_token[:10] if final_token else None}...")
        # 日志中截断图片base64
        log_params = {}
        for k, v in params.items():
            if k in ("imgBase64", "imageBase64") and isinstance(v, str) and len(v) > 10:
                log_params[k] = v[:10] + "..."
            else:
                log_params[k] = v
        logger.info(f"  params={log_params}")

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if content_type == "json":
                    resp = await client.request(method, url, json=params)
                else:
                    resp = await client.request(method, url, data=params)

                logger.info(f"[RESPONSE] status={resp.status_code}")
                logger.info(f"  body={resp.text[:500]}")

                resp.raise_for_status()
                return resp.json()

        except httpx.TimeoutException:
            logger.error(f"[ERROR] 请求超时: {path}")
            return {"error": "请求超时，请稍后重试"}
        except httpx.HTTPStatusError as e:
            logger.error(f"[ERROR] HTTP错误: status={e.response.status_code}")
            return {"error": f"服务端返回错误: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"[ERROR] 请求异常: {str(e)}")
            return {"error": f"请求异常: {str(e)}"}
