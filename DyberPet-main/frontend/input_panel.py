"""Minimal floating input panel for EchoPet. Retro Walkman Style."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, Qt, Signal, QSize
from PySide6.QtGui import QFont, QPainter, QPixmap, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

DEBUG_FORM_BUTTONS = [
    ("普通", "idle"),
    ("专注", "focus"),
    ("高压", "focused_stressed"),
    ("疲惫", "tired"),
    ("烦躁", "frustrated"),
    ("难过", "sad"),
]

STATE_LABELS = {
    "idle": "普通",
    "focus": "专注",
    "focused_stressed": "高压",
    "tired": "疲惫",
    "frustrated": "烦躁",
    "sad": "难过",
}


class InputPanel(QFrame):
    submit_requested = Signal(str, str)
    mock_state_requested = Signal(str)
    player_event_requested = Signal(str, float, str)
    pause_requested = Signal()
    skip_requested = Signal()
    record_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._current_track_id = ""
        self._current_session_id = ""
        self._drag_active = False
        self._drag_offset = QPoint()
        self._build_ui()
        self._apply_styles()

    def _build_avatar_pixmap(self, target_width: int, target_height: int) -> QPixmap:
        img_path = Path(__file__).resolve().parents[2] / "1.png"
        source = QPixmap(str(img_path))
        if source.isNull():
            return QPixmap()

        inner_width = max(1, target_width - 14)
        inner_height = max(1, target_height - 10)
        scale = min(inner_width / source.width(), inner_height / source.height()) * 0.96
        scaled = source.scaled(
            max(1, int(source.width() * scale)),
            max(1, int(source.height() * scale)),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        canvas = QPixmap(target_width, target_height)
        canvas.fill(Qt.transparent)
        painter = QPainter(canvas)
        x = (target_width - scaled.width()) // 2
        y = max(2, (target_height - scaled.height()) // 2)
        painter.drawPixmap(x, y, scaled)
        painter.end()
        return canvas

    def _build_ui(self) -> None:
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setObjectName("EchoPetInputPanel")
        self.resize(620, 660)

        # Main container to simulate the physical plastic casing
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.casing = QFrame()
        self.casing.setObjectName("Casing")
        casing_layout = QVBoxLayout(self.casing)
        casing_layout.setContentsMargins(14, 14, 14, 14)
        casing_layout.setSpacing(10)
        main_layout.addWidget(self.casing)

        # --- Top Section: Brand Header ---
        brand_row = QHBoxLayout()
        brand_meta = QLabel("VERSION 1.0.0\nBUILT WITH ♥")
        brand_meta.setObjectName("BrandMeta")
        brand_name = QLabel("EchoPet")
        brand_name.setObjectName("AppTitle")
        brand_subtitle = QLabel("EMOTIONAL MUSIC AI")
        brand_subtitle.setObjectName("AppSubtitle")
        brand_center = QVBoxLayout()
        brand_center.setSpacing(0)
        brand_center.addWidget(brand_name, alignment=Qt.AlignCenter)
        brand_center.addWidget(brand_subtitle, alignment=Qt.AlignCenter)

        header_controls = QHBoxLayout()
        header_controls.setSpacing(5)
        self.min_button = QPushButton("−")
        self.min_button.setObjectName("SmallBtn")
        self.min_button.setFixedSize(22, 22)
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("SmallBtn")
        self.close_button.setFixedSize(22, 22)
        header_controls.addWidget(self.min_button)
        header_controls.addWidget(self.close_button)

        brand_row.addWidget(brand_meta)
        brand_row.addStretch()
        brand_row.addLayout(brand_center)
        brand_row.addStretch()
        brand_row.addLayout(header_controls)
        casing_layout.addLayout(brand_row)

        # --- Top Section: Header & Input (The "Cassette" Area) ---
        header_layout = QHBoxLayout()
        title = QLabel("01 INPUT")
        title.setObjectName("BrandTitle")
        
        tape_label = QLabel("TAPE INPUT ▼")
        tape_label.setObjectName("LcdSmall")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(tape_label)
        header_layout.addSpacing(20)
        casing_layout.addLayout(header_layout)

        # Input Area (Tape / Paper note style)
        input_container = QFrame()
        input_container.setObjectName("InputContainer")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(14, 14, 14, 14)
        input_layout.setSpacing(14)

        # Tape Cassette Frame
        tape_frame = QFrame()
        tape_frame.setObjectName("TapeFrame")
        tape_vbox = QVBoxLayout(tape_frame)
        tape_vbox.setContentsMargins(12, 12, 12, 12)
        tape_vbox.setSpacing(8)

        tape_header = QLabel("HOW ARE YOU FEELING?")
        tape_header.setObjectName("TapeMeta")
        tape_vbox.addWidget(tape_header, alignment=Qt.AlignLeft)

        note_strip = QFrame()
        note_strip.setObjectName("TapeNote")
        note_layout = QVBoxLayout(note_strip)
        note_layout.setContentsMargins(16, 10, 16, 10)
        note_layout.setSpacing(6)

        self.editor = QPlainTextEdit()
        self.editor.setObjectName("TapeInput")
        self.editor.setPlaceholderText("I miss the summer nights and old friends...")
        self.editor.setMinimumHeight(52)
        self.editor.setMaximumHeight(64)
        note_layout.addWidget(self.editor)
        submit_row = QHBoxLayout()
        submit_row.addStretch()
        self.submit_button = QPushButton("[ SEND ]")
        self.submit_button.setObjectName("ActionBtn")
        self.submit_button.setMinimumHeight(34)
        submit_row.addWidget(self.submit_button)
        note_layout.addLayout(submit_row)
        tape_vbox.addWidget(note_strip)

        reel_row = QHBoxLayout()
        reel_row.setSpacing(14)
        self.left_reel = QFrame()
        self.left_reel.setObjectName("TapeReel")
        left_reel_layout = QVBoxLayout(self.left_reel)
        left_reel_layout.setContentsMargins(0, 0, 0, 0)
        self.left_hub = QLabel()
        self.left_hub.setObjectName("TapeHub")
        left_reel_layout.addWidget(self.left_hub, alignment=Qt.AlignCenter)
        self.tape_window = QFrame()
        self.tape_window.setObjectName("TapeWindow")
        tape_window_layout = QHBoxLayout(self.tape_window)
        tape_window_layout.setContentsMargins(16, 12, 16, 12)
        tape_window_layout.setSpacing(10)
        self.left_band = QFrame()
        self.left_band.setObjectName("TapeBand")
        self.center_band = QFrame()
        self.center_band.setObjectName("TapeBandCenter")
        self.right_band = QFrame()
        self.right_band.setObjectName("TapeBand")
        tape_window_layout.addWidget(self.left_band)
        tape_window_layout.addWidget(self.center_band, stretch=1)
        tape_window_layout.addWidget(self.right_band)

        self.right_reel = QFrame()
        self.right_reel.setObjectName("TapeReel")
        right_reel_layout = QVBoxLayout(self.right_reel)
        right_reel_layout.setContentsMargins(0, 0, 0, 0)
        self.right_hub = QLabel()
        self.right_hub.setObjectName("TapeHub")
        right_reel_layout.addWidget(self.right_hub, alignment=Qt.AlignCenter)
        reel_row.addWidget(self.left_reel)
        reel_row.addWidget(self.tape_window, stretch=1)
        reel_row.addWidget(self.right_reel)
        tape_vbox.addLayout(reel_row)

        tape_badge_row = QHBoxLayout()
        self.tape_type_label = QLabel("TYPE I (NORMAL)\nNORMAL BIAS 120us EQ")
        self.tape_type_label.setObjectName("TapeSmallLabel")
        self.tape_model_label = QLabel("EF90")
        self.tape_model_label.setObjectName("TapeModelLabel")
        tape_badge_row.addWidget(self.tape_type_label)
        tape_badge_row.addStretch()
        tape_badge_row.addWidget(self.tape_model_label)
        tape_vbox.addLayout(tape_badge_row)

        deck_slots = QHBoxLayout()
        deck_slots.setSpacing(12)
        for _ in range(4):
            slot = QFrame()
            slot.setObjectName("DeckSlot")
            slot.setFixedSize(12, 8)
            deck_slots.addWidget(slot)
        deck_slots.addStretch()
        tape_vbox.addLayout(deck_slots)
        
        input_layout.addWidget(tape_frame, stretch=4)

        # Big Red Record Button
        record_panel = QFrame()
        record_panel.setObjectName("RecordPanel")
        record_layout = QVBoxLayout(record_panel)
        record_layout.setContentsMargins(8, 8, 8, 8)
        record_layout.setSpacing(10)

        rec_header = QHBoxLayout()
        self.voice_button = QPushButton()
        self.voice_button.setObjectName("RecordBtn")
        self.voice_button.setText("VOICE")
        self.voice_button.setFixedSize(76, 76)
        rec_label = QLabel("REC")
        rec_label.setObjectName("RecLabel")
        self.rec_dot = QLabel("●")
        self.rec_dot.setObjectName("RecDot")
        rec_header.addWidget(rec_label)
        rec_header.addStretch()
        rec_header.addWidget(self.rec_dot)

        press_label = QLabel("PRESS TO RECORD")
        press_label.setObjectName("LcdSmall")
        press_label.setAlignment(Qt.AlignCenter)

        level_title = QLabel("INPUT LEVEL")
        level_title.setObjectName("TapeMeta")
        level_row = QHBoxLayout()
        level_row.setSpacing(3)
        for index in range(14):
            meter = QFrame()
            meter.setFixedSize(7, 16)
            meter.setObjectName("MeterSegOn" if index >= 10 else "MeterSeg")
            level_row.addWidget(meter)
        channel_label = QLabel("L   R")
        channel_label.setObjectName("TapeMeta")
        self.rec_info = QLabel("AUTO MIC\nNOISE FILTER")
        self.rec_info.setObjectName("RecInfo")
        self.rec_info.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        record_layout.addLayout(rec_header)
        record_layout.addWidget(self.voice_button, alignment=Qt.AlignHCenter)
        record_layout.addWidget(press_label)
        transport_row = QHBoxLayout()
        transport_row.setSpacing(8)
        self.pause_button = QPushButton("[ PAUSE ]")
        self.skip_button = QPushButton("[ SKIP ]")
        for btn in (self.pause_button, self.skip_button):
            btn.setObjectName("TransportBtn")
            btn.setMinimumHeight(34)
            btn.setEnabled(False)
            transport_row.addWidget(btn)
        record_layout.addLayout(transport_row)
        record_layout.addSpacing(6)
        record_layout.addWidget(level_title, alignment=Qt.AlignLeft)
        record_layout.addLayout(level_row)
        record_layout.addWidget(channel_label, alignment=Qt.AlignRight)
        record_layout.addSpacing(8)
        record_layout.addWidget(self.rec_info, alignment=Qt.AlignRight)
        record_layout.addStretch()
        input_layout.addWidget(record_panel)

        casing_layout.addWidget(input_container)

        self.status_label = QLabel("TYPE OR THINK. ECHOPET LISTENS.")
        self.status_label.setObjectName("StatusLed")
        casing_layout.addWidget(self.status_label, alignment=Qt.AlignHCenter)

        self.debug_panel = QFrame()
        self.debug_panel.setObjectName("DebugPanel")
        debug_layout = QVBoxLayout(self.debug_panel)
        debug_layout.setContentsMargins(12, 10, 12, 12)
        debug_layout.setSpacing(8)

        debug_header = QLabel("03 DEBUG FORMS ▼")
        debug_header.setObjectName("LcdSmall")
        debug_layout.addWidget(debug_header)

        debug_grid = QGridLayout()
        debug_grid.setContentsMargins(0, 0, 0, 0)
        debug_grid.setHorizontalSpacing(8)
        debug_grid.setVerticalSpacing(8)
        self.debug_form_buttons: list[QPushButton] = []
        for index, (label, state_name) in enumerate(DEBUG_FORM_BUTTONS):
            button = QPushButton(f"[ {label} ]")
            button.setObjectName("DebugFormBtn")
            button.setMinimumHeight(38)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.clicked.connect(
                lambda _checked=False, state_name=state_name: self.mock_state_requested.emit(state_name)
            )
            debug_grid.addWidget(button, index // 2, index % 2)
            self.debug_form_buttons.append(button)
        debug_grid.setColumnStretch(0, 1)
        debug_grid.setColumnStretch(1, 1)
        debug_layout.addLayout(debug_grid)

        # --- Bottom Section: Music Card (The "LCD / Player" Area) ---
        bottom_container = QFrame()
        bottom_container.setObjectName("BottomContainer")
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(12, 12, 12, 12)
        bottom_layout.setSpacing(16)

        # Left: Avatar card
        avatar_panel = QFrame()
        avatar_panel.setObjectName("MusicCardPanel")
        avatar_panel.setFixedWidth(190)
        avatar_layout = QVBoxLayout(avatar_panel)
        avatar_layout.setContentsMargins(8, 8, 8, 8)
        avatar_layout.setSpacing(6)
        avatar_header = QLabel("02 MUSIC CARD ▼")
        avatar_header.setObjectName("LcdSmall")
        avatar_layout.addWidget(avatar_header)
        
        self.avatar_label = QLabel()
        self.avatar_label.setObjectName("AvatarPlaceholder")
        self.avatar_label.setFixedSize(128, 160)
        self.avatar_label.setAlignment(Qt.AlignCenter)

        avatar_pixmap = self._build_avatar_pixmap(124, 156)
        if not avatar_pixmap.isNull():
            self.avatar_label.setPixmap(avatar_pixmap)
        else:
            self.avatar_label.setText("Avatar")
            
        avatar_layout.addWidget(self.avatar_label)
        
        self.state_label = QLabel("STATE: IDLE")
        self.state_label.setObjectName("MiniTag")
        self.state_label.setAlignment(Qt.AlignCenter)
        avatar_layout.addWidget(self.state_label)
        avatar_layout.addStretch()
        bottom_layout.addWidget(avatar_panel)

        # Right: LCD Screen & Feedback
        lcd_panel = QFrame()
        lcd_panel.setObjectName("PlayerPanel")
        lcd_layout = QVBoxLayout(lcd_panel)
        lcd_layout.setContentsMargins(8, 8, 8, 8)
        lcd_layout.setSpacing(10)
        
        self.lcd_screen = QFrame()
        self.lcd_screen.setObjectName("LcdScreen")
        screen_layout = QVBoxLayout(self.lcd_screen)
        screen_layout.setContentsMargins(12, 8, 12, 8)
        
        playing_header = QLabel("▶ NOW PLAYING")
        playing_header.setObjectName("LcdSmall")
        self.track_label = QLabel("Waiting for vibe...")
        self.track_label.setObjectName("LcdLarge")
        self.track_label.setWordWrap(True)
        self.reply_label = QLabel("...")
        self.reply_label.setObjectName("LcdMedium")
        self.reply_label.setWordWrap(True)
        
        self.match_label = QLabel("♡ EMOTIONAL MATCH             --%")
        self.match_label.setObjectName("LcdSmall")
        self.progress_label = QLabel("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
        self.progress_label.setObjectName("LcdSmall")
        
        top_screen_row = QHBoxLayout()
        self.screen_meta_left = QLabel("▶ NOW PLAYING")
        self.screen_meta_left.setObjectName("LcdSmall")
        self.screen_meta_right = QLabel("04:12  ▮▮▮")
        self.screen_meta_right.setObjectName("LcdSmall")
        top_screen_row.addWidget(self.screen_meta_left)
        top_screen_row.addStretch()
        top_screen_row.addWidget(self.screen_meta_right)

        screen_layout.addLayout(top_screen_row)
        screen_layout.addWidget(self.track_label)
        screen_layout.addWidget(self.reply_label)
        screen_layout.addStretch()
        screen_layout.addWidget(self.match_label)
        screen_layout.addWidget(self.progress_label)
        
        lcd_layout.addWidget(self.lcd_screen)

        bottom_layout.addWidget(lcd_panel, stretch=1)

        casing_layout.addWidget(bottom_container)
        casing_layout.addWidget(self.debug_panel)

        self.nameplate = QLabel("ECHOPET WALKMAN INTERFACE")
        self.nameplate.setObjectName("Nameplate")
        self.nameplate.setAlignment(Qt.AlignLeft)
        casing_layout.addWidget(self.nameplate)

        # Connect signals
        self.min_button.clicked.connect(self.showMinimized)
        self.close_button.clicked.connect(self.hide)
        self.voice_button.clicked.connect(self.record_requested.emit)
        self.submit_button.clicked.connect(self._emit_submit)
        self.pause_button.clicked.connect(self.pause_requested.emit)
        self.skip_button.clicked.connect(self.skip_requested.emit)
        for widget in (
            self,
            self.casing,
            brand_meta,
            brand_name,
            brand_subtitle,
            input_container,
            bottom_container,
            avatar_panel,
            lcd_panel,
        ):
            widget.installEventFilter(self)
        self.editor.installEventFilter(self)

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            QFrame#Casing {
                background-color: #E8E6DF;
                border-radius: 12px;
                border: 2px solid #BEB7A3;
            }
            QLabel#BrandTitle {
                font-size: 18px;
                font-weight: bold;
                color: #1A1A18;
                font-family: "Consolas", "Courier New", monospace;
            }
            QLabel#BrandMeta {
                color: #4A4843;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 9px;
                font-weight: bold;
            }
            QLabel#AppTitle {
                color: #1A1A18;
                font-family: "Arial Black", "Arial", sans-serif;
                font-size: 26px;
                font-weight: 900;
                letter-spacing: 1px;
            }
            QLabel#AppSubtitle {
                color: #A33B2F;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 2px;
            }
            QPushButton#SmallBtn {
                background-color: #D0CDBE;
                border: 1px solid #B5B2A5;
                border-radius: 4px;
                color: #2C2B29;
                font-weight: bold;
            }
            QPushButton#SmallBtn:hover { background-color: #B5B2A5; }
            
            QFrame#InputContainer {
                background-color: #E3DECF;
                border-radius: 10px;
                border: 2px solid #8F887A;
            }
            QFrame#TapeFrame {
                background-color: #22201D;
                border-radius: 12px;
                border: 3px solid #111111;
            }
            QLabel#TapeMeta {
                color: #D3CCB7;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 10px;
                font-weight: bold;
            }
            QFrame#TapeNote {
                background-color: #F1E5CC;
                border-radius: 6px;
                border: 2px solid #B7A98C;
            }
            QPlainTextEdit#TapeInput {
                background-color: transparent;
                border: none;
                border-bottom: 2px solid #B22222;
                border-radius: 2px;
                padding: 4px 8px 6px 8px;
                font-family: "Comic Sans MS", "Courier New", monospace;
                font-size: 14px;
                color: #333333;
            }
            QFrame#TapeReel {
                min-width: 64px;
                min-height: 64px;
                max-width: 64px;
                max-height: 64px;
                background-color: #151310;
                border: 4px solid #4A443C;
                border-radius: 32px;
            }
            QLabel#TapeHub {
                min-width: 22px;
                min-height: 22px;
                max-width: 22px;
                max-height: 22px;
                background-color: #D1C8B5;
                border: 4px solid #60594E;
                border-radius: 11px;
            }
            QFrame#TapeBand {
                background-color: #090909;
                border-radius: 6px;
                min-width: 22px;
            }
            QFrame#TapeBandCenter {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0E0E0E, stop:0.3 #1B1713, stop:0.5 #40372F, stop:0.7 #1B1713, stop:1 #0E0E0E);
                border-radius: 6px;
            }
            QFrame#TapeWindow {
                background-color: #171411;
                border: 2px solid #474138;
                border-radius: 10px;
                min-height: 70px;
            }
            QFrame#RecordPanel {
                background-color: transparent;
            }
            QFrame#MeterSeg {
                background-color: #5E6F2D;
                border: 1px solid #49531F;
                border-radius: 1px;
            }
            QFrame#MeterSegOn {
                background-color: #D26B3A;
                border: 1px solid #8F4523;
                border-radius: 1px;
            }
            QLabel#RecLabel {
                color: #B22222;
                font-weight: bold;
                font-size: 18px;
                font-family: "Consolas", "Courier New", monospace;
            }
            QLabel#RecDot {
                color: #D32F2F;
                font-size: 14px;
                font-weight: bold;
            }
            QLabel#RecInfo {
                color: #A9A18C;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 11px;
                font-weight: bold;
                line-height: 1.15em;
                padding-right: 4px;
                padding-top: 4px;
            }
            QLabel#TapeSmallLabel {
                color: #B6D1A4;
                background-color: #274D47;
                border-radius: 4px;
                padding: 6px 8px;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 10px;
                font-weight: bold;
            }
            QLabel#TapeModelLabel {
                color: #E4D6BC;
                background-color: #35625D;
                border-radius: 4px;
                padding: 8px 12px;
                font-family: "Arial Black", "Arial", sans-serif;
                font-size: 22px;
                font-weight: 900;
            }
            QFrame#DeckSlot {
                background-color: #0F0E0D;
                border-radius: 3px;
            }
            QPushButton#RecordBtn {
                background-color: #D32F2F;
                border-radius: 38px;
                border: 4px solid #8B0000;
                color: #FFF6E8;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#RecordBtn:hover { background-color: #FF4500; }
            QPushButton#RecordBtn:pressed { background-color: #8B0000; border: 4px solid #600000; }
            QPushButton#RecordBtn[recording="true"] {
                background-color: #FF1F1F;
                border: 4px solid #FFB000;
                color: #FFFFFF;
            }
            
            QPushButton#ActionBtn, QPushButton#DebugToggleBtn, QPushButton#TransportBtn {
                background-color: #DCD9D0;
                border: 2px solid #B5B2A5;
                border-radius: 8px;
                padding: 8px 10px;
                font-family: "Consolas", "Courier New", monospace;
                font-weight: bold;
                color: #4A4843;
                border-bottom: 4px solid #A3A093;
            }
            QPushButton#ActionBtn:hover, QPushButton#TransportBtn:hover { background-color: #C4C1B3; }
            QPushButton#ActionBtn:pressed, QPushButton#TransportBtn:pressed { 
                background-color: #A3A093; 
                border-bottom: 2px solid #A3A093;
                margin-top: 2px;
            }
            
            QLabel#StatusLed {
                color: #5E5A50;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 10px;
                font-weight: bold;
            }
            
            QFrame#BottomContainer {
                background-color: #E3DECF;
                border-radius: 10px;
                border: 2px solid #8F887A;
            }
            QFrame#DebugPanel {
                background-color: #E3DECF;
                border-radius: 10px;
                border: 2px solid #8F887A;
            }
            QFrame#MusicCardPanel, QFrame#PlayerPanel {
                background-color: transparent;
            }
            QLabel#AvatarPlaceholder {
                background-color: #201D1A;
                color: #8F8D85;
                border-radius: 8px;
                border: 3px solid #6E6556;
            }
            QLabel#MiniTag {
                color: #666666;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 9px;
                margin-top: 5px;
            }
            
            QFrame#LcdScreen {
                background-color: #9EAB88;
                border: 5px solid #2E3027;
                border-radius: 12px;
            }
            QLabel#LcdSmall {
                color: #2A3020;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 9px;
                font-weight: bold;
            }
            QLabel#LcdLarge {
                color: #151810;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 24px;
                font-weight: bold;
                margin-top: 5px;
            }
            QLabel#LcdMedium {
                color: #2A3020;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 11px;
                margin-top: 5px;
            }
            
            QPushButton#FeedbackBtn {
                background-color: #DCD9D0;
                border: 2px solid #B5B2A5;
                border-radius: 8px;
                padding: 9px 10px;
                font-family: "Consolas", "Courier New", monospace;
                font-weight: bold;
                color: #4A4843;
                border-bottom: 4px solid #A3A093;
            }
            QPushButton#FeedbackBtn:hover { background-color: #C4C1B3; }
            QPushButton#FeedbackBtn:pressed { 
                background-color: #A3A093; 
                border-bottom: 2px solid #A3A093;
                margin-top: 2px;
            }
            QPushButton#FeedbackBtn:disabled { background-color: #E8E6DF; color: #A3A093; border-color: #D0CDBE; border-bottom: 2px solid #D0CDBE; margin-top: 2px; }
            QPushButton#DebugFormBtn {
                background-color: #DCD9D0;
                border: 2px solid #B5B2A5;
                border-radius: 8px;
                padding: 10px 12px;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 13px;
                font-weight: bold;
                color: #4A4843;
                border-bottom: 4px solid #A3A093;
            }
            QPushButton#DebugFormBtn:hover { background-color: #C4C1B3; }
            QPushButton#DebugFormBtn:pressed {
                background-color: #A3A093;
                border-bottom: 2px solid #A3A093;
                margin-top: 2px;
            }
            QLabel#Nameplate {
                color: #6B6559;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 9px;
                font-weight: bold;
                padding-top: 2px;
            }
        """)

    def _emit_submit(self) -> None:
        text = self.editor.toPlainText().strip()
        if text:
            self.submit_requested.emit(text, "text")
        else:
            self.show_status("STATUS: NO INPUT")

    def _emit_player_event(self, completion_rate: float, ended_reason: str) -> None:
        self.player_event_requested.emit(self._current_session_id, completion_rate, ended_reason)

    def set_busy(self, busy: bool, message: str = "") -> None:
        has_track = bool(self._current_track_id)
        self.pause_button.setEnabled(has_track)
        self.skip_button.setEnabled(has_track and not busy)
        self.voice_button.setEnabled(not busy)
        self.submit_button.setEnabled(not busy)
        if message:
            self.show_status(message)

    def show_status(self, message: str) -> None:
        self.status_label.setText(f"STATUS: {message.upper()}")

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        if watched is self.editor and event.type() == QEvent.KeyPress:
            key = getattr(event, "key", lambda: None)()
            modifiers = getattr(event, "modifiers", lambda: Qt.NoModifier)()
            if key in (Qt.Key_Return, Qt.Key_Enter) and not (modifiers & Qt.ShiftModifier):
                self._emit_submit()
                return True
        if event.type() == QEvent.MouseButtonPress and hasattr(event, "button"):
            if event.button() == Qt.LeftButton:
                self._drag_active = True
                self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True
        elif event.type() == QEvent.MouseMove and self._drag_active and hasattr(event, "globalPosition"):
            if event.buttons() & Qt.LeftButton:
                self.move(event.globalPosition().toPoint() - self._drag_offset)
                return True
        elif event.type() == QEvent.MouseButtonRelease:
            self._drag_active = False
        return super().eventFilter(watched, event)

    def set_debug_tools_visible(self, visible: bool) -> None:
        self.debug_panel.setVisible(visible)

    def set_transcript(self, text: str) -> None:
        current = self.editor.toPlainText().strip()
        if current:
            self.editor.setPlainText(f"{current}\n{text}")
        else:
            self.editor.setPlainText(text)

    def set_recording(self, is_recording: bool) -> None:
        self.voice_button.setProperty("recording", is_recording)
        self.voice_button.style().unpolish(self.voice_button)
        self.voice_button.style().polish(self.voice_button)
        if is_recording:
            self.voice_button.setText("STOP")
            self.rec_dot.setText("REC")
            self.rec_info.setText("LISTENING\nCTRL+ALT+3 TO STOP")
            self.show_status("RECORDING... SPEAK NOW")
        else:
            self.voice_button.setText("VOICE")
            self.rec_dot.setText("●")
            self.rec_info.setText("AUTO MIC\nNOISE FILTER")
            self.show_status("READY")

    def show_agent_result(self, mapped_result: dict) -> None:
        recommendation = mapped_result.get("recommendation") or {}
        track_title = recommendation.get("title") or "NO TRACK"
        artist = recommendation.get("artist") or ""
        self._current_track_id = recommendation.get("id", "")
        self._current_session_id = mapped_result.get("session_id", "")

        pet_state = mapped_result.get("pet_state", "idle")
        state_label = STATE_LABELS.get(pet_state, "普通")
        self.state_label.setText(f"STATE: {state_label}")
        if artist:
            self.track_label.setText(f"{track_title}\n{artist}")
        else:
            self.track_label.setText(f"{track_title}")
            
        reply = mapped_result.get('assistant_reply', '')
        self.reply_label.setText(reply if reply else "...")

        mode = mapped_result.get("debug_mode", "api")
        if mode == "mock":
            self.show_status("MODE: LOCAL MOCK")
        else:
            self.show_status("MODE: ONLINE")

        has_track = bool(self._current_track_id)
        self.pause_button.setEnabled(has_track)
        self.skip_button.setEnabled(has_track)
            
        import random
        match_score = random.randint(85, 99) if has_track else 0
        if has_track:
            self.match_label.setText(f"♡ EMOTIONAL MATCH             {match_score}%")
        else:
            self.match_label.setText("♡ EMOTIONAL MATCH             --%")

    def sync_player_status(self, status_payload: dict, session_id: str = "") -> None:
        track_id = status_payload.get("track_id", "") or ""
        title = status_payload.get("title", "") or "NO TRACK"
        artist = status_payload.get("artist", "") or ""
        status = status_payload.get("status", "idle")

        self._current_track_id = track_id
        self._current_session_id = session_id if track_id else ""

        if artist:
            self.track_label.setText(f"{title}\n{artist}")
        else:
            self.track_label.setText(title if track_id else "NO TRACK")

        has_track = bool(track_id)
        self.pause_button.setEnabled(has_track)
        self.skip_button.setEnabled(has_track)
        if not has_track and status == "idle":
            self.match_label.setText("♡ EMOTIONAL MATCH             --%")

