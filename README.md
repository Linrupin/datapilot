# DataPilot · M1 MVP 骨架

> AI 驱动的浏览器数据协同 SaaS —— 浏览器插件 + 桌面客户端 + 多数据源 + 自然语言编排

本仓库是 **M1（最小可运行骨架）** 阶段的代码，用于验证"自然语言 → AI 编排 → 浏览器抓取 → 双通道写入"完整链路。

## 核心能力

- 🧠 **意图解析 + 任务规划**：自然语言输入，4 步流式回执（plan / extract / write / done）
- 🌐 **浏览器抓取（Mock）**：内置京东蓝牙耳机竞品、飞书任务两个示例数据集
- 📄 **双通道写入**：
  - **飞书云文档**（Mock）—— 文档块结构（heading + table）
  - **MySQL**（Mock）—— CREATE TABLE + UPSERT
- 🔌 **可扩展 Sink**：所有写入适配器实现 `WriteSink` 抽象，未来接真实 SDK 零成本切换
- 🌊 **SSE 流式回执**：前端可逐步订阅执行进度

## 当前状态：Mock 模式

不真连飞书、不真连 MySQL，所有写入产物落到本地 `outputs/` 目录的 JSON 文件。
**接口设计真实、实现是 Mock** —— 上线时只需替换 `app/sinks/feishu_doc.py` 与 `app/sinks/mysql.py` 的 `write()` 方法。

## 架构

```
┌──────────────────────────────────────┐
│  用户输入 (自然语言)                  │
└────────────────┬─────────────────────┘
                 ↓
┌──────────────────────────────────────┐
│  客户端 (FastAPI + Agent)            │
│  ├─ 意图解析                          │
│  ├─ 任务规划                          │
│  ├─ Mock 抓取                         │
│  └─ 双通道写入（飞书 + MySQL）        │
└────────────────┬─────────────────────┘
                 ↓
┌──────────────────────────────────────┐
│  Sinks (可插拔)                       │
│  ├─ FeishuDocSink  (Mock)            │
│  └─ MySQLSink      (Mock)            │
└──────────────────────────────────────┘
```

## 快速开始

```bash
# 1. 安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 启动服务
python -m app.main
# 监听: http://127.0.0.1:8765

# 3. 测试
curl http://127.0.0.1:8765/health
# {"status":"ok","mock_mode":true}

# 4. 流式执行 Agent
curl -N -X POST http://127.0.0.1:8765/agent/run \
  -H "Content-Type: application/json" \
  -d '{"input": "京东"}'
```

## 运行测试

```bash
pytest tests/ -v
```

8 个测试，覆盖：
- Agent 编排（意图解析、写入规划、端到端流）
- 双 Sink 写入逻辑（飞书文档块结构、MySQL UPSERT SQL）

## 目录结构

```
datapilot/
├── app/
│   ├── core/         # config + models (Dataset/Field/WriteResult)
│   ├── sinks/        # feishu_doc, mysql (均 Mock 实现)
│   ├── tools/        # mock_extract (内置示例数据集)
│   ├── agent/        # orchestrator (4 步流式编排)
│   ├── api/          # FastAPI + SSE
│   └── main.py
├── tests/            # 8 个单元测试
├── outputs/          # [gitignore] Mock 写入产物
├── README.md
├── requirements.txt
└── .env.example
```

## 路线图

| 阶段 | 状态 | 目标 |
|------|------|------|
| **M1 MVP** | ✅ 本仓库 | FastAPI + Mock 双通道 + SSE 流式 |
| M2 AI Agent 化 | ⏳ | 接入 pi-agent 替换意图规则 + 选择器自愈 |
| M3 多人协作 | ⏳ | SaaS 控制台 + RBAC + Yjs |
| M4 规模化 | ⏳ | Tauri 客户端 + 真实浏览器插件 + 真实 SDK |

## 设计原则

1. **非强占**：浏览器插件永不模拟真实鼠标键盘、不抢焦点
2. **本地优先**：数据查询在客户端跑，只上送元数据
3. **凭证加密**：连接凭证 AES-256 + 用户主密钥派生
4. **可回放**：所有抓取录屏、所有 SQL 留痕
5. **接口先行**：先定 WriteSink 抽象，再实现 Mock，再换真实 SDK

## License

MIT
