import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Base paths (supports both normal python and PyInstaller executable)
if getattr(sys, 'frozen', False):
    PROJECT_ROOT = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, '_MEIPASS', PROJECT_ROOT))
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    BUNDLE_DIR = PROJECT_ROOT

# System AppData Directories (Windows standard locations)
APP_DIR_NAME = "IELTS_Shadowing_Assistant"

# Roaming AppData for User Settings (persists across runs/updates, outside project folder)
ROAMING_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / APP_DIR_NAME
ROAMING_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = ROAMING_DIR / "config.json"

# Local AppData for Audio Cache (cleared/managed by OS or app, outside project folder)
LOCAL_DIR = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_DIR_NAME
CACHE_DIR = LOCAL_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Assets (Bundled with application/executable)
ASSETS_DIR = BUNDLE_DIR / "assets"
if not ASSETS_DIR.exists():
    ASSETS_DIR = PROJECT_ROOT / "assets"

LOGO_PATH = ASSETS_DIR / "logo.png"
LOGO_ICO_PATH = ASSETS_DIR / "logo.ico"

# Load existing .env if present (check roaming first, then project root)
if (ROAMING_DIR / ".env").exists():
    load_dotenv(ROAMING_DIR / ".env")
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_CONFIG = {
    "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
    "gemini_model": "gemini-2.5-flash",
    "voice": "en-GB-SoniaNeural",  # British accent ideal for IELTS
    "pause_multiplier": 1.3,        # Silence = chunk_duration * pause_multiplier
    "band_level": "7.5+",          # IELTS target band: "1-4", "4.5-5.5", "6-7", "7.5+"
    "volume": 80
}

AVAILABLE_BAND_LEVELS = {
    "Band 1 - 4 (Temel)": "1-4",
    "Band 4.5 - 5.5 (Orta)": "4.5-5.5",
    "Band 6.0 - 7.0 (İleri)": "6-7",
    "Band 7.5+ (Uzman)": "7.5+"
}

AVAILABLE_VOICES = {
    "British (Female) - Sonia": "en-GB-SoniaNeural",
    "British (Male) - Ryan": "en-GB-RyanNeural",
    "American (Female) - Jenny": "en-US-JennyNeural",
    "American (Male) - Guy": "en-US-GuyNeural",
    "Australian (Female) - Natasha": "en-AU-NatashaNeural"
}

def load_config() -> dict:
    """Loads configuration from JSON file with environment and default fallbacks."""
    # If AppData config does not exist yet, check if one exists in project root and migrate it
    if not CONFIG_FILE.exists():
        legacy_config = PROJECT_ROOT / "config.json"
        if legacy_config.exists():
            try:
                import shutil
                shutil.copy2(legacy_config, CONFIG_FILE)
            except Exception as e:
                print(f"Notice: Could not migrate legacy config: {e}")

    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception as e:
            print(f"Warning: Could not read config file: {e}")

    # Env var takes precedence if saved key is empty
    if not config.get("gemini_api_key"):
        config["gemini_api_key"] = os.getenv("GEMINI_API_KEY", "")

    return config

def save_config(updates: dict) -> dict:
    """Saves updated configuration to JSON file."""
    config = load_config()
    config.update(updates)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config file: {e}")
    return config
