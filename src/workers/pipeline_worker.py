import os
import asyncio
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from src.llm.gemini_client import GeminiClient
from src.audio.shadow_engine import ShadowAudioEngine

class GenerationWorker(QThread):
    """
    Background worker thread that runs the LLM generation followed by
    the Hear-Pause-Repeat audio processing pipeline without freezing the PyQt6 UI.
    """

    stage_changed = pyqtSignal(str)
    progress_updated = pyqtSignal(int, int, str)
    content_generated = pyqtSignal(dict)
    audio_generated = pyqtSignal(str, dict)
    error_occurred = pyqtSignal(str)
    pipeline_finished = pyqtSignal()

    def __init__(
        self,
        topic: str,
        part: int,
        api_key: str,
        voice: str,
        pause_multiplier: float,
        band_level: str,
        output_dir: Path
    ):
        super().__init__()
        self.topic = topic
        self.part = part
        self.api_key = api_key
        self.voice = voice
        self.pause_multiplier = pause_multiplier
        self.band_level = band_level
        self.output_dir = output_dir
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            # Step 1: LLM Content Generation
            self.stage_changed.emit(f"Gemini LLM ile Part {self.part} ({self.band_level}) için içerik üretiliyor...")

            client = GeminiClient(api_key=self.api_key)
            content_data = client.generate_ielts_content(
                topic=self.topic,
                part=self.part,
                band_level=self.band_level
            )

            if self._is_cancelled:
                return

            # Emit parsed content immediately so the user can read while audio compiles
            self.content_generated.emit(content_data)

            # Step 2: Hear-Pause-Repeat Audio Processing
            self.stage_changed.emit("Duy-Durakla-Tekrar Et ses dosyası hazırlanıyor...")
            chunks = content_data.get("chunks", [])
            if not chunks:
                raise ValueError("Üretilen içerikte seslendirilecek parça bulunamadı.")

            output_file = self.output_dir / f"final_shadowing_part{self.part}.mp3"

            engine = ShadowAudioEngine(
                voice=self.voice,
                pause_multiplier=self.pause_multiplier
            )

            def on_progress(cur, total, msg):
                self.progress_updated.emit(cur, total, msg)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                audio_result = loop.run_until_complete(
                    engine.build_shadowing_audio(
                        chunks=chunks,
                        output_file=str(output_file),
                        voice=self.voice,
                        pause_multiplier=self.pause_multiplier,
                        progress_callback=on_progress,
                        is_cancelled=lambda: self._is_cancelled
                    )
                )
            finally:
                loop.close()

            if self._is_cancelled:
                return

            self.stage_changed.emit("Ses hazır! Gölgeleme pratiğine başlayabilirsiniz.")
            self.audio_generated.emit(str(output_file), audio_result)

        except Exception as e:
            if not self._is_cancelled:
                self.error_occurred.emit(str(e))
        finally:
            self.pipeline_finished.emit()
