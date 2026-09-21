import os
import sys
import asyncio
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional

class ShadowAudioEngine:
    """
    Core 'Hear - Pause - Repeat' audio generation engine.
    Uses edge-tts to synthesize individual chunks, pydub to measure duration,
    appends proportionate silence (1.2x - 1.5x), and concatenates into final_shadowing.mp3.
    """

    def __init__(self, voice: str = "en-GB-SoniaNeural", pause_multiplier: float = 1.3):
        self.voice = voice
        self.pause_multiplier = max(1.0, min(2.5, pause_multiplier))
        self._setup_ffmpeg()

    def _setup_ffmpeg(self):
        """Configures pydub to use the bundled imageio-ffmpeg binary."""
        try:
            import imageio_ffmpeg
            from pydub import AudioSegment
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ.get("PATH", "")
            AudioSegment.converter = ffmpeg_path
        except Exception as e:
            print(f"[ShadowAudioEngine] Warning configuring imageio-ffmpeg: {e}")

    async def _synthesize_single_chunk(self, text: str, voice: str, out_path: str):
        """Generates audio for a single chunk using edge-tts."""
        import edge_tts
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(out_path)

    async def build_shadowing_audio(
        self,
        chunks: List[Dict[str, str]],
        output_file: str,
        voice: Optional[str] = None,
        pause_multiplier: Optional[float] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None
    ) -> Dict[str, Any]:
        """
        Processes chunks, generates individual TTS files, calculates silence durations,
        concatenates them, and outputs final MP3 with precise timing coordinates.
        """
        import imageio_ffmpeg
        from pydub import AudioSegment

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        os.environ["PATH"] = os.path.dirname(ffmpeg_exe) + os.pathsep + os.environ.get("PATH", "")
        AudioSegment.converter = ffmpeg_exe

        active_voice = voice or self.voice
        active_multiplier = pause_multiplier if pause_multiplier is not None else self.pause_multiplier

        temp_dir = tempfile.mkdtemp(prefix="ielts_shadow_")
        combined_audio = AudioSegment.empty()
        timings = []
        current_time_ms = 0

        total_chunks = len(chunks)

        try:
            for idx, chunk in enumerate(chunks):
                if is_cancelled and is_cancelled():
                    raise RuntimeError("Kullanıcı tarafından iptal edildi.")

                en_text = chunk.get("en", "").strip()
                tr_text = chunk.get("tr", "").strip()

                if progress_callback:
                    progress_callback(idx + 1, total_chunks, f"Seslendiriliyor ({idx + 1}/{total_chunks}): '{en_text[:30]}...'")

                chunk_file = os.path.join(temp_dir, f"chunk_{idx}.mp3")

                # Synthesize chunk with edge-tts
                await self._synthesize_single_chunk(en_text, active_voice, chunk_file)

                # Load chunk and measure duration
                chunk_audio = AudioSegment.from_file(chunk_file, codec="mp3")
                speech_dur_ms = len(chunk_audio)

                # Calculate user repetition silence (1.2x to 1.5x)
                silence_dur_ms = int(speech_dur_ms * active_multiplier)
                silence_segment = AudioSegment.silent(duration=silence_dur_ms)

                # Record exact timestamps for UI highlighting
                speech_start = current_time_ms
                speech_end = speech_start + speech_dur_ms
                pause_end = speech_end + silence_dur_ms

                timings.append({
                    "index": idx,
                    "en": en_text,
                    "tr": tr_text,
                    "speech_start_ms": speech_start,
                    "speech_end_ms": speech_end,
                    "pause_end_ms": pause_end,
                    "speech_sec": round(speech_dur_ms / 1000.0, 2),
                    "pause_sec": round(silence_dur_ms / 1000.0, 2)
                })

                # Concatenate: Speech Chunk + Silence
                combined_audio += chunk_audio + silence_segment
                current_time_ms = pause_end

            if progress_callback:
                progress_callback(total_chunks, total_chunks, "Ses dosyası birleştiriliyor ve kaydediliyor...")

            # Export final combined MP3
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            combined_audio.export(output_file, format="mp3", bitrate="192k")

            total_duration_ms = len(combined_audio)

            return {
                "output_file": os.path.abspath(output_file),
                "total_duration_ms": total_duration_ms,
                "total_duration_sec": total_duration_ms / 1000.0,
                "timings": timings,
                "voice": active_voice,
                "pause_multiplier": active_multiplier
            }

        finally:
            # Clean up temporary chunk files
            for f in Path(temp_dir).glob("*.mp3"):
                try:
                    f.unlink()
                except Exception:
                    pass
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass
