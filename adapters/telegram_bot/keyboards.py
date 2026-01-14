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
        # Try to force 2 lines if text is long by inserting a newline
        if len(opt.text) > 40:
            pivot = opt.text.find(' ', 35)
            if pivot != -1:
                display_text = f"{opt.id}) {opt.text[:pivot]}\n{opt.text[pivot:].strip()}"
            else:
                display_text = f"{opt.id}) {opt.text}"
        else:
            display_text = f"{opt.id}) {opt.text}\n"
            
        builder.button(text=display_text, callback_data=f"ans:{opt.id}")
    builder.adjust(1) # 1 column
    return builder.as_markup()

def get_lead_magnet_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📥 Отримати детальний звіт та стратегію", 
        callback_data="get_report"
    )
    return builder.as_markup()
