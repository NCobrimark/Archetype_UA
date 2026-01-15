from typing import List, Dict, Optional
import json
import asyncio
from .config import settings
from .models import ArchetypeType

# Placeholder for actual API client
# We will implement Gemini logic here

from openai import AsyncOpenAI

class AIService:
    def __init__(self):
        # Initialize OpenRouter Client
        # OpenRouter uses the OpenAI SDK but with a custom base_url
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            timeout=60.0
        )
        self.model = settings.OPENROUTER_MODEL

    async def analyze_open_text(self, text: str, context: str) -> Optional[Dict[str, any]]:
        """
        Analyzes the user's open text answer.
        Returns mapped Archetype and confidence score.
        """
        prompt_text = f"Context: {context}\nUser Answer: {text}\nTask: Identify Jungian Archetype."
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Jungian Analyst. return valid JSON only: { 'archetype': 'Hero', 'confidence': 0.9 } "},
                    {"role": "user", "content": prompt_text}
                ],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"AI Error: {e}")
            return None

    async def synthesize_meta_archetype(self, primary_archetypes: List[str]) -> Dict[str, str]:
        """
        Generates a unique title and description for a combination of archetypes.
        """
        arch_str = ", ".join(primary_archetypes)
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a poetic archetype synthesizer. Return JSON: { 'title': '...', 'description': '...' }"},
                    {"role": "user", "content": f"Dominant Archetypes: {', '.join(primary_archetypes)}. Synthesize a Meta-Archetype title and description."}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"AI Synthesis Error: {e}")
            return {"title": "The Unified Soul", "description": "Complex integration."}

    async def generate_report_strategy(self, scores: Dict[str, int]) -> str:
        """
        Generates the full markdown content for the strategy section of the report.
        """
        prompt = (
            f"Archetype Scores: {scores}. \n"
            "Generate a comprehensive marketing and branding strategy in Ukrainian based on these scores. "
            "The report should include: \n"
            "1. **Сильні сторони** вашого профілю.\n"
            "2. **Комунікаційна стратегія**: як вам спілкуватися з аудиторією.\n"
            "3. **Візуальні коди**: які кольори та образи використовувати.\n"
            "4. **Маркетингові поради**: конкретні кроки для росту.\n"
            "Use clear Markdown headers (##) and bullet points."
        )
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ви — провідний експерт з брендингу та архетипів. Ваше завдання — створити глибоку та практичну стратегію на основі результатів тесту. Мова: Українська."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return "## Strategy Error\nCould not generate strategy."

ai_service = AIService()
