"""
文件工具模块，提供文件校验、读取等辅助功能。
"""
import os
import mimetypes
from typing import Dict, Optional, Tuple, BinaryIO
import tempfile

from utils import logger, FileHandlingError


def validate_file(file_path: str, max_size_mb: int = 10) -> Tuple[str, str]:
    """
    校验文件是否存在且大小不超过指定MB。
    :param file_path: 文件路径
    :param max_size_mb: 最大允许大小（MB）
    :raises: FileNotFoundError, ValueError
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValueError(f"文件过大: {size_mb:.2f}MB > {max_size_mb}MB")
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        # Default to application/octet-stream if MIME type cannot be determined
        mime_type = "application/octet-stream"
    
    logger.debug(f"Validated file: {file_path} ({mime_type}, {size_mb:.2f} MB)")
    return file_path, mime_type


def is_text_file(file_path: str) -> bool:
    """
    判断文件是否为文本类型。
    :param file_path: 文件路径
    :return: 是否为文本文件
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except Exception:
        return False


def read_file_content(file_path: str, max_size_mb: int = 10) -> Tuple[str, bool]:
    """
    读取文本文件内容。
    :param file_path: 文件路径
    :return: 文件内容字符串
    """
    try:
        # Validate the file
        validate_file(file_path, max_size_mb)
        
        # Check if it's a text file
        is_text = is_text_file(file_path)
        
        if is_text:
            # Read as text
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content, True
        else:
            # For binary files, return the file name
            return os.path.basename(file_path), False
    
    except Exception as e:
        raise FileHandlingError(f"Error reading file: {str(e)}")


def create_temp_file(content: str, suffix: str = ".txt") -> str:
    """
    创建临时文件，返回路径。
    :param suffix: 文件后缀
    :return: 临时文件路径
    """
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.debug(f"Created temporary file: {temp_file_path}")
        return temp_file_path
    
    except Exception as e:
        raise FileHandlingError(f"Error creating temporary file: {str(e)}")


def get_common_mime_types() -> Dict[str, str]:
    """
    Get a dictionary of common file extensions and their MIME types.
    
    Returns:
        Dict[str, str]: Dictionary of file extensions to MIME types
    """
    return {
        # Text
        ".txt": "text/plain",
        ".html": "text/html",
        ".htm": "text/html",
        ".css": "text/css",
        ".csv": "text/csv",
        
        # Application
        ".json": "application/json",
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".ppt": "application/vnd.ms-powerpoint",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".zip": "application/zip",
        ".xml": "application/xml",
        
        # Image
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
        
        # Audio
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        
        # Video
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".webm": "video/webm",
        
        # Code
        ".py": "text/x-python",
        ".js": "text/javascript",
        ".java": "text/x-java",
        ".c": "text/x-c",
        ".cpp": "text/x-c++",
        ".rb": "text/x-ruby",
        ".go": "text/x-go",
        ".rs": "text/x-rust",
        ".php": "text/x-php",
    }