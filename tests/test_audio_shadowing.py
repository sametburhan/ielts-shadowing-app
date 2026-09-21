"""
Isolated test script for TTS + Pydub audio segmenting & silence concatenation.
Tests the 'Duy - Durakla - Tekrar Et' (Hear - Pause - Repeat) shadowing audio engine.
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path

# Sample IELTS Band 7 chunks to test
TEST_CHUNKS = [
    {
        "en": "What I appreciate most is its vibrant atmosphere,",
        "tr": "En çok takdir ettiğim şey onun canlı atmosferi,"
    },
    {
        "en": "because it has a great blend of historic charm and modern amenities.",
        "tr": "çünkü tarihi cazibe ve modern olanakların harika bir karışımına sahip."
    },
    {
        "en": "Furthermore, the extensive public transport network makes getting around seamless.",
        "tr": "Dahası, kapsamlı toplu taşıma ağı bir yerden bir yere gitmeyi zahmetsiz kılıyor."
    }
]

async def generate_chunk_tts(text: str, voice: str, output_path: str):
    """Generates audio for a single text chunk using edge-tts."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(output_path)

async def build_shadowing_audio(chunks: list, output_file: str, voice: str = "en-US-JennyNeural", pause_multiplier: float = 1.3):
    """
    Synthesizes each English chunk, calculates duration, adds silence padding (1.3x),
    and concatenates them into a single shadowing audio file.
    """
    import imageio_ffmpeg
    from pydub import AudioSegment

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.environ["PATH"] = os.path.dirname(ffmpeg_exe) + os.pathsep + os.environ.get("PATH", "")
    AudioSegment.converter = ffmpeg_exe
    print(f"[FFmpeg] Using binary from imageio-ffmpeg: {ffmpeg_exe}")

    temp_dir = tempfile.mkdtemp(prefix="ielts_tts_test_")
    print(f"[TempDir] Temporary chunk directory: {temp_dir}")

    combined_audio = AudioSegment.empty()
    chunk_timings = []
    current_time_ms = 0

    print(f"\n--- Starting Shadowing Audio Synthesis (Pause Factor: {pause_multiplier}x) ---")

    for i, item in enumerate(chunks):
        en_text = item["en"]
        tr_text = item["tr"]
        chunk_path = os.path.join(temp_dir, f"chunk_{i}.mp3")

        print(f"\n[Chunk {i+1}/{len(chunks)}]")
        print(f"  EN: {en_text}")
        print(f"  TR: {tr_text}")

        # Step 1: Synthesize chunk TTS
        await generate_chunk_tts(en_text, voice, chunk_path)

        # Step 2: Read chunk with pydub and measure duration
        chunk_audio = AudioSegment.from_file(chunk_path, codec="mp3")
        speech_duration_ms = len(chunk_audio)
        speech_duration_sec = speech_duration_ms / 1000.0

        # Step 3: Calculate silence duration (1.2x - 1.5x, default 1.3x)
        pause_duration_ms = int(speech_duration_ms * pause_multiplier)
        pause_duration_sec = pause_duration_ms / 1000.0

        # Step 4: Create silence segment
        silence_segment = AudioSegment.silent(duration=pause_duration_ms)

        # Step 5: Append chunk + silence
        speech_start_ms = current_time_ms
        speech_end_ms = speech_start_ms + speech_duration_ms
        pause_end_ms = speech_end_ms + pause_duration_ms

        chunk_timings.append({
            "index": i + 1,
            "en": en_text,
            "tr": tr_text,
            "speech_start_ms": speech_start_ms,
            "speech_end_ms": speech_end_ms,
            "pause_end_ms": pause_end_ms,
            "speech_sec": round(speech_duration_sec, 2),
            "pause_sec": round(pause_duration_sec, 2)
        })

        print(f"  Duration: {speech_duration_sec:.2f}s | Repeat Pause: {pause_duration_sec:.2f}s | Total Chunk Window: {(speech_duration_sec + pause_duration_sec):.2f}s")

        combined_audio += chunk_audio + silence_segment
        current_time_ms = pause_end_ms

    # Step 6: Export combined final audio
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    combined_audio.export(output_file, format="mp3")

    total_sec = len(combined_audio) / 1000.0
    print(f"\n[Success] Output exported to: {output_file}")
    print(f"[Stats] Total audio length: {total_sec:.2f} seconds ({int(total_sec // 60):02d}:{int(total_sec % 60):02d})")

    # Clean up temp files
    for f in Path(temp_dir).glob("*.mp3"):
        try:
            f.unlink()
        except Exception:
            pass
    try:
        os.rmdir(temp_dir)
    except Exception:
        pass

    return output_file, chunk_timings

def main():
    output_test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_output.mp3"))
    print(f"Running isolated audio shadowing test...")
    output_path, timings = asyncio.run(build_shadowing_audio(TEST_CHUNKS, output_test_file))
    print(f"\nVerification check:")
    assert os.path.exists(output_path), f"Output file does not exist: {output_path}"
    assert os.path.getsize(output_path) > 10000, f"Output file is suspiciously small: {os.path.getsize(output_path)} bytes"
    print(f"Test passed! Output file size: {os.path.getsize(output_path)} bytes.")
    for t in timings:
        print(f" - [{t['speech_start_ms']}ms -> {t['speech_end_ms']}ms Speech] + [{t['speech_end_ms']}ms -> {t['pause_end_ms']}ms Pause] : {t['en'][:35]}...")

if __name__ == "__main__":
    main()
