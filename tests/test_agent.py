"""测试 Agent 编排：意图 → 抓取 → 双通道写入"""
import asyncio

import pytest

from app.agent.orchestrator import run_agent, parse_intent, plan_writes
from app.sinks import feishu_doc, mysql  # noqa: F401 触发注册


def test_parse_intent_jd():
    query, name = parse_intent("把京东竞品价格抓下来")
    assert query == "京东"


def test_plan_writes_default():
    """无关键词时默认双通道"""
    targets = plan_writes("随便说点啥")
    sinks = [t["sink"] for t in targets]
    assert "feishu_doc" in sinks
    assert "mysql" in sinks


def test_plan_writes_feishu_only():
    targets = plan_writes("存到飞书文档")
    sinks = [t["sink"] for t in targets]
    assert "feishu_doc" in sinks
    assert "mysql" not in sinks


def test_plan_writes_mysql_only():
    targets = plan_writes("存到 mysql 表里")
    sinks = [t["sink"] for t in targets]
    assert "mysql" in sinks


@pytest.mark.asyncio
async def test_run_agent_full_flow():
    """端到端：用户输入 → 4 步完成 → 双通道写入"""
    events = []
    async for ev in run_agent("把京东竞品价格抓下来存到飞书和mysql"):
        events.append(ev)

    # 至少有 plan, extract, write, done 四类
    types = [e.type for e in events]
    assert "plan" in types
    assert "extract" in types
    assert "write" in types
    assert "done" in types

    # 至少有 1 个 feishu_doc 写入结果 + 1 个 mysql 写入结果
    write_results = [e.result for e in events if e.result]
    sinks_used = {r.sink for r in write_results}
    assert "feishu_doc" in sinks_used
    assert "mysql" in sinks_used
