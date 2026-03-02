"""UI 工具模块

提供 Toast 浮动消息通知和系统托盘功能。
该模块设计为 Client 和 Server 共用，日志记录器通过注入方式加载。
"""
import logging

# ============================================================
# Logger 代理机制
# ============================================================

class _LoggerProxy:
    """
    日志代理类（利用 __getattr__ 动态转发）
    允许先导入 logger 对象，稍后再注入真正的实现。
    """
    def __init__(self):
        self._target = logging.getLogger('util.ui')  # 默认 logger

    def set_target(self, logger):
        """注入真正的 logger 实现"""
        self._target = logger

    def __getattr__(self, name):
        """将所有属性访问转发给真正的 logger"""
        return getattr(self._target, name)

# 1. 创建代理实例
logger = _LoggerProxy()

def set_ui_logger(real_logger):
    """设置 UI 模块使用的日志记录器"""
    logger.set_target(real_logger)

# tray 模块在 Linux 无 GUI 的情况下也可安全导入（内部已做平台检测）
from .tray import enable_min_to_tray, stop_tray

# toast 相关导入改为延迟加载，避免在无 tkinter 环境下导入失败
_toast_import_error = None
ToastMessage = None
ToastMessageManager = None


def _load_toast_symbols() -> bool:
    """按需导入 toast 相关符号。"""
    global _toast_import_error, ToastMessage, ToastMessageManager
    if ToastMessage is not None and ToastMessageManager is not None:
        return True
    if _toast_import_error is not None:
        return False

    try:
        from .toast import ToastMessage as _ToastMessage
        from .toast import ToastMessageManager as _ToastMessageManager
        ToastMessage = _ToastMessage
        ToastMessageManager = _ToastMessageManager
        return True
    except Exception as e:
        _toast_import_error = e
        logger.warning(f"Toast 功能不可用，已自动降级: {e}")
        return False


def toast(*args, **kwargs):
    """显示 Toast；若依赖不可用则降级为日志输出。"""
    if not _load_toast_symbols():
        if args:
            logger.info(f"[Toast降级] {args[0]}")
        return None

    from .toast import toast as _toast
    return _toast(*args, **kwargs)


def toast_stream(*args, **kwargs):
    """流式 Toast；若依赖不可用则静默降级。"""
    if not _load_toast_symbols():
        return None

    from .toast import toast_stream as _toast_stream
    return _toast_stream(*args, **kwargs)

__all__ = [
    'logger',
    'set_ui_logger',
    'toast',
    'toast_stream',
    'ToastMessage',
    'ToastMessageManager',
    'enable_min_to_tray',
    'stop_tray',
]
