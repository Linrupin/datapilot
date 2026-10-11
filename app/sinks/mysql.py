"""Mock MySQL 写入：实际生产替换为 SQLAlchemy 异步 + aiomysql"""
from __future__ import annotations

import json
import re
from pathlib import Path

from sqlalchemy import (
    Column, MetaData, String, Integer, Float, DateTime, Boolean, Table,
    create_engine, insert, select, text,
)

# SQLAlchemy 异步相关只在真实模式下需要，Mock 模式延迟导入以避免 greenlet 依赖
# from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.core.config import settings
from app.core.models import Dataset, Field, WriteResult
from app.sinks.base import WriteSink, SinkRegistry


# 类型映射：Field.type -> SQLAlchemy 列类型
_TYPE_MAP = {
    "string": String(255),
    "number": Float,
    "integer": Integer,
    "boolean": Boolean,
    "datetime": DateTime,
}


class MySQLSink(WriteSink):
    """MySQL 写入（Mock 实现）

    真实实现需要：
      1. async_engine = create_async_engine("mysql+aiomysql://user:pwd@host:3306/db")
      2. 推断 schema -> 创建表（如不存在）
      3. UPSERT (ON DUPLICATE KEY UPDATE)

    Mock 实现：把 SQL 与数据写入 outputs/mysql/{db.table}.json，便于审计与回放
    """

    name = "mysql"

    def __init__(self) -> None:
        self._output_dir = Path("outputs/mysql")
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._engine = None  # Mock 模式不真连

    async def write(self, dataset: Dataset, target: str, *, mode: str = "upsert") -> WriteResult:
        # target 形如 "db.table"
        if "." not in target:
            raise ValueError(f"MySQL target 必须是 'db.table' 格式，收到: {target}")
        db, table = target.split(".", 1)

        # 1) 推断 / 校验 schema
        pk_field = self._pick_primary_key(dataset.fields)
        create_sql = self._build_create_table_sql(db, table, dataset.fields, pk_field)
        upsert_sql = self._build_upsert_sql(table, dataset.fields, pk_field)

        # 2) 执行（Mock：打印 SQL）
        print(f"[MySQLSink/Mock] CREATE TABLE IF NOT EXISTS {db}.{table}")
        print(f"[MySQLSink/Mock] {upsert_sql[:200]}... ({len(dataset.rows)} 行)")

        # 3) 写本地审计文件
        audit_path = self._output_dir / f"{db}.{table}.json"
        audit = {
            "target": target,
            "create_table_sql": create_sql,
            "upsert_sql_preview": upsert_sql,
            "rows": dataset.rows,
            "mode": mode,
            "mock": settings.mock_mode,
        }
        audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2))

        return WriteResult(
            sink=self.name,
            target=target,
            rows_written=len(dataset.rows),
            sql=upsert_sql,
            mock=settings.mock_mode,
            extra={"create_sql": create_sql, "audit_path": str(audit_path)},
        )

    def _pick_primary_key(self, fields: list[Field]) -> Field | None:
        for f in fields:
            if f.primary_key:
                return f
        return None

    def _build_create_table_sql(self, db: str, table: str, fields: list[Field], pk: Field | None) -> str:
        """生成 CREATE TABLE IF NOT EXISTS 语句"""
        cols = []
        for f in fields:
            sql_type = _TYPE_MAP.get(f.type, String(255))
            type_str = (
                "VARCHAR(255)" if f.type == "string" else
                "DOUBLE" if f.type == "number" else
                "INT" if f.type == "integer" else
                "BOOLEAN" if f.type == "boolean" else
                "DATETIME"
            )
            nullable = "NULL" if f.nullable else "NOT NULL"
            cols.append(f"  `{f.name}` {type_str} {nullable}")

        pk_clause = ""
        if pk:
            cols.append(f"  PRIMARY KEY (`{pk.name}`)")

        body = ",\n".join(cols)
        return f"CREATE TABLE IF NOT EXISTS `{db}`.`{table}` (\n{body}\n);"

    def _build_upsert_sql(self, table: str, fields: list[Field], pk: Field | None) -> str:
        """生成 INSERT ... ON DUPLICATE KEY UPDATE 预览（不参数化，便于审计展示）"""
        field_names = [f.name for f in fields]
        cols_sql = ", ".join(f"`{n}`" for n in field_names)
        placeholders = ", ".join(f":{n}" for n in field_names)

        if pk:
            update_cols = [n for n in field_names if n != pk.name]
            update_clause = ", ".join(f"`{n}` = VALUES(`{n}`)" for n in update_cols)
            return (
                f"INSERT INTO `{table}` ({cols_sql}) VALUES ({placeholders}) "
                f"ON DUPLICATE KEY UPDATE {update_clause};"
            )
        else:
            return f"INSERT INTO `{table}` ({cols_sql}) VALUES ({placeholders});"


SinkRegistry.register(MySQLSink())
