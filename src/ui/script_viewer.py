from typing import Optional, Dict, Any, List
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser,
    QLabel, QPushButton, QFrame, QApplication
)
from src.config import LOGO_PATH
from src.ui.styles import generate_script_html

class ScriptViewer(QFrame):
    """
    Middle area displaying the IELTS Question & bilingual shadow script chunks.
    Matches the 'konuşma scripti' area from the wireframe.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("scriptContainer")

        self.content_data: Optional[Dict[str, Any]] = None
        self.chunk_timings: List[Dict[str, Any]] = []
        self.active_chunk_idx: int = -1

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)

        # Header toolbar inside the script container
        header_layout = QHBoxLayout()
        self.title_label = QLabel("📝 Konuşma Scripti (Duy - Durakla - Tekrar Et)")
        self.title_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #065f46;")

        self.copy_btn = QPushButton("Metni Kopyala")
        self.copy_btn.setObjectName("btnSecondary")
        self.copy_btn.setFixedHeight(28)
        self.copy_btn.clicked.connect(self._copy_to_clipboard)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.copy_btn)

        layout.addLayout(header_layout)

        # Text browser for rich formatted bilingual content
        self.browser = QTextBrowser()
        self.browser.setObjectName("scriptBrowser")
        self.browser.setOpenExternalLinks(True)

        layout.addWidget(self.browser)

        self.show_placeholder()

    def show_placeholder(self):
        """Displays welcome and instructions when no content is generated yet."""
        self.content_data = None
        self.chunk_timings = []
        self.active_chunk_idx = -1

        logo_tag = f'<img src="{LOGO_PATH.as_uri()}" width="88" height="88" style="border-radius: 12px; margin-bottom: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">' if LOGO_PATH.exists() else '<div style="font-size: 38px; margin-bottom: 12px;">🎙️</div>'

        placeholder_html = f"""
        <div style="text-align: center; padding: 40px 20px; color: #64748b;">
            {logo_tag}
            <h2 style="color: #0f172a; margin-bottom: 8px;">IELTS Speaking Shadowing Pratiğine Hoş Geldiniz</h2>
            <p style="font-size: 14px; max-width: 520px; margin: 0 auto 16px auto; line-height: 1.5;">
                Yukarıdaki çubuğa pratik yapmak istediğiniz konuyu yazın (veya boş bırakıp rastgele konu seçin),
                IELTS Part 1, 2 veya 3 sekmesini seçin ve <strong>Generate</strong> butonuna basın.
            </p>
            <div style="background-color: #ffffff; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 14px; max-width: 480px; margin: 0 auto; text-align: left; font-size: 13px;">
                <strong style="color: #059669;">💡 Duy-Durakla-Tekrar Et (Shadowing) Nasıl Çalışır?</strong><br>
                1. Sistem her İngilizce cümleyi doğal telaffuz ile seslendirir.<br>
                2. Cümlenin ardından <strong>sesin süresi kadar sessizlik</strong> eklenir.<br>
                3. Bu sessizlik esnasında cümleyi yüksek sesle ve aynı tonlamayla siz tekrar edersiniz.
            </div>
        </div>
        """
        self.browser.setHtml(placeholder_html)

    def set_content(self, content_data: Dict[str, Any]):
        """Sets the parsed IELTS script data and displays it."""
        self.content_data = content_data
        self.active_chunk_idx = -1
        html = generate_script_html(content_data, active_chunk_idx=-1)
        self.browser.setHtml(html)

    def set_timings(self, timings: List[Dict[str, Any]]):
        """Sets the timing coordinates for chunk synchronization."""
        self.chunk_timings = timings

    def update_playback_position(self, position_ms: int):
        """Highlights the active chunk based on playback time."""
        if not self.chunk_timings or not self.content_data:
            return

        current_idx = -1
        for idx, timing in enumerate(self.chunk_timings):
            if timing["speech_start_ms"] <= position_ms <= timing["pause_end_ms"]:
                current_idx = idx
                break

        if current_idx != self.active_chunk_idx:
            self.active_chunk_idx = current_idx
            # Preserve scroll position if possible
            scroll_bar = self.browser.verticalScrollBar()
            scroll_pos = scroll_bar.value()
            html = generate_script_html(self.content_data, active_chunk_idx=self.active_chunk_idx)
            self.browser.setHtml(html)
            scroll_bar.setValue(scroll_pos)

    def _copy_to_clipboard(self):
        """Copies plain text script to clipboard."""
        if not self.content_data:
            return

        lines = []
        lines.append(f"Topic: {self.content_data.get('topic', '')}")
        lines.append(f"Question: {self.content_data.get('question', '')}\n")

        for idx, chunk in enumerate(self.content_data.get("chunks", [])):
            lines.append(f"[{idx + 1}] {chunk.get('en', '')}")
            lines.append(f"    {chunk.get('tr', '')}\n")

        full_text = "\n".join(lines)
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(full_text)
            self.copy_btn.setText("✓ Kopyalandı!")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self.copy_btn.setText("Metni Kopyala"))
