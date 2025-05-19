# Poe Proxy HTTP API

本项目是一个简洁的 Poe.com 多模型 API 代理服务，支持通过标准 HTTP 接口调用 Poe 平台上的主流大模型（如 GPT-4.1、GPT-4o、Claude、o3 等），并自带网页测试工具，适合开发者快速集成和验证。

---

## 主要功能
- 通过 `/ask_poe` 等 HTTP API 直接调用 Poe 各类模型
- 支持多轮对话（会话ID）
- 支持网页端一键测试 API（`web_test.html`）
- 仅保留 API 服务和网页测试，**无其他复杂依赖**

---

## 快速开始

### 1. 安装依赖

建议使用 Python 3.8 及以上，先创建虚拟环境：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置 Poe API Key

在项目根目录下新建 `.env` 文件，内容如下（请替换为你自己的 API Key）：

```
POE_API_KEY=你的poe_api_key
```

### 3. 启动 API 服务

```bash
python http_api.py
```

默认监听 `http://localhost:8000`。

### 4. 网页测试

直接用浏览器打开 `web_test.html`，即可通过页面输入问题、选择模型、测试 API。

---

## API 说明

### 1. 问答接口
- `GET /ask_poe?bot=模型名&prompt=你的问题[&session_id=会话ID]`
- 返回：`{"text": "回复内容", "session_id": "..."}`

### 2. 获取模型列表
- `GET /list_available_models`

### 3. 获取服务信息
- `GET /get_server_info`

### 4. 清空会话
- `POST /clear_session`（表单参数：session_id）

---

## 常见问题

- **端口被占用**：如遇 `Address already in use`，请关闭占用8000端口的进程或修改端口。
- **Assistant模型不可用**：Poe Assistant 仅支持网页端，API 不支持。
- **API Key 获取**：需 Poe 订阅用户，详见 https://poe.com/api_key

---

## 目录结构

```
http_api.py         # 主API服务入口
web_test.html       # 网页测试工具
poe_client/         # Poe API核心调用逻辑
utils/              # 配置与日志工具
requirements.txt    # 依赖列表
```

---

如有问题欢迎反馈！ 