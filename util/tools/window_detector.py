"""
前台窗口检测器

检测当前前台活动的应用程序信息，用于兼容性配置
"""
import platform


def get_active_window_info() -> dict:
    """
    获取当前前台窗口信息

    Returns:
        包含窗口信息的字典:
        - title: 窗口标题
        - class_name: 窗口类名
        - process_name: 进程名
        - app_name: 应用名称（推测）
    """
    system = platform.system()

    if system == 'Windows':
        return _get_windows_window_info()
    elif system == 'Darwin':  # macOS
        return _get_macos_window_info()
    elif system == 'Linux':
        return _get_linux_window_info()
    else:
        return {}


def _get_windows_window_info() -> dict:
    """Windows 平台窗口检测"""
    try:
        import win32gui
        import win32process

        hwnd = win32gui.GetForegroundWindow()

        # 获取窗口标题
        title = win32gui.GetWindowText(hwnd)

        # 获取窗口类名
        class_name = win32gui.GetClassName(hwnd)

        # 获取进程 ID 和进程名
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            import psutil
            process = psutil.Process(pid)
            process_name = process.name()
        except:
            process_name = ""

        # 推测应用名称
        app_name = _guess_app_name(title, class_name, process_name)

        return {
            'title': title,
            'class_name': class_name,
            'process_name': process_name,
            'app_name': app_name
        }
    except ImportError:
        # 如果没有安装依赖，返回空信息
        return {}
    except Exception:
        return {}


def _get_macos_window_info() -> dict:
    """macOS 平台窗口检测"""
    try:
        import subprocess
        from plistlib import loads

        # 使用 AppleScript 获取前台窗口信息
        script = '''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
            if frontApp contains "Safari" then
                tell application frontApp
                    if (count of windows) > 0 then
                        set windowTitle to name of front window
                    else
                        set windowTitle to ""
                    end if
                end tell
            else if frontApp contains "Terminal" then
                tell application frontApp
                    if (count of windows) > 0 then
                        set windowTitle to name of front window
                    else
                        set windowTitle to ""
                    end if
                end tell
            else
                set windowTitle to ""
            end if
        end tell
        return frontApp & "||" & windowTitle
        '''

        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            parts = result.stdout.strip().split('||')
            app_name = parts[0] if len(parts) > 0 else ""
            title = parts[1] if len(parts) > 1 else ""

            return {
                'title': title,
                'class_name': '',
                'process_name': app_name,
                'app_name': app_name
            }
    except Exception:
        pass

    return {}


def _get_linux_window_info() -> dict:
    """Linux 平台窗口检测"""
    try:
        import subprocess
        from pathlib import Path

        # 优先使用 xdotool 获取活动窗口
        win_id = ''
        try:
            win_id_res = subprocess.run(
                ['xdotool', 'getactivewindow'],
                capture_output=True,
                text=True
            )
            if win_id_res.returncode == 0:
                win_id = win_id_res.stdout.strip()
        except FileNotFoundError:
            pass

        # xdotool 不可用时，改用 xprop 获取活动窗口 ID
        if not win_id:
            root_res = subprocess.run(
                ['xprop', '-root', '_NET_ACTIVE_WINDOW'],
                capture_output=True,
                text=True
            )
            if root_res.returncode == 0 and '#' in root_res.stdout:
                win_hex = root_res.stdout.split('#', 1)[1].strip()
                if win_hex.lower() not in ('0x0', '0'):
                    try:
                        win_id = str(int(win_hex, 16))
                    except Exception:
                        win_id = ''

        if win_id:
            title = ''
            process_name = ''

            # 窗口标题
            try:
                title_res = subprocess.run(
                    ['xdotool', 'getwindowname', win_id],
                    capture_output=True,
                    text=True
                )
                if title_res.returncode == 0:
                    title = title_res.stdout.strip()
            except FileNotFoundError:
                pass

            # 进程 PID + 标题（wmctrl 兜底）
            pid = ''
            wm_res = subprocess.run(
                ['wmctrl', '-lp'],
                capture_output=True,
                text=True
            )
            if wm_res.returncode == 0:
                target_hex = format(int(win_id), '#010x')
                for line in wm_res.stdout.splitlines():
                    parts = line.split(None, 4)
                    if len(parts) < 5:
                        continue
                    wid, _desk, wpid, _host, wtitle = parts
                    if wid.lower() == target_hex.lower():
                        pid = wpid
                        if not title:
                            title = wtitle.strip()
                        break

            if pid.isdigit():
                comm_path = Path(f'/proc/{pid}/comm')
                if comm_path.exists():
                    process_name = comm_path.read_text(encoding='utf-8', errors='ignore').strip()

            # 窗口类名
            class_res = subprocess.run(
                ['xprop', '-id', str(int(win_id)), 'WM_CLASS'],
                capture_output=True,
                text=True
            )
            class_name = ''
            if class_res.returncode == 0:
                out = class_res.stdout.strip()
                if '=' in out:
                    class_name = out.split('=', 1)[1].strip().strip('"')

            return {
                'title': title,
                'class_name': class_name,
                'process_name': process_name,
                'app_name': process_name or (title.split()[0] if title else '')
            }
    except Exception:
        pass

    return {}


def _guess_app_name(title: str, class_name: str, process_name: str) -> str:
    """
    根据窗口信息推测应用名称

    Args:
        title: 窗口标题
        class_name: 窗口类名
        process_name: 进程名

    Returns:
        推测的应用名称
    """
    # 优先使用进程名
    if process_name:
        # 去除 .exe 后缀
        name = process_name.replace('.exe', '').lower()
        return name

    # 其次使用类名
    if class_name:
        # Windows 常见类名映射
        class_mappings = {
            'chrome': 'Chrome',
            'msedge': 'Edge',
            'firefox': 'Firefox',
            'notepad': 'Notepad',
            'notepad++': 'Notepad++',
            'vscode': 'VSCode',
            'winword': 'Word',
            'xlmain': 'Excel',
            'pptmain': 'PowerPoint',
            'wndclass_desktop_glass': 'Desktop',
        }

        class_lower = class_name.lower()
        for key, value in class_mappings.items():
            if key in class_lower:
                return value

    # 最后使用标题的第一个词
    if title:
        first_word = title.split()[0]
        return first_word

    return ''


def is_likely_editor(window_info: dict) -> bool:
    """
    判断当前窗口是否可能是编辑器

    Args:
        window_info: 窗口信息字典

    Returns:
        True 表示可能是编辑器
    """
    if not window_info:
        return True  # 默认安全起见

    title = window_info.get('title', '').lower()
    class_name = window_info.get('class_name', '').lower()
    process_name = window_info.get('process_name', '').lower()

    # 编辑器关键词
    editor_keywords = [
        'visual studio', 'vscode', 'vim', 'nano', 'emacs',
        'notepad', 'sublime', 'atom', 'intellij', 'pycharm',
        'webstorm', 'idea', 'editor'
    ]

    # 检查标题
    for keyword in editor_keywords:
        if keyword in title or keyword in class_name or keyword in process_name:
            return True

    return False


def is_likely_browser(window_info: dict) -> bool:
    """
    判断当前窗口是否可能是浏览器

    Args:
        window_info: 窗口信息字典

    Returns:
        True 表示可能是浏览器
    """
    if not window_info:
        return False

    class_name = window_info.get('class_name', '').lower()
    process_name = window_info.get('process_name', '').lower()

    browser_keywords = ['chrome', 'firefox', 'edge', 'safari', 'opera', 'brave']

    for keyword in browser_keywords:
        if keyword in class_name or keyword in process_name:
            return True

    return False
