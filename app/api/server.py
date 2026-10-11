"""FastAPI 接口：流式 Agent + 写入结果"""
from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.orchestrator import run_agent, StepEvent
from app.core.config import settings
from app.sinks.base import SinkRegistry
from app.sinks import feishu_doc, mysql  # noqa: F401 触发注册

app = FastAPI(title="DataPilot", version="0.1.0")


class RunRequest(BaseModel):
    input: str


def _event_to_sse(event: StepEvent) -> str:
    """把事件转成 SSE 格式"""
    payload = {
        "type": event.type,
        "step": event.step,
        "total": event.total,
        "title": event.title,
        "detail": event.detail,
        "error": event.error,
    }
    if event.result:
        payload["result"] = {
            "sink": event.result.sink,
            "target": event.result.target,
            "rows_written": event.result.rows_written,
            "document_url": event.result.document_url,
            "sql_preview": (event.result.sql or "")[:200],
            "mock": event.result.mock,
        }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.get("/")
async def root():
    return {
        "name": "DataPilot",
        "version": "0.1.0",
        "mock_mode": settings.mock_mode,
        "sinks": SinkRegistry.all(),
    }


@app.get("/sinks")
async def list_sinks():
    """列出所有已注册的写入目标"""
    return {"sinks": SinkRegistry.all(), "mock_mode": settings.mock_mode}


@app.post("/agent/run")
async def agent_run(req: RunRequest):
    """流式执行 Agent，返回 SSE"""
    async def event_generator() -> AsyncIterator[str]:
        async for event in run_agent(req.input):
            yield _event_to_sse(event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/health")
async def health():
    return {"status": "ok", "mock_mode": settings.mock_mode}
