import random

RANDOM_TOPICS = [
    "Public Transport",
    "Hometown & Urban Transformation",
    "Artificial Intelligence & Future Careers",
    "Environmental Sustainability & Recycling",
    "A Memorable Journey",
    "Traditional Festivals & Celebrations",
    "Social Media & Human Connection",
    "Lifelong Learning & Higher Education",
    "Healthy Lifestyle & Nutrition",
    "Reading Habits & Digital Books",
    "Modern Architecture & Historic Heritage",
    "Work-Life Balance",
    "Art, Music & Creativity",
    "Childhood Memories & Games",
    "Travel & Cultural Immersion",
    "Consumerism & Shopping Habits"
]

BAND_CRITERIA = {
    "1-4": {
        "title": "Band 1.0 - 4.0 (Temel / Beginner)",
        "description": "A1-A2 Elementary English. Use simple vocabulary, basic present and past simple tenses, direct straightforward sentences, and short easy-to-repeat chunks (3-5 words per chunk). Avoid idioms, complex subordinations, or academic words.",
        "notes_label": "Band 1-4 Temel Kelimeler ve Kalıplar"
    },
    "4.5-5.5": {
        "title": "Band 4.5 - 5.5 (Orta / Intermediate)",
        "description": "B1 Intermediate English. Use everyday conversational vocabulary, compound sentences connected by 'and', 'but', 'so', 'because', and familiar expressions. Chunks should be 4-6 words long.",
        "notes_label": "Band 5 Günlük İfadeler ve Bağlaçlar"
    },
    "6-7": {
        "title": "Band 6.0 - 7.0 (İleri / Competent)",
        "description": "B2 Competent English. Use a good range of vocabulary with natural collocations, complex sentence structures (relative clauses, conditionals, passive forms), and clear cohesive devices. Chunks should be 5-8 words long.",
        "notes_label": "Band 6-7 Eşdizimler (Collocations) ve Karmaşık Yapılar"
    },
    "7.5+": {
        "title": "Band 7.5+ (Uzman / Master)",
        "description": "C1-C2 Master English. Use sophisticated topic-specific lexis, natural idiomatic expressions, nuanced discourse markers, stylistic variation (e.g. inversion, advanced fronting), and authentic native-like speech flow. Chunks should be 6-9 words long.",
        "notes_label": "Band 7.5+ İleri Düzey İdiomlar ve Akademik Kelimeler"
    }
}

def get_random_topic() -> str:
    """Returns a random IELTS speaking topic."""
    return random.choice(RANDOM_TOPICS)

def get_system_prompt(band_level: str = "7.5+") -> str:
    criteria = BAND_CRITERIA.get(band_level, BAND_CRITERIA["7.5+"])
    return f"""You are an expert IELTS Speaking Examiner and Cambridge-certified English Pronunciation Coach.
Your mission is to generate authentic IELTS Speaking test materials tailored specifically for speech shadowing practice.

TARGET LEVEL: {criteria['title']}
PROFICIENCY GUIDELINES:
{criteria['description']}

CRITICAL REQUIREMENTS:
1. Strict Level Adherence: Ensure the vocabulary, syntax, and complexity strictly match {criteria['title']}.
2. Chunking for Shadowing: Divide the candidate's answer into natural 'thought groups' or 'breath chunks'. Each chunk must represent a meaningful grammatical phrase so the learner can listen, digest, and repeat it comfortably.
3. Accuracy: The Turkish translations ('tr') must be natural, accurate, and correspond strictly to each English chunk ('en').
4. Strict JSON Format: You must output ONLY valid, parsable JSON matching the required schema. No markdown outside the JSON, no conversational chatter."""

def get_ielts_prompt(topic: str, part: int = 1, band_level: str = "7.5+") -> str:
    """
    Builds the user prompt for IELTS Part 1, 2, or 3 based on topic and target band level.
    """
    criteria = BAND_CRITERIA.get(band_level, BAND_CRITERIA["7.5+"])

    if part == 1:
        part_instruction = f"""
Create an IELTS Speaking Part 1 (Introduction and Interview) task for topic: '{topic}' targeting {criteria['title']}.
- Question: A realistic examiner question about daily habits, personal routine, or preferences.
- Answer: Around 40-60 words (3-4 sentences), divided into 4-6 concise shadowing chunks matching the target band level.
"""
    elif part == 2:
        part_instruction = f"""
Create an IELTS Speaking Part 2 (Long Turn / Cue Card) task for topic: '{topic}' targeting {criteria['title']}.
- Question: Classic Cue Card format ('Describe ...' with 3-4 bullet points).
- Answer: A cohesive monologue (around 100-150 words), divided into 7-11 natural shadowing chunks matching the target band level.
"""
    else:  # Part 3
        part_instruction = f"""
Create an IELTS Speaking Part 3 (Two-way Discussion) task for topic: '{topic}' targeting {criteria['title']}.
- Question: An analytical discussion question exploring broader societal or global angles.
- Answer: A thoughtful response, divided into 5-8 natural shadowing chunks matching the target band level.
"""

    format_instruction = f"""
OUTPUT JSON SCHEMA (Strictly adhere to this JSON structure):
{{
  "topic": "{topic}",
  "part": {part},
  "part_name": "<Part 1: Introduction | Part 2: Long Turn (Cue Card) | Part 3: Two-way Discussion>",
  "band_level": "{band_level}",
  "band_title": "{criteria['title']}",
  "question": "<The full examiner question or Cue Card prompt with bullet points>",
  "band_notes": "<1-2 sentences highlighting key vocabulary or grammar features for {criteria['notes_label']} used in this answer>",
  "chunks": [
    {{
      "en": "<English chunk 1>",
      "tr": "<Natural Turkish translation of chunk 1>"
    }},
    {{
      "en": "<English chunk 2>",
      "tr": "<Natural Turkish translation of chunk 2>"
    }}
  ]
}}
"""
    return part_instruction.strip() + "\n\n" + format_instruction.strip()
