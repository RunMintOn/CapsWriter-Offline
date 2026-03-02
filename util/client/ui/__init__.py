# coding: utf-8
"""
客户端 UI 门面模块

该模块作为客户端访问 UI 功能的统一入口。
在导入此模块时，会自动将客户端的 logger 注入到通用 UI 模块中。
并重新导出常用的 UI 组件。
"""

from .. import logger
import util.ui

# 1. 注入 Client Logger 到通用 UI 模块
util.ui.set_ui_logger(logger)

# 2. 导出客户端特有的 UI 组件
from util.client.ui.tips import TipsDisplay

def toast(*args, **kwargs):
    """延迟调用通用 UI 的 toast。"""
    return util.ui.toast(*args, **kwargs)


def toast_stream(*args, **kwargs):
    """延迟调用通用 UI 的流式 toast。"""
    return util.ui.toast_stream(*args, **kwargs)


def enable_min_to_tray(*args, **kwargs):
    """延迟调用通用 UI 的托盘功能。"""
    return util.ui.enable_min_to_tray(*args, **kwargs)


def stop_tray(*args, **kwargs):
    """延迟调用通用 UI 的停止托盘功能。"""
    return util.ui.stop_tray(*args, **kwargs)


# 3. 透传 toast 相关类型（可能为 None，取决于平台依赖）
ToastMessage = util.ui.ToastMessage
ToastMessageManager = util.ui.ToastMessageManager

def on_add_rectify_record(*args, **kwargs):
    from util.ui.rectify_menu_handler import on_add_rectify_record as _impl
    return _impl(*args, **kwargs)


def on_add_hotword(*args, **kwargs):
    from util.ui.hotword_menu_handler import on_add_hotword as _impl
    return _impl(*args, **kwargs)


def on_edit_context(*args, **kwargs):
    from util.ui.context_menu_handler import on_edit_context as _impl
    return _impl(*args, **kwargs)

__all__ = [
    'logger',
    'TipsDisplay',
    'toast',
    'toast_stream',
    'ToastMessage',
    'ToastMessageManager',
    'enable_min_to_tray',
    'stop_tray',
    'on_add_rectify_record',
    'on_add_hotword',
    'on_edit_context',
]
