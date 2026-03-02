# coding: utf-8
"""
服务端 UI 门面模块

该模块作为服务端访问 UI 功能的统一入口。
在导入此模块时，会自动将服务端的 logger 注入到通用 UI 模块中。
并重新导出服务端需要的 UI 组件。
"""

from .. import logger
import util.ui

# 1. 注入 Server Logger 到通用 UI 模块
util.ui.set_ui_logger(logger)

def enable_min_to_tray(*args, **kwargs):
    return util.ui.enable_min_to_tray(*args, **kwargs)


def stop_tray(*args, **kwargs):
    return util.ui.stop_tray(*args, **kwargs)


def toast(*args, **kwargs):
    """服务端 toast 调用（在无 GUI 环境自动降级）。"""
    return util.ui.toast(*args, **kwargs)


__all__ = [
    'logger',
    'enable_min_to_tray',
    'stop_tray',
    'toast',
]
