from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
from core.models import QuestionOption

def get_question_keyboard(options: List[QuestionOption]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for opt in options:
        # Callback data format: "ans:{option_id}"
        # Truncate text for specific mobile view if needed? 
        # Telegram buttons wrap text automatically.
        # Add a newline to make buttons 'higher' as requested
        text = f"{opt.id}) {opt.text}\n"
        builder.button(text=text, callback_data=f"ans:{opt.id}")
    builder.adjust(1) # 1 column
    return builder.as_markup()

def get_lead_magnet_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📥 Отримати детальний звіт та стратегію", 
        callback_data="get_report"
    )
    return builder.as_markup()
