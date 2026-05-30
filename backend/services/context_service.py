"""环境感知服务。

这个文件负责回答一个问题：

    “用户现在大概处在什么电脑环境里？”

目前 MVP 返回：
    - 当前小时
    - 当前活跃应用
    - kpm=0
    - backspace_ratio=0.0

kpm/backspace_ratio 以后可以由前端采集后传给 `/api/analyze`，
这样后端就不需要做全局键盘监听，权限问题更少。
"""

from datetime import datetime


def get_current_context() -> dict:
    """采集当前上下文。

    返回字典是为了让 API 层再用 ContextModel 做一次校验。

    字段解释：
        hour:
            当前小时。比如晚上 23 点，可能说明用户比较累。

        active_app:
            当前正在使用的软件。比如 VSCode/Cursor 说明可能在写代码。

        kpm:
            keys per minute，每分钟按键数。MVP 先返回 0。

        backspace_ratio:
            退格比例。高退格可能说明用户在反复修改、卡住。MVP 先返回 0。
    """

    return {
        "hour": datetime.now().hour,
        "active_app": get_active_app(),
        "kpm": 0,
        "backspace_ratio": 0.0,
    }


def get_active_app() -> str:
    """获取当前 Windows 前台应用名。

    这里用了三个库：
        - win32gui: 找当前前台窗口
        - win32process: 从窗口拿进程 pid
        - psutil: 根据 pid 找进程名

    如果任何一步失败，就返回 Unknown。
    这样做是为了保证接口稳定：环境采集失败不应该让整个后端崩。
    """

    try:
        import psutil
        import win32gui
        import win32process

        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name().replace(".exe", "")
    except Exception:
        return "Unknown"
