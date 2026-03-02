# coding: utf-8
"""
Linux X11 快捷键监听后端

基于 pynput 的 on_press/on_release 回调实现全局监听。
本后端不支持 suppress（按键阻塞）。
"""

from __future__ import annotations

from . import logger
from .key_mapper import KeyMapper


class X11ShortcutBackend:
    """Linux X11 平台快捷键后端。"""

    def __init__(self, shortcuts, on_keydown, on_keyup, should_suppress):
        self.shortcuts = shortcuts
        self.on_keydown = on_keydown
        self.on_keyup = on_keyup
        self.should_suppress = should_suppress

        self.keyboard_listener = None
        self.mouse_listener = None
        self._pressed_keys = set()
        self._pressed_mouse = set()

    def capabilities(self) -> dict:
        return {
            'supports_suppress': False,
            'supports_mouse_xbuttons': True,
        }

    def _on_press(self, key):
        key_name = KeyMapper.pynput_key_to_name(key)
        if not key_name:
            return
        if key_name in self._pressed_keys:
            return  # 忽略自动重复触发
        self._pressed_keys.add(key_name)
        self.on_keydown(key_name, False)

    def _on_release(self, key):
        key_name = KeyMapper.pynput_key_to_name(key)
        if not key_name:
            return
        self._pressed_keys.discard(key_name)
        self.on_keyup(key_name, False)

    def _on_click(self, _x, _y, button, pressed):
        button_name = KeyMapper.pynput_button_to_name(button)
        if button_name not in ('x1', 'x2'):
            return

        if pressed:
            if button_name in self._pressed_mouse:
                return
            self._pressed_mouse.add(button_name)
            self.on_keydown(button_name, True)
        else:
            self._pressed_mouse.discard(button_name)
            self.on_keyup(button_name, True)

    def start(self) -> None:
        try:
            from pynput import keyboard, mouse
        except Exception as e:
            raise RuntimeError(f"X11 快捷键监听初始化失败: {e}") from e

        has_keyboard = any(s.type == 'keyboard' for s in self.shortcuts if s.enabled)
        has_mouse = any(s.type == 'mouse' for s in self.shortcuts if s.enabled)

        if has_keyboard:
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
            )
            self.keyboard_listener.start()
            logger.info("X11 键盘监听器已启动（非阻塞）")

        if has_mouse:
            self.mouse_listener = mouse.Listener(
                on_click=self._on_click
            )
            self.mouse_listener.start()
            logger.info("X11 鼠标监听器已启动（非阻塞）")

    def stop(self) -> None:
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
