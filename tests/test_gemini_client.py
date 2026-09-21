import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.llm.gemini_client import GeminiClient
from src.llm.prompts import get_ielts_prompt, get_random_topic

def test_random_topic():
    topic = get_random_topic()
    assert isinstance(topic, str) and len(topic) > 0

def test_prompt_generation():
    p1 = get_ielts_prompt("Technology", 1, band_level="1-4")
    assert "Part 1" in p1
    assert "Technology" in p1
    assert "1.0 - 4.0" in p1

    p2 = get_ielts_prompt("A Memorable Journey", 2, band_level="4.5-5.5")
    assert "Part 2" in p2
    assert "Cue Card" in p2
    assert "4.5 - 5.5" in p2

    p3 = get_ielts_prompt("Artificial Intelligence", 3, band_level="7.5+")
    assert "Part 3" in p3
    assert "Discussion" in p3
    assert "7.5+" in p3

def test_json_parsing_clean():
    client = GeminiClient(api_key="test")
    raw = '{"topic": "Transport", "part": 1, "question": "Q?", "chunks": [{"en": "Hello", "tr": "Merhaba"}]}'
    data = client._parse_json_response(raw)
    assert data["topic"] == "Transport"
    assert len(data["chunks"]) == 1

def test_json_parsing_markdown_wrapped():
    client = GeminiClient(api_key="test")
    raw = '```json\n{"topic": "Transport", "part": 1, "question": "Q?", "chunks": [{"en": "Hello", "tr": "Merhaba"}]}\n```'
    data = client._parse_json_response(raw)
    assert data["topic"] == "Transport"
    assert data["chunks"][0]["en"] == "Hello"

def test_validate_ielts_json():
    client = GeminiClient(api_key="test")
    valid_data = {
        "topic": "Transport",
        "question": "Do you like buses?",
        "chunks": [
            {"en": "Yes, they are convenient.", "tr": "Evet, çok elverişliler."}
        ]
    }
    client._validate_ielts_json(valid_data, expected_part=1)
    assert valid_data["part"] == 1
    assert len(valid_data["chunks"]) == 1

if __name__ == "__main__":
    test_random_topic()
    test_prompt_generation()
    test_json_parsing_clean()
    test_json_parsing_markdown_wrapped()
    test_validate_ielts_json()
    print("All Gemini client tests passed successfully!")
