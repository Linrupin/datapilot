"""测试两个 sink 的写入逻辑"""
import asyncio
import json
from pathlib import Path

import pytest

from app.core.models import Dataset, Field
from app.sinks.base import SinkRegistry
from app.sinks import feishu_doc, mysql  # noqa: F401 触发注册


@pytest.fixture
def sample_dataset():
    return Dataset(
        name="测试数据集",
        source_url="https://example.com",
        fields=[
            Field(name="id", type="integer", primary_key=True),
            Field(name="name", type="string"),
            Field(name="price", type="number"),
        ],
        rows=[
            {"id": 1, "name": "A", "price": 10.5},
            {"id": 2, "name": "B", "price": 20.0},
        ],
    )


def test_registry_has_both_sinks():
    assert "feishu_doc" in SinkRegistry.all()
    assert "mysql" in SinkRegistry.all()


@pytest.mark.asyncio
async def test_feishu_doc_sink(sample_dataset):
    sink = SinkRegistry.get("feishu_doc")
    result = await sink.write(sample_dataset, "test_doc_001")

    assert result.sink == "feishu_doc"
    assert result.rows_written == 2
    assert result.mock is True
    assert result.document_url is not None

    # 检查产出文件
    out_path = Path("outputs/feishu_doc/test_doc_001.json")
    assert out_path.exists()
    payload = json.loads(out_path.read_text())
    assert payload["title"] == "测试数据集"
    assert len(payload["blocks"]) >= 4


@pytest.mark.asyncio
async def test_mysql_sink(sample_dataset):
    sink = SinkRegistry.get("mysql")
    result = await sink.write(sample_dataset, "test_db.test_table", mode="upsert")

    assert result.sink == "mysql"
    assert result.rows_written == 2
    assert result.mock is True
    assert "INSERT INTO" in result.sql
    assert "ON DUPLICATE KEY UPDATE" in result.sql

    # 检查 SQL 关键字
    assert "CREATE TABLE" in result.extra["create_sql"]
    assert "`id`" in result.extra["create_sql"]
    assert "PRIMARY KEY" in result.extra["create_sql"]

    # 检查产出文件
    out_path = Path("outputs/mysql/test_db.test_table.json")
    assert out_path.exists()
