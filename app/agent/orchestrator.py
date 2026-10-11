"""Agent 编排：意图解析 → 任务规划 → 步骤执行 → 写入双通道

MVP 阶段：不依赖 pi-agent，直接用规则 + Mock 工具跑通链路。
后续替换：将每个 step 替换为 pi-agent 的 Tool Calling。
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncIterator

from app.core.models import Dataset, WriteResult
from app.sinks.base import SinkRegistry
from app.tools.mock_extract import mock_extract


@dataclass
class StepEvent:
    """Agent 执行流中的一个事件（前端可订阅）"""
    type: str                              # "plan" / "extract" / "write" / "done" / "error"
    step: int | None = None
    total: int | None = None
    title: str | None = None
    detail: str | None = None
    result: WriteResult | None = None
    error: str | None = None


# 简单的意图解析规则（后续替换为 pi-agent Router）
# 每条规则：(关键词子串, 匹配的 dataset key)
_INTENT_RULES = [
    ("京东", "jd_蓝牙耳机"),
    ("蓝牙耳机", "jd_蓝牙耳机"),
    ("飞书任务", "feishu_任务"),
]


def parse_intent(user_input: str) -> tuple[str, str]:
    """返回 (extract_query, dataset_name)

    匹配规则：用户输入包含关键词 → 返回对应数据集
    """
    for keyword, dataset_key in _INTENT_RULES:
        if keyword in user_input:
            return keyword, dataset_key

    # 兜底：把整句作为 query
    return user_input, user_input[:20]


def plan_writes(user_input: str) -> list[dict]:
    """根据用户指令推断要写入哪些 sink

    规则：
      - 提到 "飞书" 或 "文档" -> feishu_doc
      - 提到 "mysql" / "数据库" / "表" -> mysql
      - 都没提 -> 默认双通道都写（演示用途）
    """
    targets = []
    if any(k in user_input for k in ["飞书", "文档", "doc", "feishu"]):
        targets.append({"sink": "feishu_doc", "target": "mock_doc_001", "mode": "append"})
    if any(k in user_input for k in ["mysql", "数据库", "表"]):
        targets.append({"sink": "mysql", "target": "datapilot.competitor_prices", "mode": "upsert"})

    if not targets:
        # 默认演示：双通道都写
        targets = [
            {"sink": "feishu_doc", "target": "mock_doc_001", "mode": "append"},
            {"sink": "mysql", "target": "datapilot.competitor_prices", "mode": "upsert"},
        ]
    return targets


async def run_agent(user_input: str) -> AsyncIterator[StepEvent]:
    """主入口：流式产出执行事件

    完整流程：
      1. 意图解析
      2. 任务规划
      3. Mock 抓取
      4. 多通道写入
      5. 汇总
    """
    # Step 1: 意图解析
    yield StepEvent(type="plan", step=1, total=4, title="意图解析", detail=f'输入: "{user_input}"')
    await asyncio.sleep(0.1)
    query, dataset_name = parse_intent(user_input)

    # Step 2: 规划写入
    yield StepEvent(type="plan", step=2, total=4, title="任务规划", detail=f'查询 "{query}" → 写入 {len(plan_writes(user_input))} 个目标')
    await asyncio.sleep(0.1)
    write_targets = plan_writes(user_input)

    # Step 3: 抓取
    yield StepEvent(type="extract", step=3, total=4, title="浏览器抓取", detail="调用插件 mock_extract")
    dataset: Dataset = await mock_extract(query)
    yield StepEvent(
        type="extract",
        step=3,
        total=4,
        title="抓取完成",
        detail=f'{dataset.name}: {len(dataset.rows)} 行 / {len(dataset.fields)} 列',
    )

    # Step 4: 多通道写入
    results: list[WriteResult] = []
    for i, t in enumerate(write_targets):
        yield StepEvent(
            type="write",
            step=4,
            total=4,
            title=f'写入 {t["sink"]}',
            detail=f'目标: {t["target"]} ({len(dataset.rows)} 行)',
        )
        sink = SinkRegistry.get(t["sink"])
        result = await sink.write(dataset, t["target"], mode=t.get("mode", "append"))
        results.append(result)
        yield StepEvent(
            type="write",
            step=4,
            total=4,
            title=f'{t["sink"]} 写入完成',
            detail=f'rows={result.rows_written}, mock={result.mock}',
            result=result,
        )

    # 完成
    yield StepEvent(
        type="done",
        step=4,
        total=4,
        title="任务完成",
        detail=f'共 {len(results)} 个目标写入成功',
    )
