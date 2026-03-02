# coding: utf-8
"""
shortcut 子模块

包含快捷键处理相关功能，使用 ShortcutManager 统一管理所有快捷键（键盘和鼠标）。
"""

from .. import logger
from util.client.shortcut.shortcut_config import Shortcut, CommonShortcuts


def __getattr__(name):
    """懒加载 ShortcutManager，避免在包导入阶段触发平台依赖。"""
    if name == 'ShortcutManager':
        from util.client.shortcut.shortcut_manager import ShortcutManager
        return ShortcutManager
    raise AttributeError(f"module {__name__} has no attribute {name}")

__all__ = [
    'logger',
    'Shortcut',
    'CommonShortcuts',
    'ShortcutManager',
]
