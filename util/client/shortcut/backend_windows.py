# coding: utf-8
"""
Windows 快捷键监听后端

基于 pynput 的 win32_event_filter 实现高性能全局监听与按键抑制。
"""

from __future__ import annotations

from . import logger
from .key_mapper import (
    KEYBOARD_MESSAGES,
    KEY_DOWN_MESSAGES,
    KEY_UP_MESSAGES,
    MOUSE_MESSAGES,
    WM_XBUTTONDOWN,
    WM_XBUTTONUP,
    XBUTTON1,
    XBUTTON2,
    KeyMapper,
)


class WindowsShortcutBackend:
    """Windows 平台快捷键后端。"""

    def __init__(self, shortcuts, on_keydown, on_keyup, should_suppress):
        self.shortcuts = shortcuts
        self.on_keydown = on_keydown
        self.on_keyup = on_keyup
        self.should_suppress = should_suppress

        self.keyboard_listener = None
        self.mouse_listener = None

    def capabilities(self) -> dict:
        return {
            'supports_suppress': True,
            'supports_mouse_xbuttons': True,
        }

    def _create_keyboard_filter(self):
        def win32_event_filter(msg, data):
            if msg not in KEYBOARD_MESSAGES:
                return True

            key_name = KeyMapper.vk_to_name(data.vkCode)

            if msg in KEY_DOWN_MESSAGES:
                self.on_keydown(key_name, False)
            elif msg in KEY_UP_MESSAGES:
                self.on_keyup(key_name, False)

            if self.should_suppress(key_name, False) and self.keyboard_listener:
                self.keyboard_listener.suppress_event()

            return True

        return win32_event_filter

    def _create_mouse_filter(self):
        def win32_event_filter(msg, data):
            if msg not in MOUSE_MESSAGES:
                return True

            xbutton = (data.mouseData >> 16) & 0xFFFF
            button_name = 'x1' if xbutton == XBUTTON1 else 'x2'

            if msg == WM_XBUTTONDOWN:
                self.on_keydown(button_name, True)
            elif msg == WM_XBUTTONUP:
                self.on_keyup(button_name, True)

            if self.should_suppress(button_name, True) and self.mouse_listener:
                self.mouse_listener.suppress_event()

            return True

        return win32_event_filter

    def start(self) -> None:
        from pynput import keyboard, mouse

        has_keyboard = any(s.type == 'keyboard' for s in self.shortcuts if s.enabled)
        has_mouse = any(s.type == 'mouse' for s in self.shortcuts if s.enabled)

        if has_keyboard:
            self.keyboard_listener = keyboard.Listener(
                win32_event_filter=self._create_keyboard_filter()
            )
            self.keyboard_listener.start()
            logger.info("Windows 键盘监听器已启动")

        if has_mouse:
            self.mouse_listener = mouse.Listener(
                win32_event_filter=self._create_mouse_filter()
            )
            self.mouse_listener.start()
            logger.info("Windows 鼠标监听器已启动")

    def stop(self) -> None:
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
