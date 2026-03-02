# coding: utf-8
"""
快捷键后端工厂

根据平台选择对应的快捷键监听后端。
"""

import os
from platform import system


def create_shortcut_backend(shortcuts, on_keydown, on_keyup, should_suppress):
    """
    创建平台对应的快捷键后端实例。

    Args:
        shortcuts: Shortcut 配置列表
        on_keydown: 按键按下回调，签名 (key_name: str, is_mouse: bool)
        on_keyup: 按键释放回调，签名 (key_name: str, is_mouse: bool)
        should_suppress: 查询是否应抑制事件，签名 (key_name: str, is_mouse: bool) -> bool
    """
    current = system()

    if current == 'Windows':
        from .backend_windows import WindowsShortcutBackend
        return WindowsShortcutBackend(shortcuts, on_keydown, on_keyup, should_suppress)

    if current == 'Linux':
        session_type = (os.environ.get('XDG_SESSION_TYPE') or '').lower()
        display = os.environ.get('DISPLAY')

        if session_type and session_type != 'x11':
            raise RuntimeError(f"Linux 实时模式当前仅支持 X11，会话类型为: {session_type}")
        if not display:
            raise RuntimeError("Linux 实时模式需要图形会话（未检测到 DISPLAY）")

        from .backend_x11 import X11ShortcutBackend
        return X11ShortcutBackend(shortcuts, on_keydown, on_keyup, should_suppress)

    raise RuntimeError(f"当前平台暂不支持实时快捷键后端: {current}")
