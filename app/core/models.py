"""统一数据模型：DataPilot 内部流转的数据格式"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass
class Field:
    """单个字段定义"""
    name: str
    type: Literal["string", "number", "integer", "boolean", "datetime"] = "string"
    primary_key: bool = False
    nullable: bool = True


@dataclass
class Dataset:
    """一次抓取/分析产出的结构化数据"""
    name: str                              # 数据集名（用作表名/文档标题）
    fields: list[Field]                    # 字段定义
    rows: list[dict[str, Any]]             # 数据行（key 对应 field.name）
    source_url: str | None = None           # 来源 URL
    captured_at: datetime = field(default_factory=datetime.now)


@dataclass
class WriteResult:
    """写入结果"""
    sink: str                              # "feishu_doc" / "feishu_sheet" / "mysql"
    target: str                            # 目标标识（doc_id / table_id / db.table）
    rows_written: int
    document_url: str | None = None        # 飞书文档链接
    sql: str | None = None                 # MySQL 的关键 SQL（可审计）
    mock: bool = False                     # 是否 Mock 模式
    extra: dict[str, Any] = field(default_factory=dict)
