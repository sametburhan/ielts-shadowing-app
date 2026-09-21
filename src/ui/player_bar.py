import os
from pathlib import Path
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QSlider, QLabel, QFrame, QComboBox
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class AudioPlayerBar(QFrame):
    """
    Bottom audio player bar matching the wireframe layout.
    Features Play/Pause button on the right, seek progress slider, and duration counters.
    """

    position_changed_ms = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("playerFrame")

        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.85)

        self.current_audio_file = ""
        self.duration_ms = 0
        self.is_slider_pressed = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 10, 16, 10)
        main_layout.setSpacing(16)

        # Left Info & Status
        left_layout = QVBoxLayout()
        left_layout.setSpacing(2)
        self.track_title = QLabel("Ses Dosyası: Bekleniyor...")
        self.track_title.setStyleSheet("font-weight: 600; font-size: 13px; color: #1e293b;")
        self.track_status = QLabel("İçerik üretildikten sonra ses otomatik yüklenecektir.")
        self.track_status.setObjectName("statusBadge")
        left_layout.addWidget(self.track_title)
        left_layout.addWidget(self.track_status)
        main_layout.addLayout(left_layout, stretch=1)

        # Center Seeker & Time
        center_layout = QVBoxLayout()
        center_layout.setSpacing(4)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)

        time_layout = QHBoxLayout()
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("timeLabel")

        # Playback speed selector
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.8x Hız", "1.0x Normal", "1.2x Hızlı"])
        self.speed_combo.setCurrentIndex(1)
        self.speed_combo.setToolTip("Oynatma Hızı")
        self.speed_combo.currentIndexChanged.connect(self._on_speed_changed)

        time_layout.addWidget(self.time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.speed_combo)

        center_layout.addWidget(self.slider)
        center_layout.addLayout(time_layout)
        main_layout.addLayout(center_layout, stretch=3)

        # Right: Prominent Play/Pause Button
        self.play_btn = QPushButton("▶")
        self.play_btn.setObjectName("playPauseBtn")
        self.play_btn.setEnabled(False)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setToolTip("Oynat / Duraklat (Space)")
        main_layout.addWidget(self.play_btn)

    def _connect_signals(self):
        self.play_btn.clicked.connect(self.toggle_play_pause)
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_state_changed)

        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderReleased.connect(self._on_slider_released)
        self.slider.sliderMoved.connect(self._on_slider_moved)

    def load_audio(self, audio_path: str, title: str = "IELTS Shadowing Audio"):
        """Loads an audio file and prepares player."""
        if not os.path.exists(audio_path):
            self.track_status.setText("Hata: Ses dosyası bulunamadı.")
            return

        self.current_audio_file = audio_path
        self.media_player.stop()
        self.media_player.setSource(QUrl.fromLocalFile(audio_path))

        self.track_title.setText(f"🎧 {title}")
        self.track_status.setText("Hazır! Dinle ve duraklamalarda tekrar et.")
        self.play_btn.setEnabled(True)
        self.play_btn.setText("▶")

    def toggle_play_pause(self):
        """Toggles between play and pause."""
        state = self.media_player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def _on_state_changed(self, state: QMediaPlayer.PlaybackState):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setText("⏸")
            self.track_status.setText("Oynatılıyor (Duy - Durakla - Tekrar Et)...")
        else:
            self.play_btn.setText("▶")
            if self.duration_ms > 0 and self.media_player.position() >= self.duration_ms:
                self.track_status.setText("Tamamlandı. Tekrar dinlemek için oynatın.")
            else:
                self.track_status.setText("Duraklatıldı.")

    def _on_duration_changed(self, duration_ms: int):
        self.duration_ms = duration_ms
        self.slider.setRange(0, duration_ms)
        self._update_time_label(self.media_player.position(), duration_ms)

    def _on_position_changed(self, position_ms: int):
        if not self.is_slider_pressed:
            self.slider.setValue(position_ms)
        self._update_time_label(position_ms, self.duration_ms)
        self.position_changed_ms.emit(position_ms)

    def _on_slider_pressed(self):
        self.is_slider_pressed = True

    def _on_slider_released(self):
        self.is_slider_pressed = False
        self.media_player.setPosition(self.slider.value())

    def _on_slider_moved(self, pos: int):
        self._update_time_label(pos, self.duration_ms)

    def _on_speed_changed(self, index: int):
        rates = [0.8, 1.0, 1.2]
        if 0 <= index < len(rates):
            self.media_player.setPlaybackRate(rates[index])

    def _update_time_label(self, current_ms: int, total_ms: int):
        curr_sec = max(0, current_ms // 1000)
        tot_sec = max(0, total_ms // 1000)
        curr_str = f"{curr_sec // 60:02d}:{curr_sec % 60:02d}"
        tot_str = f"{tot_sec // 60:02d}:{tot_sec % 60:02d}"
        self.time_label.setText(f"{curr_str} / {tot_str}")
