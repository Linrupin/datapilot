"""DataPilot 启动入口

使用：python -m app.main
或：uvicorn app.api.server:app --host 127.0.0.1 --port 8765
"""
import uvicorn

from app.core.config import settings


def main():
    print(f"🚀 DataPilot v0.1.0  启动中...")
    print(f"   Mock 模式: {settings.mock_mode}")
    print(f"   监听: http://{settings.host}:{settings.port}")
    uvicorn.run(
        "app.api.server:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
