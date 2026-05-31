"""环境感知服务。

这个文件负责回答一个问题：

    "用户现在大概处在什么电脑环境里？"

字段来源：
    - hour: 后端获取（系统时间）
    - active_app: 后端获取（Windows 前台窗口）
    - kpm: 前端采集后传入（键盘监听在前端做，避免权限问题）
    - backspace_ratio: 前端采集后传入
"""

import json
from datetime import datetime
from urllib import error, parse, request

from backend.config import settings


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

    active_app = get_activitywatch_active_app() or get_active_app()

    return {
        "hour": datetime.now().hour,
        "active_app": active_app,
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


def get_activitywatch_active_app() -> str | None:
    """优先从 ActivityWatch 读取前台窗口对应应用名。

    只读取本机已经运行的 ActivityWatch server；任何错误都静默回退到
    `get_active_app()`，避免影响现有 MVP 链路。
    """

    if not settings.enable_activitywatch:
        return None

    try:
        bucket_id = _pick_activitywatch_window_bucket()
        if not bucket_id:
            return None

        encoded_bucket_id = parse.quote(bucket_id, safe="")
        events = _activitywatch_get_json(
            f"/api/0/buckets/{encoded_bucket_id}/events?limit=1"
        )
        if not isinstance(events, list) or not events:
            return None

        data = events[-1].get("data") or {}
        app_name = str(data.get("app") or "").strip()
        if app_name:
            return app_name

        title = str(data.get("title") or "").strip()
        if title:
            return title[:120]
        return None
    except Exception:
        return None


def _pick_activitywatch_window_bucket() -> str | None:
    buckets = _activitywatch_get_json("/api/0/buckets/")
    if isinstance(buckets, dict):
        bucket_ids = list(buckets.keys())
    elif isinstance(buckets, list):
        bucket_ids = [str(item.get("id") or "") for item in buckets]
    else:
        bucket_ids = []

    window_buckets = [bucket_id for bucket_id in bucket_ids if "aw-watcher-window" in bucket_id]
    return sorted(window_buckets)[-1] if window_buckets else None


def _activitywatch_get_json(path: str):
    base_url = settings.activitywatch_base_url.rstrip("/")
    url = f"{base_url}{path}"
    req = request.Request(url, headers={"Accept": "application/json"}, method="GET")
    with request.urlopen(req, timeout=1.5) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload) if payload else {}
