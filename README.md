# Archetype Chatbot Project

This is a Telegram Chatbot for Jungian Archetype Testing, built with Python, Aiogram, and OpenAI/Gemini.

## Project Structure
- `core/`: Business logic, models, AI service.
- `adapters/`: Database repository and Telegram Bot handlers.
- `reports/`: PDF generation and Chart rendering.
- `data/`: `questions.json` content database.

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   Create a `.env` file in this directory (copy from `.env.example`):
   ```ini
   BOT_TOKEN=your_telegram_bot_token
   OPENAI_API_KEY=your_openai_key
   GEMINI_API_KEY=your_gemini_key
   DATABASE_URL=sqlite+aiosqlite:///./archetype.db
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   ```

3. **Run the Bot**
   Execute from the project root:
   ```bash
   python -m adapters.telegram_bot.main
   ```

## Features
- 36 Archetype scenarios (Work, Family, Social).
- "Cluster Detection" scoring logic.
- AI-powered "Meta-Archetype" synthesis.
- PDF Lead Magnet generation (Strategy Report).
