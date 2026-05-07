# Enterprise AI Assistant Platform

企业智能助手底座，使用 FastAPI + LangChain + 向量库实现 MVP：企业资料上传、文档入库、RAG 问答、工具调用、会话记忆和单页演示前端。

## 已补齐能力

- 企业部署能力：Bearer Token 鉴权、CORS 白名单、上传大小限制、结构化请求日志、`/health` 和 `/ready`
- LangChain Document Loaders：读取 `txt / md / pdf / docx`
- RecursiveCharacterTextSplitter：按 `chunk_size=500, overlap=50` 切片
- Chroma 向量库：持久化到 `data/chroma`
- 本地 JSON 向量库兜底：开发机暂未安装 `chromadb` 时自动启用；安装好依赖后自动切回 Chroma
- 国产模型 API 适配：DeepSeek、通义千问/Qwen、智谱 GLM、Moonshot/Kimi、零一万物、硅基流动
- Embedding：
  - `auto`：有 API Key 时用兼容 Embedding API，否则用本地 Hash Embedding
  - `api`：强制调用兼容 Embedding API
  - `local`：强制本地 Embedding，适合无 Key 演示
- RAG 检索：`knowledge_search`
- 政策解释：`policy_explain`
- 工具调用：`calculator`、`current_time`
- 文件上传：`POST /upload`
- 向量库重建：`POST /ingest`
- 知识库状态：`GET /knowledge/status`
- 会话记忆：按 `session_id` 隔离

## 快速启动

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

打开：

```text
http://127.0.0.1:8000
```

## 企业级部署配置

生产环境建议在 `.env` 中开启：

```env
APP_ENV=production
AUTH_ENABLED=true
ADMIN_TOKEN=换成足够长的随机令牌
CORS_ORIGINS=https://your-domain.com
MAX_UPLOAD_MB=20
LOG_LEVEL=INFO
```

启用鉴权后，页面左侧填写“访问令牌”，或者 API 请求带上：

```text
Authorization: Bearer 你的 ADMIN_TOKEN
```

健康检查：

```text
GET /health
GET /ready
```

部署文件：

```text
Dockerfile
docker-compose.yml
deploy/nginx.conf
deploy/enterprise-ai-assistant.service
deploy/README.md
```

## 国产模型配置

支持的 `MODEL_PROVIDER`：

```text
deepseek / qwen / zhipu / moonshot / yi / siliconflow / openai / custom
```

DeepSeek：

```env
MODEL_PROVIDER=deepseek
API_KEY=你的 DeepSeek API Key
CHAT_MODEL=deepseek-chat
EMBEDDING_PROVIDER=local
```

通义千问/Qwen：

```env
MODEL_PROVIDER=qwen
API_KEY=你的 DashScope API Key
CHAT_MODEL=qwen-plus
EMBEDDING_PROVIDER=api
EMBEDDING_MODEL=text-embedding-v4
```

智谱 GLM：

```env
MODEL_PROVIDER=zhipu
API_KEY=你的智谱 API Key
CHAT_MODEL=glm-4-flash
EMBEDDING_PROVIDER=local
```

Moonshot/Kimi：

```env
MODEL_PROVIDER=moonshot
API_KEY=你的 Moonshot API Key
CHAT_MODEL=moonshot-v1-8k
EMBEDDING_PROVIDER=local
```

硅基流动：

```env
MODEL_PROVIDER=siliconflow
API_KEY=你的 SiliconFlow API Key
CHAT_MODEL=Qwen/Qwen2.5-72B-Instruct
EMBEDDING_PROVIDER=api
EMBEDDING_MODEL=BAAI/bge-m3
```

自定义 OpenAI-compatible 服务：

```env
MODEL_PROVIDER=custom
API_KEY=你的 key
BASE_URL=https://你的服务商地址/v1
CHAT_MODEL=模型名
EMBEDDING_PROVIDER=local
```

旧的 `OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL` 仍兼容。

## 使用流程

1. 打开网页。
2. 上传企业资料，支持 `txt / md / pdf / docx`。
3. 点击“重建向量库”。
4. 提问，例如：`年假制度怎么规定？`

也可以直接把资料放进：

```text
data/raw
```

然后执行：

```powershell
python scripts/ingest.py
```

## API

```text
GET  /health
GET  /knowledge/status
POST /upload
POST /ingest
POST /knowledge/reset
POST /chat
```

`POST /chat` 示例：

```json
{
  "session_id": "user_001",
  "message": "年假制度怎么规定？"
}
```

响应：

```json
{
  "answer": "……",
  "sources": ["员工手册.pdf"],
  "tool_used": "policy_explain"
}
```

## 目录结构

```text
app/
  main.py       FastAPI 入口、上传、入库、状态和聊天路由
  config.py     环境变量配置
  providers.py  国产模型与兼容接口预设
  llm.py        OpenAI-compatible LLM 封装
  rag.py        LangChain Loader / Splitter / Chroma / Embedding
  agent.py      工具选择和问答编排
  memory.py     session_id 隔离的会话记忆
  tools.py      calculator / current_time
  prompts.py    系统 Prompt 和 RAG Prompt
  schemas.py    请求和响应模型
data/
  raw/          原始企业文档
  chroma/       Chroma 或本地向量库
scripts/
  ingest.py     文档入库脚本
  start_server.py
tests/
  test_api.py   基础接口测试
web/
  index.html    演示前端
```
