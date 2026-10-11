"""Mock 飞书云文档写入：实际生产替换为 openapi SDK 调用 docx/v1"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.models import Dataset, WriteResult
from app.sinks.base import WriteSink, SinkRegistry


class FeishuDocSink(WriteSink):
    """飞书云文档写入（Mock 实现）

    真实实现需要：
      1. tenant_access_token (POST /auth/v3/tenant_access_token/internal)
      2. 创建文档块 (POST /docx/v1/documents/{doc_token}/blocks/{block_id}/children)
      3. 写入表格块 (table block + table_cell block)

    Mock 实现：把 Dataset 序列化成 Markdown 段落 + 表格，写到 outputs/feishu_doc/{doc_token}.json
    """

    name = "feishu_doc"

    def __init__(self) -> None:
        self._output_dir = Path("outputs/feishu_doc")
        self._output_dir.mkdir(parents=True, exist_ok=True)

    async def write(self, dataset: Dataset, target: str, *, mode: str = "append") -> WriteResult:
        # target 即 doc_token
        doc_token = target

        # 构造飞书文档块结构（简化版）
        blocks = self._build_blocks(dataset)

        # Mock：写入本地 JSON
        out_path = self._output_dir / f"{doc_token}.json"
        payload = {
            "doc_token": doc_token,
            "title": dataset.name,
            "source_url": dataset.source_url,
            "captured_at": dataset.captured_at.isoformat(),
            "block_count": len(blocks),
            "blocks": blocks,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

        print(f"[FeishuDocSink/Mock] 写入文档 {doc_token}: {len(dataset.rows)} 行, {len(blocks)} 个 block -> {out_path}")

        return WriteResult(
            sink=self.name,
            target=doc_token,
            rows_written=len(dataset.rows),
            document_url=f"https://feishu.cn/docx/{doc_token}",
            mock=settings.mock_mode,
            extra={"block_count": len(blocks), "out_path": str(out_path)},
        )

    def _build_blocks(self, dataset: Dataset) -> list[dict]:
        """构造飞书文档块（heading + table）"""
        blocks = [
            {"block_type": 2, "text": {"elements": [{"text_run": {"content": dataset.name}}]}},  # heading
            {"block_type": 2, "text": {"elements": [{"text_run": {"content": f"来源: {dataset.source_url or 'N/A'}"}}]}},
            {"block_type": 2, "text": {"elements": [{"text_run": {"content": f"抓取时间: {dataset.captured_at.isoformat()}"}}]}},
            {"block_type": 2, "text": {"elements": [{"text_run": {"content": f"共 {len(dataset.rows)} 行 / {len(dataset.fields)} 列"}}]}},
        ]

        # 表格块（飞书 table block 类型 31）
        if dataset.rows:
            table_block = {
                "block_type": 31,
                "table": {
                    "property": {
                        "row_size": len(dataset.rows) + 1,  # +1 表头
                        "column_size": len(dataset.fields),
                    },
                    "cells": self._build_table_cells(dataset),
                },
            }
            blocks.append(table_block)

        return blocks

    def _build_table_cells(self, dataset: Dataset) -> list[list[str]]:
        """二维数组：飞书 table 的 cells 是按行优先的二维数组"""
        cells = []
        # 表头
        cells.append([f.name for f in dataset.fields])
        # 数据行
        for row in dataset.rows:
            cells.append([str(row.get(f.name, "")) for f in dataset.fields])
        return cells


SinkRegistry.register(FeishuDocSink())
