$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$FrontendPython = Join-Path $RepoRoot "DyberPet-main\.venv\Scripts\python.exe"

if (-not (Test-Path $FrontendPython)) {
    throw "Frontend venv not found: $FrontendPython. Run scripts/start_echopet.ps1 -InstallFrontendDeps first."
}

Push-Location $RepoRoot
try {
    @'
import json
import sys
import time
from pathlib import Path

repo = Path.cwd()
sys.path.insert(0, str(repo / "DyberPet-main"))

from PySide6.QtCore import QCoreApplication
from frontend.agent_client import AgentClient
from frontend.local_audio_player import LocalAudioPlayer

app = QCoreApplication([])
client = AgentClient(timeout=20)

print("STEP context")
context = client.get_context(timeout=5)
print(json.dumps(context, ensure_ascii=False))

print("STEP analyze via frontend AgentClient.submit_text")
keyboard_events = {
    "window_seconds": 60,
    "active_app": context.get("active_app") or "Unknown",
    "events": [
        {"key": "CHAR", "type": "keydown", "timestamp": 1.0},
        {"key": "CHAR", "type": "keyup", "timestamp": 1.08},
        {"key": "CHAR", "type": "keydown", "timestamp": 1.2},
        {"key": "CHAR", "type": "keyup", "timestamp": 1.28},
    ],
}
result = client.submit_text(
    "我现在想听一首适合专注的歌",
    input_source="faster_whisper",
    keyboard_events=keyboard_events,
)
print(json.dumps({
    "mode": result.get("_mode"),
    "error": result.get("_error"),
    "session_id": result.get("session_id"),
    "player_status": result.get("player_status"),
    "recommendation": result.get("recommendation", {}).get("title"),
    "file_path": result.get("recommendation", {}).get("file_path"),
    "playlist_len": len(result.get("playlist") or []),
}, ensure_ascii=False))
if result.get("_mode") != "api":
    raise SystemExit("frontend AgentClient fell back to mock")

track = result["recommendation"]
player = LocalAudioPlayer(repo)
resolved = player._resolve_file_path(track.get("file_path", ""))
print("STEP resolved_path", resolved, "exists=", bool(resolved and resolved.exists()))
if not resolved or not resolved.exists():
    raise SystemExit("recommended file does not exist on frontend filesystem")

print("STEP local play")
player.set_playlist(result.get("playlist") or [], start_index=0)
player.play_track(track)
for _ in range(20):
    app.processEvents()
    time.sleep(0.1)
    if player.get_status()["status"] in {"playing", "error"}:
        break
print(json.dumps(player.get_status(), ensure_ascii=False))
if player.get_status()["status"] == "error":
    raise SystemExit("local player failed to start playback")

print("STEP pause")
player.play_current_or_resume()
for _ in range(5):
    app.processEvents()
    time.sleep(0.05)
print(json.dumps(player.get_status(), ensure_ascii=False))
if player.get_status()["status"] not in {"paused", "idle"}:
    raise SystemExit("pause did not change player status as expected")

print("STEP resume/start")
player.play_current_or_resume()
for _ in range(10):
    app.processEvents()
    time.sleep(0.1)
    if player.get_status()["status"] in {"playing", "error"}:
        break
print(json.dumps(player.get_status(), ensure_ascii=False))
if player.get_status()["status"] == "error":
    raise SystemExit("resume/start failed")

print("STEP skip")
player.skip()
for _ in range(10):
    app.processEvents()
    time.sleep(0.1)
    if player.get_status()["status"] in {"playing", "idle", "error"}:
        break
print(json.dumps(player.get_status(), ensure_ascii=False))
if (result.get("playlist") or [])[1:] and player.get_status()["status"] == "error":
    raise SystemExit("skip failed to play next track")

print("SMOKE_OK")
'@ | & $FrontendPython -
}
finally {
    Pop-Location
}
