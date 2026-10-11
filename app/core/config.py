"""配置加载：.env + 环境变量，支持 Mock 模式"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env（如果存在）
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


def _bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    # 模式开关：true = 所有外部调用走 Mock 适配器
    mock_mode: bool

    # 飞书
    feishu_app_id: str
    feishu_app_secret: str
    feishu_base_url: str

    # MySQL
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str

    # LLM（Mock 模式不需要真实 key）
    llm_api_key: str
    llm_base_url: str
    llm_model: str

    # 服务
    host: str
    port: int

    @classmethod
    def load(cls) -> "Settings":
        return cls(
            mock_mode=_bool(os.getenv("MOCK_MODE"), default=True),
            feishu_app_id=os.getenv("FEISHU_APP_ID", ""),
            feishu_app_secret=os.getenv("FEISHU_APP_SECRET", ""),
            feishu_base_url=os.getenv("FEISHU_BASE_URL", "https://open.feishu.cn/open-apis"),
            mysql_host=os.getenv("MYSQL_HOST", ""),
            mysql_port=int(os.getenv("MYSQL_PORT", "3306")),
            mysql_user=os.getenv("MYSQL_USER", ""),
            mysql_password=os.getenv("MYSQL_PASSWORD", ""),
            mysql_database=os.getenv("MYSQL_DATABASE", ""),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "8765")),
        )


settings = Settings.load()
