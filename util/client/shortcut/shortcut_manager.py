# coding: utf-8
"""
快捷键管理器（跨平台后端版）

负责：
1. 管理快捷键任务状态
2. 处理按下/释放逻辑
3. 与平台后端解耦（Windows / Linux X11）
"""

import time
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Dict, List

from . import logger
from util.client.shortcut.emulator import ShortcutEmulator
from util.client.shortcut.event_handler import ShortcutEventHandler
from util.client.shortcut.task import ShortcutTask
from util.client.shortcut.backend_factory import create_shortcut_backend

if TYPE_CHECKING:
    from util.client.shortcut.shortcut_config import Shortcut
    from util.client.state import ClientState


class ShortcutManager:
    """统一管理多个快捷键任务与平台监听后端。"""

    def __init__(self, state: 'ClientState', shortcuts: List['Shortcut']):
        self.state = state
        self.shortcuts = shortcuts

        # 快捷键任务映射（key -> ShortcutTask）
        self.tasks: Dict[str, ShortcutTask] = {}

        # 线程池
        self._pool = ThreadPoolExecutor(max_workers=4)

        # 按键模拟器
        self._emulator = ShortcutEmulator()

        # 按键恢复状态追踪
        self._restoring_keys = set()

        # 事件处理器
        self._event_handler = ShortcutEventHandler(self.tasks, self._pool, self._emulator)

        # 初始化任务
        self._init_tasks()

        # 选择平台后端
        self._backend = create_shortcut_backend(
            shortcuts=self.shortcuts,
            on_keydown=self._on_backend_keydown,
            on_keyup=self._on_backend_keyup,
            should_suppress=self._should_suppress,
        )
        self._backend_caps = self._backend.capabilities()
        self._apply_capability_degradation()

    def _init_tasks(self) -> None:
        """初始化所有快捷键任务。"""
        from config_client import ClientConfig as Config

        for shortcut in self.shortcuts:
            if not shortcut.enabled:
                continue

            task = ShortcutTask(shortcut, self.state)
            task._manager_ref = lambda: self  # 弱引用回调
            task.pool = self._pool
            task.threshold = shortcut.get_threshold(Config.threshold)
            self.tasks[shortcut.key] = task

    def _apply_capability_degradation(self) -> None:
        """根据后端能力进行运行时降级。"""
        if not self._backend_caps.get('supports_suppress', False):
            for task in self.tasks.values():
                if task.shortcut.suppress:
                    logger.warning(
                        f"[{task.shortcut.key}] 当前后端不支持 suppress，已自动降级为非阻塞监听"
                    )
                    task.shortcut.suppress = False

        if not self._backend_caps.get('supports_mouse_xbuttons', False):
            for key, task in list(self.tasks.items()):
                if task.shortcut.type == 'mouse':
                    logger.warning(f"[{task.shortcut.key}] 当前后端不支持鼠标侧键，已跳过")
                    self.tasks.pop(key, None)

    def _task_for(self, key_name: str):
        return self.tasks.get(key_name)

    def _on_backend_keydown(self, key_name: str, is_mouse: bool) -> None:
        if self._check_emulating(key_name, is_release=False):
            return
        if not is_mouse and self._check_restoring(key_name, is_release=False):
            return

        task = self._task_for(key_name)
        if not task:
            return

        self._event_handler.handle_keydown(key_name, task)

    def _on_backend_keyup(self, key_name: str, is_mouse: bool) -> None:
        if self._check_emulating(key_name, is_release=True):
            return
        if not is_mouse and self._check_restoring(key_name, is_release=True):
            return

        task = self._task_for(key_name)
        if not task:
            return

        if is_mouse:
            self._handle_mouse_keyup(key_name, task)
        else:
            self._event_handler.handle_keyup(key_name, task)

    def _handle_mouse_keyup(self, button_name: str, task) -> None:
        """处理鼠标按键释放事件。"""
        # 单击模式
        if not task.shortcut.hold_mode:
            if task.pressed:
                task.pressed = False
                task.released = True
                task.event.set()
            return

        # 长按模式
        if not task.is_recording:
            return

        duration = time.time() - task.recording_start_time
        logger.debug(f"[{button_name}] 松开按键，持续时间: {duration:.3f}s")

        if duration < task.threshold:
            task.cancel()
            if task.shortcut.suppress:
                logger.debug(f"[{button_name}] 安排异步补发鼠标按键")
                self._pool.submit(self._emulator.emulate_mouse_click, button_name)
        else:
            task.finish()

    def _should_suppress(self, key_name: str, is_mouse: bool) -> bool:
        task = self._task_for(key_name)
        return bool(task and task.shortcut.suppress)

    def schedule_restore(self, key: str) -> None:
        """
        安排按键恢复（延迟执行，避免在事件处理中阻塞）。
        """
        self._restoring_keys.add(key)

        def do_restore():
            import time
            from pynput import keyboard

            time.sleep(0.05)  # 延迟 50ms
            if key == 'caps_lock':
                controller = keyboard.Controller()
                controller.press(keyboard.Key.caps_lock)
                controller.release(keyboard.Key.caps_lock)

        self._pool.submit(do_restore)

    def is_restoring(self, key: str) -> bool:
        return key in self._restoring_keys

    def clear_restoring_flag(self, key: str) -> None:
        self._restoring_keys.discard(key)

    def _check_emulating(self, key_name: str, is_release: bool) -> bool:
        if not self._emulator.is_emulating(key_name):
            return False

        if is_release:
            self._emulator.clear_emulating_flag(key_name)
        return True

    def _check_restoring(self, key_name: str, is_release: bool) -> bool:
        if not self.is_restoring(key_name):
            return False

        if is_release:
            self.clear_restoring_flag(key_name)
        return True

    def start(self) -> None:
        """启动平台监听后端。"""
        self._backend.start()
        logger.info(
            "快捷键后端已启动: %s (supports_suppress=%s, supports_mouse_xbuttons=%s)",
            self._backend.__class__.__name__,
            self._backend_caps.get('supports_suppress', False),
            self._backend_caps.get('supports_mouse_xbuttons', False),
        )

        for shortcut in self.shortcuts:
            if shortcut.enabled:
                mode = "长按" if shortcut.hold_mode else "单击"
                toggle = "可恢复" if shortcut.is_toggle_key() else "普通键"
                logger.info(f"  [{shortcut.key}] {mode}模式, 阻塞:{shortcut.suppress}, {toggle}")

    def stop(self) -> None:
        """停止监听器并清理资源。"""
        try:
            self._backend.stop()
        except Exception as e:
            logger.warning(f"停止快捷键后端时发生错误: {e}")

        for task in self.tasks.values():
            if task.is_recording:
                task.cancel()

        self._pool.shutdown(wait=False)
        logger.debug("快捷键管理器线程池已关闭")
