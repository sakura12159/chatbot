# 个人项目：基于领域驱动设计的对话 AI
## 涉及：Python | Typescript | Vue3 | Zod | Pinia | FastAPI | Pydantic | RAG | PostgreSQL | SQLAlchemy | Tavily | E2B | Cohere | DeepSeek API
## 项目描述：通用场景对话 AI，支持多轮会话、思考模式、工具调用（网络搜索与代码执行）、RAG、流式输出、会话持久化与 Markdown 渲染。后端采用 DDD 分层架构，解耦领域逻辑、LLM 调用与数据库实现；前端基于 Vue3 + TypeScript 实现流式对话交互。

## 依赖安装
```bash
sudo apt install postgresql postgresql-16-pgvector  # 安装 postgresql和 pgvector

uv sync  # 安装项目后端依赖包，需要 uv
npm install  # 安装项目前端依赖包，需要 Node.js
```

## 命令行
后端：目录 chatbot/backend下，
```bash 
python -m uvicorn main:app --reload
```
前端：目录 chatbot/frontend下，启用开发者模式
```bash
npm run dev
```
数据库：
```bash
sudo systemctl start postgresql  # 开启
sudo systemctl stop postgresql  # 关闭
```  

本地运行在 http://localhost:5173/

## 效果
### 开始新会话
![新会话](新会话.gif)

### 加载会话历史并继续会话
![继续会话](继续会话.gif)

## 注意
### Cohere API 国内 ip 无法访问，可通过设置代理绕过（Clash 监听 7890 端口并更换节点），极不稳定，采用该 api 仅因其免费额度 -.-
