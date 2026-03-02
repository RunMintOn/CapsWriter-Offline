# coding: utf-8
"""
文本输出模块

提供 TextOutput 类用于将识别结果输出到当前窗口。
"""

from __future__ import annotations

import asyncio
import platform
from typing import Optional
import re

import keyboard
import pyclip

from config_client import ClientConfig as Config
from util.tools.window_detector import get_active_window_info
from . import logger



class TextOutput:
    """
    文本输出器
    
    提供文本输出功能，支持模拟打字和粘贴两种方式。
    """
    
    @staticmethod
    def _is_terminal_window(window_info: dict) -> bool:
        """判断当前活动窗口是否像终端。"""
        if not window_info:
            return False

        text = ' '.join([
            str(window_info.get('title', '')),
            str(window_info.get('class_name', '')),
            str(window_info.get('process_name', '')),
            str(window_info.get('app_name', '')),
        ]).lower()

        terminal_keywords = [
            'terminal', 'gnome-terminal', 'konsole', 'xterm', 'alacritty',
            'kitty', 'wezterm', 'tilix', 'tabby', 'warp', 'tmux', 'codex',
        ]
        return any(k in text for k in terminal_keywords)

    @staticmethod
    def _send_paste_hotkey(controller, key_module, is_terminal: bool) -> None:
        """
        发送粘贴快捷键。

        Linux 终端通常使用 Ctrl+Shift+V，其他应用使用 Ctrl+V。
        """
        if platform.system() == 'Darwin':
            with controller.pressed(key_module.Key.cmd):
                controller.tap('v')
            return

        # Windows/Linux 常规
        if not is_terminal:
            with controller.pressed(key_module.Key.ctrl):
                controller.tap('v')
            return

        # Linux 终端：优先 Ctrl+Shift+V，回退 Shift+Insert
        try:
            with controller.pressed(key_module.Key.ctrl):
                with controller.pressed(key_module.Key.shift):
                    controller.tap('v')
        except Exception:
            with controller.pressed(key_module.Key.shift):
                controller.tap(key_module.Key.insert)

    @staticmethod
    def strip_punc(text: str) -> str:
        """
        消除末尾最后一个标点
        
        Args:
            text: 原始文本
            
        Returns:
            去除末尾标点后的文本
        """
        if not text or not Config.trash_punc:
            return text
        clean_text = re.sub(f"(?<=.)[{Config.trash_punc}]$", "", text)
        return clean_text
    
    async def output(self, text: str, paste: Optional[bool] = None) -> None:
        """
        输出识别结果
        
        根据配置选择使用模拟打字或粘贴方式输出文本。
        
        Args:
            text: 要输出的文本
            paste: 是否使用粘贴方式（None 表示使用配置值）
        """
        if not text:
            return
        
        # 确定输出方式
        if paste is None:
            paste = Config.paste
        
        if paste:
            await self._paste_text(text)
        else:
            self._type_text(text)
    
    async def _paste_text(self, text: str) -> None:
        """
        通过粘贴方式输出文本
        
        Args:
            text: 要粘贴的文本
        """
        logger.debug(f"使用粘贴方式输出文本，长度: {len(text)}")
        
        # 保存剪贴板
        try:
            temp = pyclip.paste().decode('utf-8')
        except Exception:
            temp = ''
        
        # 复制结果（失败则降级为打字输出）
        try:
            pyclip.copy(text)
        except Exception as e:
            logger.warning(f"剪贴板不可用，降级为打字输出: {e}")
            self._type_text(text)
            return

        # 粘贴结果（优先使用 pynput）
        try:
            from pynput import keyboard as pynput_keyboard

            window_info = get_active_window_info()
            is_terminal = self._is_terminal_window(window_info)

            controller = pynput_keyboard.Controller()
            self._send_paste_hotkey(controller, pynput_keyboard, is_terminal)
        except Exception as e:
            logger.warning(f"pynput 粘贴失败，降级 keyboard.press_and_release: {e}")
            try:
                # 终端场景优先尝试 Ctrl+Shift+V
                window_info = get_active_window_info()
                if self._is_terminal_window(window_info):
                    keyboard.press_and_release('ctrl+shift+v')
                else:
                    keyboard.press_and_release('ctrl+v')
            except Exception as ex:
                logger.warning(f"keyboard 粘贴失败，降级打字输出: {ex}")
                self._type_text(text)
        
        logger.debug("已发送粘贴命令")
        
        # 还原剪贴板
        if Config.restore_clip:
            await asyncio.sleep(0.1)
            try:
                pyclip.copy(temp)
                logger.debug("剪贴板已恢复")
            except Exception as e:
                logger.warning(f"恢复剪贴板失败: {e}")
    
    def _type_text(self, text: str) -> None:
        """
        通过模拟打字方式输出文本

        Windows 优先使用 keyboard.write；
        Linux/macOS 使用 pynput Controller.type，避免 keyboard 库权限问题。

        Args:
            text: 要输出的文本
        """
        logger.debug(f"使用打字方式输出文本，长度: {len(text)}")
        if platform.system() == 'Windows':
            keyboard.write(text)
            return

        try:
            from pynput import keyboard as pynput_keyboard
            controller = pynput_keyboard.Controller()
            controller.type(text)
        except Exception as e:
            logger.warning(f"pynput 打字输出失败，降级到 keyboard.write: {e}")
            keyboard.write(text)
