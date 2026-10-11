# 基于 LangChain 的企业级 RAG 知识库问答系统

面向**电商商品问答**场景的企业级 RAG 知识库问答系统（毕业设计）。用户通过浏览器完成知识库管理与问答，问答时引用知识库片段并在回答中高亮展示来源，支持多用户隔离与历史会话找回。

## 功能特性

- ✅ 浏览器端知识库管理（所有登录用户）：新建/删除知识库、上传/删除文档、查看摄取状态
- ✅ 知识库问答：流式输出，回答中标注 `[1][2]` 引用编号，并高亮展示对应知识库片段
- ✅ 多用户独立会话，会话记录持久化，不同时间登录可找回历史对话
- ✅ 注册 / 登录 / 修改密码（bcrypt + JWT）
- ✅ 管理员账号 `admin / 123456`，管理后台（统计/用户列表）仅管理员可见（RBAC）
- ✅ 多轮追问（查询改写 + 历史上下文）、会话标题自动生成、点赞/点踩反馈
- ✅ 多格式文档：PDF / Word / TXT / Markdown / CSV / Excel
- ✅ 企业级性能优化：混合检索（向量+BM25，RRF 融合）、重排序、语义缓存、异步全链路、限流、结构化日志

## 技术栈

| 层 | 选型 |
|----|------|
| 大模型 | 阿里云百炼 · 通义千问 `qwen-plus` |
| 向量化 | 百炼 `text-embedding-v3` |
| 重排序 | 百炼 `gte-rerank` |
| RAG 框架 | LangChain（`ChatTongyi` + `DashScopeEmbeddings` + `Chroma` + `BM25Retriever`） |
| 向量库 | Chroma（嵌入式持久化，免 Docker） |
| 后端 | Python 3.11+ / FastAPI / Uvicorn |
| 数据库 | SQLite + SQLAlchemy 2.0 |
| 前端 | Vue3 + Vite + TypeScript + Element Plus + Pinia |
| 认证 | JWT（PyJWT）+ bcrypt |

## 目录结构

```
RAG/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 入口
│   │   ├── config.py        # 配置（.env）
│   │   ├── database.py      # SQLAlchemy
│   │   ├── models.py        # 数据模型
│   │   ├── schemas.py       # Pydantic 模型
│   │   ├── core/            # 安全、鉴权、限流
│   │   ├── api/             # 路由（auth/conversations/chat/knowledge/admin）
│   │   ├── rag/             # 加载/切分/向量化/检索/生成/引用
│   │   └── services/        # 业务编排、语义缓存
│   ├── requirements.txt
│   ├── .env.example
│   └── init_db.py           # 建表 + 管理员
├── frontend/                # Vue3 前端
├── sample_data/             # 示例商品文档
└── README.md
```

## 环境要求

- Python 3.11+（本项目在 3.13 验证通过）
- Node.js 18+（本项目在 24 验证通过）

## 快速开始

### 1. 准备百炼 API Key

1. 打开 [阿里云百炼控制台](https://bailian.console.aliyun.com/) 开通服务；
2. 创建 API-KEY；
3. 编辑 `backend/.env`，把 `DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx` 换成你的真实 Key。
   （LLM、向量化、重排序共用这一个 Key）

### 2. 启动后端

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe init_db.py          # 建表 + 创建 admin/123456
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

后端启动后：`http://127.0.0.1:8000/api/health` 返回 `{"status":"ok"}`。

### 3. 启动前端（开发模式）

```bash
cd frontend
npm install --registry=https://registry.npmmirror.com
npm run dev          # http://localhost:5173
```

### 4. 生产模式（后端托管前端，单进程）

```bash
cd frontend && npm run build     # 生成 dist/
# 重启后端，自动托管 dist，访问 http://127.0.0.1:8000 即可
```

## 使用说明

1. **管理员登录**：`admin / 123456`
2. **知识库管理**：进入「知识库管理」→ 新建知识库 → 上传文档（可用 `sample_data/电商商品FAQ.md` 测试）→ 等待状态变为「完成」
3. **问答**：切到普通用户（先注册一个账号）→ 提问如「X20 Pro 多少钱」「耳机续航多久」→ 观察流式回答与引用片段
4. **权限**：知识库管理对所有登录用户开放；管理后台（统计/用户）仅管理员可见

## 性能优化说明（毕设要点）

- **混合检索 + RRF**：BM25 关键词召回与向量语义召回融合，商品型号/属性词命中更准
- **重排序**：`gte-rerank` 对候选精排，提升引用准确率
- **语义缓存**：相似问题命中缓存答案，降低 LLM 调用与成本
- **单次向量化复用**：query embedding 供缓存与检索共用
- **异步全链路**：FastAPI async + `astream` 流式 + 文档摄取后台任务
- **文档 hash 去重**：相同内容避免重复摄取
- **限流 + 结构化日志**：接口限流、请求延迟记录（消息含 `latency_ms`）

## 主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/change-password` | 修改密码 |
| GET/POST | `/api/conversations` | 会话列表/新建 |
| GET | `/api/conversations/{id}/messages` | 历史消息 |
| POST | `/api/chat` | 问答（SSE 流式） |
| POST | `/api/chat/messages/{id}/feedback` | 反馈 |
| CRUD | `/api/knowledge` | 知识库管理（所有登录用户） |
| GET | `/api/admin/stats` | 统计面板（仅管理员） |

## 运行测试

单元测试覆盖：密码哈希/JWT、引用解析、文档加载与切分、语义缓存、限流、RRF 检索融合，以及认证/权限/会话三类 API 测试。测试使用独立的临时数据库，不污染真实数据。

```bash
cd backend
.venv\Scripts\python.exe -m pytest -v
```

端到端验证（需先启动后端并配置好 API Key）：

```bash
.venv\Scripts\python.exe e2e_test.py
```

## 注意事项

- 首次运行需联网（调用百炼云端 API，无本地模型、无 Docker）。
- `.env` 中的 `SECRET_KEY` 生产环境请务必修改。
- 数据默认存放在 `backend/data/`（SQLite + Chroma），可整体备份迁移。
