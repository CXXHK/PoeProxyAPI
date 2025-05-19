import os
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
from poe_client import PoeClient, SessionManager, validate_file
from utils import get_config, handle_exception

# 读取配置
config = get_config()

# 创建FastAPI应用
app = FastAPI(title="Poe Proxy HTTP API")

# 允许跨域，方便前端/本地测试
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化Poe API客户端和会话管理器
poe_client = PoeClient(
    api_key=config.poe_api_key,
    debug_mode=config.debug_mode,
    claude_compatible=config.claude_compatible,
)
session_manager = SessionManager(expiry_minutes=config.session_expiry_minutes)

@app.get("/ask_poe")
async def ask_poe(
    bot: str,
    prompt: str,
    session_id: Optional[str] = None,
    thinking_enabled: Optional[bool] = None,
    thinking_depth: Optional[int] = None,
    thinking_style: Optional[str] = None,
):
    """
    问答接口：通过指定模型和问题，获取AI回复。
    支持多轮对话（session_id），可选思维链参数。
    """
    try:
        thinking = None
        if thinking_enabled is not None:
            thinking = {"thinking_enabled": thinking_enabled}
            if thinking_depth is not None:
                thinking["thinking_depth"] = thinking_depth
            if thinking_style is not None:
                thinking["thinking_style"] = thinking_style
        # 获取或创建会话
        current_session_id = session_manager.get_or_create_session(session_id)
        # 获取历史消息
        messages = session_manager.get_messages(current_session_id)
        # 调用Poe模型
        response = await poe_client.query_model(
            bot_name=bot,
            prompt=prompt,
            messages=messages,
            stream_handler=None,
            thinking=thinking,
        )
        # 更新会话历史
        session_manager.update_session(
            session_id=current_session_id,
            user_message=prompt,
            bot_message=response["text"],
        )
        return {"text": response["text"], "session_id": current_session_id}
    except Exception as e:
        return JSONResponse(status_code=500, content=handle_exception(e))

@app.post("/ask_with_attachment")
async def ask_with_attachment(
    bot: str = Form(...),
    prompt: str = Form(...),
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    thinking_enabled: Optional[bool] = Form(None),
    thinking_depth: Optional[int] = Form(None),
    thinking_style: Optional[str] = Form(None),
):
    """
    问答+文件接口：支持上传文件并结合问题进行AI回复。
    """
    try:
        thinking = None
        if thinking_enabled is not None:
            thinking = {"thinking_enabled": thinking_enabled}
            if thinking_depth is not None:
                thinking["thinking_depth"] = thinking_depth
            if thinking_style is not None:
                thinking["thinking_style"] = thinking_style
        # 保存上传文件到临时路径
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        # 校验文件大小
        validate_file(temp_path, max_size_mb=config.max_file_size_mb)
        # 获取或创建会话
        current_session_id = session_manager.get_or_create_session(session_id)
        # 获取历史消息
        messages = session_manager.get_messages(current_session_id)
        # 调用Poe模型（带文件）
        response = await poe_client.query_model_with_file(
            bot_name=bot,
            prompt=prompt,
            file_path=temp_path,
            messages=messages,
            stream_handler=None,
            thinking=thinking,
        )
        # 更新会话历史
        session_manager.update_session(
            session_id=current_session_id,
            user_message=f"{prompt} [File: {file.filename}]",
            bot_message=response["text"],
        )
        os.remove(temp_path)
        return {"text": response["text"], "session_id": current_session_id}
    except Exception as e:
        return JSONResponse(status_code=500, content=handle_exception(e))

@app.post("/clear_session")
async def clear_session(session_id: str = Form(...)):
    """
    清空指定会话ID的历史消息。
    """
    try:
        success = session_manager.delete_session(session_id)
        if success:
            return {"status": "success", "message": f"Session {session_id} cleared"}
        else:
            return {"status": "error", "message": f"Session {session_id} not found"}
    except Exception as e:
        return JSONResponse(status_code=500, content=handle_exception(e))

@app.get("/list_available_models")
async def list_available_models():
    """
    获取当前可用的Poe模型列表。
    """
    try:
        models = await poe_client.get_available_models()
        return {"models": models}
    except Exception as e:
        return JSONResponse(status_code=500, content=handle_exception(e))

@app.get("/get_server_info")
def get_server_info():
    """
    获取服务端配置信息。
    """
    try:
        return {
            "name": "Poe Proxy HTTP API",
            "version": "1.0.0",
            "claude_compatible": config.claude_compatible,
            "debug_mode": config.debug_mode,
            "max_file_size_mb": config.max_file_size_mb,
            "session_expiry_minutes": config.session_expiry_minutes,
            "active_sessions": len(session_manager.sessions),
        }
    except Exception as e:
        return JSONResponse(status_code=500, content=handle_exception(e))

if __name__ == "__main__":
    # 启动FastAPI服务，默认端口8000
    uvicorn.run("http_api:app", host="0.0.0.0", port=8000, reload=True) 