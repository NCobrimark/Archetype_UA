import textwrap
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
        # Try to force 2 lines if text is long by inserting a newline
        if len(opt.text) > 30:
            lines = textwrap.wrap(opt.text, width=30)
            if len(lines) >= 2:
                 display_text = f"{opt.id}) {lines[0]}\n{' '.join(lines[1:])}"
            else:
                 display_text = f"{opt.id}) {opt.text}"
        else:
            display_text = f"{opt.id}) {opt.text}"

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
