import os
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTabBar, QLabel,
    QMessageBox, QFrame, QComboBox, QCheckBox
)
from PyQt6.QtGui import QIcon, QPixmap

from src.config import (
    load_config, save_config, AVAILABLE_VOICES,
    AVAILABLE_BAND_LEVELS, CACHE_DIR, LOGO_PATH, LOGO_ICO_PATH
)
from src.llm.prompts import get_random_topic
from src.ui.styles import MAIN_STYLESHEET
from src.ui.script_viewer import ScriptViewer
from src.ui.player_bar import AudioPlayerBar
from src.workers.pipeline_worker import GenerationWorker

class MainWindow(QMainWindow):
    """
    Main Application Window for IELTS Speaking Shadowing Assistant.
    Follows wireframe structure: Topic Input Bar -> Part 1/2/3 Tabs -> Script Viewer -> Audio Bar.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("IELTS Speaking Shadowing Assistant (Duy - Durakla - Tekrar Et)")
        self.resize(960, 780)
        self.setMinimumSize(850, 650)

        # Set window icon (prefer multi-res ICO on Windows)
        if LOGO_ICO_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_ICO_PATH)))
        elif LOGO_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_PATH)))

        # Load persisted settings
        self.config = load_config()

        # State per part {1: {"content": ..., "audio": ..., "timings": ...}, 2: ..., 3: ...}
        self.part_data = {1: None, 2: None, 3: None}
        self.current_worker: GenerationWorker = None

        self._setup_ui()
        self._apply_styles()
        self._check_api_key_initial()

    def _setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)

        # -----------------------------------------------------------------
        # 1. TOP BAR: Topic Input & Generation Controls
        # -----------------------------------------------------------------
        top_frame = QFrame()
        top_frame.setObjectName("topBarFrame")
        top_layout = QVBoxLayout(top_frame)
        top_layout.setContentsMargins(12, 10, 12, 10)
        top_layout.setSpacing(8)

        # Topic input row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        if LOGO_PATH.exists():
            self.logo_label = QLabel()
            pix = QPixmap(str(LOGO_PATH)).scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pix)
            self.logo_label.setToolTip("IELTS Speaking Shadowing Assistant")
            input_row.addWidget(self.logo_label)

        self.topic_input = QLineEdit()
        self.topic_input.setObjectName("topicInput")
        self.topic_input.setPlaceholderText("random konu girdisi (örn: Public Transport, Artificial Intelligence, Memorable Trip...)")
        self.topic_input.returnPressed.connect(self.on_generate_clicked)

        self.random_btn = QPushButton("🎲 Rastgele Konu")
        self.random_btn.setObjectName("btnSecondary")
        self.random_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.random_btn.clicked.connect(self.on_random_topic_clicked)

        self.generate_btn = QPushButton("✨ Generate (İçerik & Ses Üret)")
        self.generate_btn.setObjectName("btnGenerate")
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_btn.clicked.connect(self.on_generate_clicked)

        input_row.addWidget(self.topic_input, stretch=3)
        input_row.addWidget(self.random_btn)
        input_row.addWidget(self.generate_btn)
        top_layout.addLayout(input_row)

        # Configuration & API Key sub-row
        settings_row = QHBoxLayout()
        settings_row.setSpacing(10)

        # API Key Field
        key_label = QLabel("Gemini Key:")
        key_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b;")
        self.api_key_input = QLineEdit()
        self.api_key_input.setObjectName("apiKeyInput")
        self.api_key_input.setPlaceholderText("AIzaSy...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setText(self.config.get("gemini_api_key", ""))
        self.api_key_input.setFixedWidth(210)

        self.show_key_check = QCheckBox("Göster")
        self.show_key_check.setStyleSheet("font-size: 11px; color: #64748b;")
        self.show_key_check.toggled.connect(self._toggle_key_visibility)

        self.save_key_btn = QPushButton("Kaydet")
        self.save_key_btn.setObjectName("saveKeyBtn")
        self.save_key_btn.setFixedHeight(28)
        self.save_key_btn.setMinimumWidth(68)
        self.save_key_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_key_btn.clicked.connect(self._save_api_key)

        # Voice Selector
        voice_label = QLabel("Aksan / Ses:")
        voice_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; margin-left: 10px;")
        self.voice_combo = QComboBox()
        for label, val in AVAILABLE_VOICES.items():
            self.voice_combo.addItem(label, val)
        # Select saved voice
        saved_voice = self.config.get("voice", "en-GB-SoniaNeural")
        idx = self.voice_combo.findData(saved_voice)
        if idx >= 0:
            self.voice_combo.setCurrentIndex(idx)
        self.voice_combo.currentIndexChanged.connect(self._on_voice_changed)

        # Pause Ratio Selector
        pause_label = QLabel("Tekrar Duraklaması:")
        pause_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; margin-left: 10px;")
        self.pause_combo = QComboBox()
        self.pause_combo.addItem("1.2x (Hızlı)", 1.2)
        self.pause_combo.addItem("1.3x (Önerilen)", 1.3)
        self.pause_combo.addItem("1.5x (Rahat)", 1.5)
        self.pause_combo.setCurrentIndex(1)
        self.pause_combo.currentIndexChanged.connect(self._on_pause_changed)

        # Band Level Selector
        band_label = QLabel("Hedef Band:")
        band_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; margin-left: 10px;")
        self.band_combo = QComboBox()
        for label, val in AVAILABLE_BAND_LEVELS.items():
            self.band_combo.addItem(label, val)
        saved_band = self.config.get("band_level", "7.5+")
        idx_b = self.band_combo.findData(saved_band)
        if idx_b >= 0:
            self.band_combo.setCurrentIndex(idx_b)
        self.band_combo.currentIndexChanged.connect(self._on_band_changed)

        settings_row.addWidget(key_label)
        settings_row.addWidget(self.api_key_input)
        settings_row.addWidget(self.show_key_check)
        settings_row.addWidget(self.save_key_btn)
        settings_row.addWidget(voice_label)
        settings_row.addWidget(self.voice_combo)
        settings_row.addWidget(pause_label)
        settings_row.addWidget(self.pause_combo)
        settings_row.addWidget(band_label)
        settings_row.addWidget(self.band_combo)
        settings_row.addStretch()

        top_layout.addLayout(settings_row)
        main_layout.addWidget(top_frame)

        # -----------------------------------------------------------------
        # 2. IELTS PART TABS (Part 1, Part 2, Part 3)
        # -----------------------------------------------------------------
        self.tab_bar = QTabBar()
        self.tab_bar.setDrawBase(False)
        self.tab_bar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tab_bar.addTab("Part 1 (Interview)")
        self.tab_bar.addTab("Part 2 (Cue Card)")
        self.tab_bar.addTab("Part 3 (Discussion)")
        self.tab_bar.currentChanged.connect(self._on_tab_changed)

        # -----------------------------------------------------------------
        # 3. MIDDLE AREA: Script Viewer ("konuşma scripti")
        # -----------------------------------------------------------------
        self.script_viewer = ScriptViewer()

        # Combine Tab bar and script viewer into a cohesive view without extra gap
        tab_container = QVBoxLayout()
        tab_container.setSpacing(0)
        tab_container.setContentsMargins(0, 0, 0, 0)
        tab_container.addWidget(self.tab_bar)
        tab_container.addWidget(self.script_viewer, stretch=1)

        main_layout.addLayout(tab_container, stretch=1)

        # -----------------------------------------------------------------
        # 4. BOTTOM BAR: Audio Player ("ses dosyası")
        # -----------------------------------------------------------------
        self.player_bar = AudioPlayerBar()
        self.player_bar.position_changed_ms.connect(self.script_viewer.update_playback_position)
        main_layout.addWidget(self.player_bar)

        # -----------------------------------------------------------------
        # Status Bar
        # -----------------------------------------------------------------
        self.statusBar().showMessage("Hazır. Başlamak için bir konu belirleyin ve 'Generate' butonuna tıklayın.")

    def _apply_styles(self):
        self.setStyleSheet(MAIN_STYLESHEET)

    def _check_api_key_initial(self):
        if not self.config.get("gemini_api_key"):
            self.statusBar().showMessage("ℹ️ Lütfen üst alana Gemini API anahtarınızı girip 'Kaydet'e basınız.")

    def _toggle_key_visibility(self, checked: bool):
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)

    def _save_api_key(self):
        key = self.api_key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Uyarı", "Lütfen geçerli bir Gemini API anahtarı giriniz.")
            return
        self.config = save_config({"gemini_api_key": key})
        self.save_key_btn.setText("✓ Kaydedildi")
        QTimer.singleShot(1500, lambda: self.save_key_btn.setText("Kaydet"))
        self.statusBar().showMessage("Gemini API anahtarı başarıyla kaydedildi.", 3000)

    def _on_voice_changed(self):
        selected_voice = self.voice_combo.currentData()
        self.config = save_config({"voice": selected_voice})

    def _on_pause_changed(self):
        selected_ratio = self.pause_combo.currentData()
        self.config = save_config({"pause_multiplier": selected_ratio})

    def _on_band_changed(self):
        selected_band = self.band_combo.currentData()
        self.config = save_config({"band_level": selected_band})

    def on_random_topic_clicked(self):
        topic = get_random_topic()
        self.topic_input.setText(topic)
        self.statusBar().showMessage(f"🎲 Rastgele konu seçildi: '{topic}'", 3000)

    def get_current_part(self) -> int:
        return self.tab_bar.currentIndex() + 1

    def _on_tab_changed(self, index: int):
        part = index + 1
        data = self.part_data.get(part)
        if data and data.get("content"):
            self.script_viewer.set_content(data["content"])
            if data.get("timings"):
                self.script_viewer.set_timings(data["timings"])
            if data.get("audio_file"):
                self.player_bar.load_audio(data["audio_file"], f"IELTS Part {part} - {data['content'].get('topic')}")
        else:
            self.script_viewer.show_placeholder()
            self.player_bar.track_title.setText(f"Part {part}: Henüz içerik üretilmedi")
            self.player_bar.track_status.setText("Bu bölüm için 'Generate' butonuna basarak içerik oluşturabilirsiniz.")
            self.player_bar.play_btn.setEnabled(False)

    def on_generate_clicked(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(
                self,
                "API Anahtarı Gerekli",
                "Lütfen yukarıdaki 'Gemini Key' alanına geçerli bir Google Gemini API anahtarı girip 'Kaydet'e basınız.\n\n"
                "Ücretsiz anahtar almak için: https://aistudio.google.com"
            )
            self.api_key_input.setFocus()
            return

        topic = self.topic_input.text().strip()
        if not topic:
            topic = get_random_topic()
            self.topic_input.setText(topic)

        part = self.get_current_part()
        voice = self.voice_combo.currentData()
        pause_multiplier = self.pause_combo.currentData()
        band_level = self.band_combo.currentData()

        # Disable generate button while running
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("⏳ Hazırlanıyor...")
        self.statusBar().showMessage(f"Part {part} ({band_level}) için içerik ve ses hazırlanıyor...")

        # Stop existing audio if playing
        self.player_bar.media_player.stop()

        # Start QThread worker
        self.current_worker = GenerationWorker(
            topic=topic,
            part=part,
            api_key=api_key,
            voice=voice,
            pause_multiplier=pause_multiplier,
            band_level=band_level,
            output_dir=CACHE_DIR
        )

        self.current_worker.stage_changed.connect(self._on_worker_stage)
        self.current_worker.progress_updated.connect(self._on_worker_progress)
        self.current_worker.content_generated.connect(self._on_content_generated)
        self.current_worker.audio_generated.connect(self._on_audio_generated)
        self.current_worker.error_occurred.connect(self._on_worker_error)
        self.current_worker.pipeline_finished.connect(self._on_worker_finished)

        self.current_worker.start()

    def _on_worker_stage(self, stage_msg: str):
        self.statusBar().showMessage(stage_msg)
        self.player_bar.track_status.setText(stage_msg)

    def _on_worker_progress(self, current: int, total: int, msg: str):
        self.statusBar().showMessage(msg)
        self.player_bar.track_status.setText(msg)

    def _on_content_generated(self, content_data: dict):
        part = self.get_current_part()
        if not self.part_data.get(part):
            self.part_data[part] = {}
        self.part_data[part]["content"] = content_data
        self.script_viewer.set_content(content_data)

    def _on_audio_generated(self, audio_file: str, audio_meta: dict):
        part = self.get_current_part()
        if not self.part_data.get(part):
            self.part_data[part] = {}
        self.part_data[part]["audio_file"] = audio_file
        self.part_data[part]["timings"] = audio_meta.get("timings", [])

        self.script_viewer.set_timings(audio_meta.get("timings", []))
        topic = self.part_data[part]["content"].get("topic", "")
        self.player_bar.load_audio(audio_file, f"Part {part} Shadowing: {topic}")

    def _on_worker_error(self, error_msg: str):
        QMessageBox.critical(self, "Hata Oluştu", f"İşlem sırasında bir hata oluştu:\n\n{error_msg}")
        self.statusBar().showMessage(f"Hata: {error_msg}")
        self.player_bar.track_status.setText("Hata nedeniyle işlem durduruldu.")

    def _on_worker_finished(self):
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("✨ Generate (İçerik & Ses Üret)")
