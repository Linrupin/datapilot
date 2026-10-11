"""写入适配器统一接口"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.models import Dataset, WriteResult


class WriteSink(ABC):
    """所有写入目标的统一接口"""

    name: str = "abstract"

    @abstractmethod
    async def write(self, dataset: Dataset, target: str, *, mode: str = "upsert") -> WriteResult:
        """
        target:
          - feishu_doc:   doc_token
          - feishu_sheet: spreadsheet_token + sheet_id  (组合字符串 "spreadsheet:sheet")
          - mysql:        "db.table"
        mode:
          - upsert: 按主键 UPSERT（MySQL）
          - append: 仅追加
        """


class SinkRegistry:
    """注册中心：按名字获取 sink"""

    _registry: dict[str, WriteSink] = {}

    @classmethod
    def register(cls, sink: WriteSink) -> None:
        cls._registry[sink.name] = sink

    @classmethod
    def get(cls, name: str) -> WriteSink:
        if name not in cls._registry:
            raise KeyError(f"sink 未注册: {name}，可选: {list(cls._registry)}")
        return cls._registry[name]

    @classmethod
    def all(cls) -> list[str]:
        return list(cls._registry)
