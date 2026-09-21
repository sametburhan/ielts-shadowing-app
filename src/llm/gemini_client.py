import os
import json
import re
from typing import Dict, Any, Optional
from src.llm.prompts import get_system_prompt, get_ielts_prompt

class GeminiClient:
    """Client for interacting with Google Gemini LLM to generate IELTS content."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name

    def set_api_key(self, api_key: str):
        """Updates the active API key."""
        self.api_key = api_key.strip()

    def generate_ielts_content(self, topic: str, part: int = 1, band_level: str = "7.5+") -> Dict[str, Any]:
        """
        Calls Gemini API with IELTS prompt and parses structured JSON response.
        Raises ValueError with clear message if API key is missing or response is invalid.
        """
        if not self.api_key:
            raise ValueError(
                "Gemini API Key bulunamadı! Lütfen üst kısımdaki API anahtarı alanına Gemini API anahtarınızı girin."
            )

        system_instruction = get_system_prompt(band_level=band_level)
        user_prompt = get_ielts_prompt(topic, part, band_level=band_level)

        raw_response = self._call_gemini(system_instruction, user_prompt)
        parsed_json = self._parse_json_response(raw_response)
        self._validate_ielts_json(parsed_json, part)
        return parsed_json

    def _call_gemini(self, system_instruction: str, user_prompt: str) -> str:
        """Invokes Gemini using either google.genai (new) or google.generativeai (fallback)."""
        # Try new google.genai SDK first
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                response_mime_type="application/json"
            )
            response = client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=config
            )
            if response.text:
                return response.text
        except ImportError:
            pass
        except Exception as e:
            # If the specific model failed, retry with gemini-1.5-flash
            if "not found" in str(e).lower() or "404" in str(e):
                try:
                    from google import genai
                    from google.genai import types
                    client = genai.Client(api_key=self.api_key)
                    config = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7,
                        response_mime_type="application/json"
                    )
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=user_prompt,
                        config=config
                    )
                    if response.text:
                        return response.text
                except Exception:
                    pass
            # Fall through to legacy SDK or re-raise
            last_err = e

        # Try google.generativeai SDK as fallback
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system_instruction,
                generation_config={"response_mime_type": "application/json", "temperature": 0.7}
            )
            response = model.generate_content(user_prompt)
            if response.text:
                return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API çağrısı başarısız oldu: {str(e)}")

        raise RuntimeError("Gemini API'den boş yanıt alındı.")

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Cleans markdown wrappers and parses JSON."""
        cleaned = text.strip()
        # Remove markdown code block fences if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
            # Handle case if LLM returned a list instead of dict
            if isinstance(data, list):
                data = {
                    "topic": "IELTS Topic",
                    "part": 1,
                    "part_name": "IELTS Speaking",
                    "question": "Sample Question",
                    "chunks": data
                }
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Gemini yanıtı geçerli bir JSON olarak ayrıştırılamadı: {e}\nYanıt:\n{text}")

    def _validate_ielts_json(self, data: Dict[str, Any], expected_part: int):
        """Ensures that the JSON has required fields and chunks."""
        if "chunks" not in data or not isinstance(data["chunks"], list):
            raise ValueError("JSON yanıtında 'chunks' listesi bulunamadı.")

        if len(data["chunks"]) == 0:
            raise ValueError("JSON yanıtındaki 'chunks' listesi boş.")

        valid_chunks = []
        for i, chunk in enumerate(data["chunks"]):
            if isinstance(chunk, dict) and "en" in chunk and "tr" in chunk:
                valid_chunks.append({
                    "en": str(chunk["en"]).strip(),
                    "tr": str(chunk["tr"]).strip()
                })

        if not valid_chunks:
            raise ValueError("Chunks listesinde geçerli 'en' ve 'tr' çiftleri bulunamadı.")

        data["chunks"] = valid_chunks
        if "part" not in data:
            data["part"] = expected_part
        if "question" not in data:
            data["question"] = "IELTS Speaking Practice"
