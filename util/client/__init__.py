# coding: utf-8
"""
客户端模块

仅提供 logger，避免在包导入阶段触发重型依赖（如 pynput、sounddevice）。
"""

from util import get_logger
logger = get_logger('client')
__all__ = ['logger']
