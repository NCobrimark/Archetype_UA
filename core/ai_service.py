from typing import List, Dict, Optional
import json
import asyncio
from .config import settings
from .models import ArchetypeType
import logging

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
        # Load archetype descriptions for context
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        info_path = os.path.join(base_dir, "data", "archetype_info.json")
        descriptions = {}
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                descriptions = json.load(f)
        except Exception as e:
            print(f"Error loading descriptions: {e}")

        # Construct context
        context_str = "\n".join([f"{k}: {v.get('title')} - {v.get('core_desire')}" for k, v in descriptions.items()])

        prompt = (
            f"Archetype Scores: {scores}. \n"
            f"Archetype Context:\n{context_str}\n\n"
            "Завдання: Створіть професійну маркетингову та брендингову стратегію для клієнта на основі його балів архетипів. "
            "Зверніть увагу на комбінацію домінантних архетипів (тих, що мають найвищі бали).\n\n"
            "Звіт ПОВИНЕН містити:\n"
            "1. **Глибинний аналіз комбінації**: Як ваші архетипи взаємодіють між собою? Яку унікальну 'суперсилу' вони дають?\n"
            "2. **Ваш Тіньовий аспект**: Чого варто остерігатися (слабкі місця).\n"
            "3. **Маркетингова стратегія (Plan)**: Конкретні кроки з позиціонування, вибору голосу бренду (Tone of Voice) та візуального стилю.\n"
            "4. **Рекомендації для росту**: Як масштабувати свій вплив, використовуючи ці архетипи.\n\n"
            "Мова: Українська. Форматування: Markdown (заголовки ##, списки)."
        )
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ви — експерт з брендингу, психології архетипів та стратегічного маркетингу. Створюйте контент, який виглядає як дорогий консалтинговий звіт."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"AI Strategy Error (Check API Key): {e}")
            # Fallback for empty/failed AI - summarize from descriptions
            fallback = "## Ваша стратегія (Автоматичне резюме)\n\n"
            fallback += "На жаль, сервіс ШІ тимчасово недоступний, але ось ваші ключові орієнтири на основі бази знань:\n\n"
            for arch_key, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:2]:
                info = descriptions.get(arch_key, {})
                if info:
                    fallback += f"### {info.get('title')}\n"
                    fallback += f"- **Тіньовий аспект:** {info.get('shadow')}\n"
                    fallback += f"- **Позиціонування:** {info.get('tone')}\n\n"
            return fallback

ai_service = AIService()
