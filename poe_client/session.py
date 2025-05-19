"""
Session management for the Poe API client.

This module provides functionality for managing conversation sessions,
including creating, retrieving, updating, and deleting sessions.
"""
import time
import uuid
from typing import Dict, List, Optional, Any
import fastapi_poe as fp

from utils import logger


class SessionManager:
    """
    Poe API会话管理器，负责多轮对话的会话ID、历史消息等管理。
    """
    
    def __init__(self, expiry_minutes: int = 60):
        """
        初始化会话管理器。
        :param expiry_minutes: 会话过期时间（分钟）
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.expiry_minutes = expiry_minutes
        logger.info(f"Session manager initialized with {expiry_minutes} minute expiry")
    
    def create_session(self) -> str:
        """
        创建新会话，返回会话ID。
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "messages": [],
            "created_at": time.time(),
            "last_accessed": time.time(),
        }
        logger.debug(f"Created new session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定ID的会话。
        :param session_id: 会话ID
        :return: 会话数据或None
        """
        if session_id not in self.sessions:
            logger.debug(f"Session not found: {session_id}")
            return None
        
        # 更新时间戳
        self.sessions[session_id]["last_accessed"] = time.time()
        
        # 检查是否过期
        if self._is_session_expired(session_id):
            logger.debug(f"Session expired: {session_id}")
            self.delete_session(session_id)
            return None
        
        return self.sessions[session_id]
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """
        获取已存在会话或新建会话。
        :param session_id: 可选会话ID
        :return: 有效会话ID
        """
        if session_id and session_id in self.sessions:
            if self._is_session_expired(session_id):
                logger.debug(f"Session expired: {session_id}")
                self.delete_session(session_id)
                return self.create_session()
            
            self.sessions[session_id]["last_accessed"] = time.time()
            logger.debug(f"Retrieved existing session: {session_id}")
            return session_id
        
        return self.create_session()
    
    def update_session(
        self, 
        session_id: str, 
        user_message: str, 
        bot_message: str,
    ) -> bool:
        """
        向会话中添加一轮对话（用户消息+AI回复）。
        :param session_id: 会话ID
        :param user_message: 用户消息
        :param bot_message: AI回复
        :return: 是否成功
        """
        session = self.get_session(session_id)
        if not session:
            logger.debug(f"Cannot update non-existent session: {session_id}")
            return False
        
        # 添加消息
        session["messages"].append(fp.ProtocolMessage(role="user", content=user_message))
        session["messages"].append(fp.ProtocolMessage(role="bot", content=bot_message))
        
        session["last_accessed"] = time.time()
        
        logger.debug(f"Updated session {session_id} with new messages")
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除指定ID的会话。
        :param session_id: 会话ID
        :return: 是否成功
        """
        if session_id not in self.sessions:
            logger.debug(f"Cannot delete non-existent session: {session_id}")
            return False
        
        del self.sessions[session_id]
        logger.debug(f"Deleted session: {session_id}")
        return True
    
    def get_messages(self, session_id: str) -> List[fp.ProtocolMessage]:
        """
        获取指定会话的历史消息列表。
        :param session_id: 会话ID
        :return: 消息列表
        """
        session = self.get_session(session_id)
        if not session:
            logger.debug(f"Cannot get messages for non-existent session: {session_id}")
            return []
        
        # 修正历史数据中role为'assistant'的消息为'bot'
        for msg in session["messages"]:
            if hasattr(msg, 'role') and msg.role == "assistant":
                msg.role = "bot"
        
        return session["messages"]
    
    def cleanup_expired_sessions(self) -> int:
        """
        清理所有已过期的会话。
        :return: 清理的会话数量
        """
        expired_sessions = []
        
        for session_id in self.sessions:
            if self._is_session_expired(session_id):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def _is_session_expired(self, session_id: str) -> bool:
        """
        判断会话是否已过期。
        :param session_id: 会话ID
        :return: 是否过期
        """
        if session_id not in self.sessions:
            return True
        
        last_accessed = self.sessions[session_id]["last_accessed"]
        expiry_time = last_accessed + (self.expiry_minutes * 60)
        
        return time.time() > expiry_time