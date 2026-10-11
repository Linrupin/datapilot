"""Mock 浏览器抓取：模拟插件返回的数据

真实实现：调用 PluginRPCClient 调浏览器插件的 extract_dom / api_fetch / js_inject

这里 Mock 返回京东搜索结果作为示例数据，便于 Agent 演示完整链路
"""
from __future__ import annotations

import random
from datetime import datetime

from app.core.models import Dataset, Field


# 示例 Mock 数据集：京东"蓝牙耳机"搜索结果
MOCK_DATASETS: dict[str, Dataset] = {
    "jd_蓝牙耳机": Dataset(
        name="京东蓝牙耳机竞品",
        source_url="https://search.jd.com/Search?keyword=蓝牙耳机",
        captured_at=datetime.now(),
        fields=[
            Field(name="sku_id", type="string", primary_key=True),
            Field(name="brand", type="string"),
            Field(name="title", type="string"),
            Field(name="price", type="number"),
            Field(name="sales", type="integer"),
            Field(name="captured_at", type="datetime"),
        ],
        rows=[
            {"sku_id": "100012345", "brand": "Sony", "title": "Sony WF-1000XM5 真无线降噪", "price": 1899.00, "sales": 12480},
            {"sku_id": "100023456", "brand": "Apple", "title": "AirPods Pro 2", "price": 1799.00, "sales": 38521},
            {"sku_id": "100034567", "brand": "Bose", "title": "Bose QuietComfort Ultra", "price": 2299.00, "sales": 5821},
            {"sku_id": "100045678", "brand": "Sony", "title": "Sony WH-1000XM5 头戴式", "price": 2499.00, "sales": 9123},
            {"sku_id": "100056789", "brand": "华为", "title": "华为 FreeBuds Pro 3", "price": 1499.00, "sales": 15823},
            {"sku_id": "100067890", "brand": "小米", "title": "小米 Buds 4 Pro", "price": 699.00, "sales": 28541},
            {"sku_id": "100078901", "brand": "漫步者", "title": "漫步者 Lolli Pro 2", "price": 299.00, "sales": 42156},
            {"sku_id": "100089012", "brand": "Apple", "title": "AirPods 4", "price": 999.00, "sales": 18234},
        ],
    ),
    "feishu_任务": Dataset(
        name="飞书本周任务",
        source_url="https://feishu.cn/task/list",
        captured_at=datetime.now(),
        fields=[
            Field(name="task_id", type="string", primary_key=True),
            Field(name="title", type="string"),
            Field(name="status", type="string"),
            Field(name="due_date", type="datetime"),
            Field(name="owner", type="string"),
        ],
        rows=[
            {"task_id": "T001", "title": "京东 Q4 投放复盘", "status": "进行中", "due_date": "2026-10-15", "owner": "滨"},
            {"task_id": "T002", "title": "抖音 10 月素材脚本", "status": "待开始", "due_date": "2026-10-13", "owner": "小张"},
            {"task_id": "T003", "title": "亚朵零售数据周报", "status": "已完成", "due_date": "2026-10-10", "owner": "滨"},
        ],
    ),
}


async def mock_extract(query: str) -> Dataset:
    """Mock：按 query 关键词匹配内置数据集"""
    matched = None

    # query → dataset 的简单映射
    if "京东" in query or "蓝牙耳机" in query:
        matched = MOCK_DATASETS["jd_蓝牙耳机"]
    elif "飞书" in query and "任务" in query:
        matched = MOCK_DATASETS["feishu_任务"]

    if not matched:
        # 兜底：通用 mock
        matched = Dataset(
            name=f"Mock 数据集 - {query}",
            source_url=f"https://mock.local/{query}",
            captured_at=datetime.now(),
            fields=[
                Field(name="id", type="integer", primary_key=True),
                Field(name="name", type="string"),
                Field(name="value", type="number"),
            ],
            rows=[
                {"id": i + 1, "name": f"item-{i}", "value": round(random.uniform(10, 1000), 2)}
                for i in range(5)
            ],
        )

    # 给每行打上抓取时间戳
    for row in matched.rows:
        if "captured_at" in [f.name for f in matched.fields]:
            row["captured_at"] = matched.captured_at.isoformat()

    return matched
