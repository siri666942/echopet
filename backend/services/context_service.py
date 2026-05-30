"""环境感知服务。

这个文件负责回答一个问题：

    "用户现在大概处在什么电脑环境里？"

字段来源：
    - hour: 后端获取（系统时间）
    - active_app: 后端获取（Windows 前台窗口）
    - kpm: 前端采集后传入（键盘监听在前端做，避免权限问题）
    - backspace_ratio: 前端采集后传入
"""

from datetime import datetime


def get_current_context(kpm: int = 0, backspace_ratio: float = 0.0) -> dict:
    """采集当前上下文。

    参数：
        kpm:
            keys per minute，每分钟按键数。
            由前端采集后通过 query 参数传入。
            前端没传时默认 0。

        backspace_ratio:
            退格键比例，0 到 1。
            由前端采集后通过 query 参数传入。
            前端没传时默认 0.0。

    返回字典，API 层再用 ContextModel 做一次校验。
    """

    return {
        "hour": datetime.now().hour,
        "active_app": get_active_app(),
        "kpm": kpm,
        "backspace_ratio": backspace_ratio,
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
