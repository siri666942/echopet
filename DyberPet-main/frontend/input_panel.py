"""Minimal floating input panel for EchoPet."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class InputPanel(QFrame):
    submit_requested = Signal(str, str)
    mock_state_requested = Signal(str)
    feedback_requested = Signal(str, str)
    record_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._current_track_id = ""
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setObjectName("EchoPetInputPanel")
        self.resize(380, 340)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        title = QLabel("EchoPet 输入面板")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        subtitle = QLabel("输入一句话，或先录音转写到文本框，再让 EchoPet 根据当前状态推荐更合适的音乐。")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #666666;")
        root.addWidget(title)
        root.addWidget(subtitle)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("比如：我有点烦，来点适合现在的歌")
        self.editor.setMinimumHeight(90)
        root.addWidget(self.editor)

        button_row = QHBoxLayout()
        self.submit_button = QPushButton("提交")
        self.clear_button = QPushButton("清空")
        self.close_button = QPushButton("关闭")
        self.voice_button = QPushButton("开始录音")
        button_row.addWidget(self.submit_button)
        button_row.addWidget(self.clear_button)
        button_row.addStretch(1)
        button_row.addWidget(self.voice_button)
        button_row.addWidget(self.close_button)
        root.addLayout(button_row)

        self.debug_toggle_button = QPushButton("显示开发调试")
        self.debug_toggle_button.setCheckable(True)
        self.debug_toggle_button.setChecked(False)
        root.addWidget(self.debug_toggle_button, alignment=Qt.AlignLeft)

        self.debug_widget = QWidget()
        debug_layout = QVBoxLayout(self.debug_widget)
        debug_layout.setContentsMargins(0, 0, 0, 0)
        debug_layout.setSpacing(8)

        mock_title = QLabel("开发调试：快速状态切换")
        mock_title.setStyleSheet("font-weight: 600;")
        debug_layout.addWidget(mock_title)

        mock_grid = QGridLayout()
        mock_states = [
            ("待机", "idle"),
            ("专注", "focus"),
            ("疲惫", "tired"),
            ("烦躁", "frustrated"),
            ("低落", "sad"),
        ]
        for index, (label, state_name) in enumerate(mock_states):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, s=state_name: self.mock_state_requested.emit(s))
            mock_grid.addWidget(button, index // 3, index % 3)
        debug_layout.addLayout(mock_grid)
        root.addWidget(self.debug_widget)
        self.debug_widget.hide()

        info_title = QLabel("当前推荐")
        info_title.setStyleSheet("font-weight: 600;")
        root.addWidget(info_title)

        self.state_label = QLabel("状态: idle")
        self.track_label = QLabel("歌曲: 暂无")
        self.reply_label = QLabel("回复: 等你输入一句话")
        self.reply_label.setWordWrap(True)
        self.status_label = QLabel("提示: 输入一句话开始体验")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #666666;")
        root.addWidget(self.state_label)
        root.addWidget(self.track_label)
        root.addWidget(self.reply_label)
        root.addWidget(self.status_label)

        feedback_row = QHBoxLayout()
        self.like_button = QPushButton("喜欢")
        self.dislike_button = QPushButton("不喜欢")
        self.energy_button = QPushButton("更有力量")
        for button in (self.like_button, self.dislike_button, self.energy_button):
            button.setEnabled(False)
            feedback_row.addWidget(button)
        root.addLayout(feedback_row)

        self.submit_button.clicked.connect(self._emit_submit)
        self.clear_button.clicked.connect(self.editor.clear)
        self.close_button.clicked.connect(self.hide)
        self.voice_button.clicked.connect(self.record_requested.emit)
        self.like_button.clicked.connect(lambda: self._emit_feedback("positive"))
        self.dislike_button.clicked.connect(lambda: self._emit_feedback("negative"))
        self.energy_button.clicked.connect(lambda: self._emit_feedback("more_energy"))
        self.debug_toggle_button.toggled.connect(self.set_debug_tools_visible)

    def _emit_submit(self) -> None:
        text = self.editor.toPlainText().strip()
        if text:
            self.submit_requested.emit(text, "text")
        else:
            self.show_status("提示: 先输入一句话")

    def _emit_feedback(self, feedback: str) -> None:
        self.feedback_requested.emit(self._current_track_id, feedback)

    def set_busy(self, busy: bool, message: str = "") -> None:
        self.submit_button.setEnabled(not busy)
        self.clear_button.setEnabled(not busy)
        self.voice_button.setEnabled(not busy)
        if message:
            self.show_status(message)

    def show_status(self, message: str) -> None:
        self.status_label.setText(message)

    def set_debug_tools_visible(self, visible: bool) -> None:
        self.debug_widget.setVisible(visible)
        self.debug_toggle_button.setText("隐藏开发调试" if visible else "显示开发调试")

    def set_transcript(self, text: str) -> None:
        current = self.editor.toPlainText().strip()
        if current:
            self.editor.setPlainText(f"{current}\n{text}")
        else:
            self.editor.setPlainText(text)

    def set_recording(self, is_recording: bool) -> None:
        if is_recording:
            self.voice_button.setText("停止录音")
            self.show_status("提示: 正在录音，再点一次结束并转写")
        else:
            self.voice_button.setText("开始录音")

    def show_agent_result(self, mapped_result: dict) -> None:
        recommendation = mapped_result.get("recommendation") or {}
        track_title = recommendation.get("title") or "暂无"
        artist = recommendation.get("artist") or ""
        self._current_track_id = recommendation.get("id", "")

        self.state_label.setText(f"状态: {mapped_result.get('pet_state', 'idle')}")
        if artist:
            self.track_label.setText(f"歌曲: {track_title} - {artist}")
        else:
            self.track_label.setText(f"歌曲: {track_title}")
        self.reply_label.setText(f"回复: {mapped_result.get('assistant_reply', '')}")

        mode = mapped_result.get("debug_mode", "api")
        if mode == "mock":
            self.show_status("提示: 当前展示的是本地 mock 结果")
        else:
            self.show_status("提示: 已连接后端 API")

        has_track = bool(self._current_track_id)
        for button in (self.like_button, self.dislike_button, self.energy_button):
            button.setEnabled(has_track)
