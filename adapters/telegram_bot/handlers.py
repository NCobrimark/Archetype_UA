import io
import random
import asyncio
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, BufferedInputFile

from core.engine import ArchetypeEngine
from adapters.db_repo import db_repo
from reports.chart_maker import create_radar_chart
from reports.pdf_generator import generate_pdf_report
from core.ai_service import ai_service
from core.email_service import send_report_email
from core.models import UserSession, Question
from .keyboards import get_question_keyboard, get_lead_magnet_keyboard
from .states import TestStates, LeadMagnetStates

router = Router()
engine = ArchetypeEngine() # Loads questions

# Temporary storage for simple session flow if not using DB logic strictly every step
# But we should use FSM data.

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # 1. Create User/Session
    user = await db_repo.get_or_create_user(message.from_user.id, message.from_user.full_name)
    session = await db_repo.create_session(user.id)
    
    # 2. Randomize Question IDs
    q_ids = list(engine.questions.keys())
    random.shuffle(q_ids)
    
    await state.update_data(
        session_id=session.id, 
        current_q_index=0,
        question_order=q_ids
    )
    
    # 3. Send Intro
    await message.answer("Вітаю! Це тест на Архетипи. 36 питань допоможуть визначити ваш профіль.")
    
    # 4. Send Q1
    await send_question(message, state)
    await state.set_state(TestStates.answering_questions)

async def send_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    q_index = data.get("current_q_index", 0)
    q_order = data.get("question_order")
    
    if not q_order:
        # Fallback if state lost or first run
        q_order = list(engine.questions.keys())
    
    q_id = q_order[q_index]
    q = engine.questions.get(q_id)
    if not q:
        import logging
        logging.error(f"Question {q_id} not found in Engine! Total Loaded: {len(engine.questions)}")
        await message.answer("⚠️ Вибачте, сталася технічна помилка. Питання не знайдено.")
        return
    
    
    text = f"<b>{q_index + 1}. {q.text}</b>\n\n{q.context}\n\n<i>{q.coaching_question}</i>"
    kb = get_question_keyboard(q.options)
    await message.answer(text,  reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("ans:"))
async def process_answer(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    q_index = data.get("current_q_index", 0)
    session_id = data.get("session_id")
    q_order = data.get("question_order")
    
    option_id = callback.data.split(":")[1]
    current_q_id = q_order[q_index]
    
    # Handle "Own Answer" (Option F)
    if option_id == "F":
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("Будь ласка, введіть вашу власну відповідь:")
        await state.set_state(TestStates.waiting_for_open_text)
        await callback.answer()
        return

    # Save Standard Answer
    await db_repo.save_answer(session_id, current_q_id, option_id)
    await callback.answer()
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await proceed_to_next(callback.message, state)

@router.message(TestStates.waiting_for_open_text)
async def process_open_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    q_index = data.get("current_q_index", 0)
    session_id = data.get("session_id")
    q_order = data.get("question_order")
    current_q_id = q_order[q_index]
    
    # Save Answer with Text
    await db_repo.save_answer(session_id, current_q_id, "F", open_text=message.text)
    
    await state.set_state(TestStates.answering_questions)
    await proceed_to_next(message, state)

async def proceed_to_next(message: types.Message, state: FSMContext):
    data = await state.get_data()
    q_index = data.get("current_q_index", 0)
    q_order = data.get("question_order")
    
    next_index = q_index + 1
    
    # Intermediate Progress Messages
    progress_messages = {
        9: "🚀 Чудовий початок! Ви пройшли 25% тесту. Ваша щирість — ключ до точного результату.",
        18: "🌓 Ви вже на екваторі (50%)! Архетипи починають проявлятися ясніше. Продовжуємо?",
        27: "🏁 Залишився останній ривок (75%)! Ви вже майже бачите свій повний профіль."
    }
    
    if next_index in progress_messages:
        await message.answer(progress_messages[next_index])

    if next_index < len(q_order):
        await state.update_data(current_q_index=next_index)
        await send_question(message, state)
    else:
        await finish_test(message, state)

async def finish_test(message: types.Message, state: FSMContext):
    # 1. Congratulation
    await message.answer("🎉 <b>Вітаю! Ви відповіли на всі питання!</b>\n\nТепер починається найцікавіше — аналіз вашого профілю.", parse_mode="HTML")
    
    # 2. Start Timer & Analysis
    timer_msg = await message.answer("⏳ <b>Запускаю процес аналізу...</b>\nЗалишилось: 2:00", parse_mode="HTML")
    
    # Run scoring in background/parallel to timer if needed, 
    # but the user wants results AFTER the countdown.
    data = await state.get_data()
    session_id = data.get("session_id")
    
    # Prepare data for scoring
    session_obj = await db_repo.get_session_with_answers(session_id)
    from core.models import UserSession as PydanticSession, UserAnswer
    p_answers = [
        UserAnswer(question_id=a.question_id, selected_option_id=a.selected_option_id, open_text_input=a.open_text_input)
        for a in session_obj.answers
    ]
    p_session = PydanticSession(
         user_id=session_obj.user_id,
         started_at=session_obj.started_at,
         answers=p_answers
    )
    result = engine.calculate_scores(p_session)
    await state.update_data(scoring_result=result.model_dump())

    # Start countdown loop (2 minutes = 120 seconds)
    # We edit every 5-10 seconds to avoid hitting Telegram limits
    total_seconds = 120
    step = 5
    
    # In parallel, we can start the AI synthesis so it's ready when timer ends
    ai_task = None
    if engine.needs_meta_archetype(result):
        primary_names = [a.value for a in result.primary_cluster]
        ai_task = asyncio.create_task(ai_service.synthesize_meta_archetype(primary_names))

    for remaining in range(total_seconds - step, -1, -step):
        await asyncio.sleep(step)
        mins, secs = divmod(remaining, 60)
        try:
            await timer_msg.edit_text(f"⏳ <b>Аналізую ваші результати...</b>\nЗалишилось: {mins}:{secs:02d}", parse_mode="HTML")
        except Exception as e:
            import logging
            logging.error(f"Timer edit failed: {e}")
            # If edit fails, we just continue or stop
    
    # Ensure AI is done with a safety timeout
    meta_title = None
    if ai_task:
        try:
            # We already waited 2 minutes, AI should be done. 
            # But let's wait a bit more just in case.
            ai_res = await asyncio.wait_for(ai_task, timeout=10.0) 
            meta_title = ai_res.get("title")
            await state.update_data(meta_title=meta_title)
        except Exception as e:
            import logging
            logging.error(f"AI Synthesis failed or timed out: {e}")

    # 3. Final Results
    await timer_msg.delete()
    
    # Generate Chart
    chart_buf = create_radar_chart(result.archetype_scores)
    
    caption = f"🏁 <b>Ваші результати готові!</b>\n\n"
    if meta_title:
        caption += f"🔮 <b>Ваш Мета-Архетип:</b> {meta_title}\n\n"
    
    # Show Top Archetypes
    primary_names = [t.ukrainian_name for t in result.primary_cluster]
    caption += f"🏆 <b>Домінантні архетипи:</b> {', '.join(primary_names)}\n\n"
    
    # Show All Scores as requested
    caption += "📊 <b>Детальні бали:</b>\n"
    sorted_scores = sorted(result.archetype_scores.items(), key=lambda x: x[1], reverse=True)
    for arch, score in sorted_scores:
        caption += f"• {arch.ukrainian_name.split(' (')[0]}: {score}\n"
        
    caption += "\nПовний опис стратегії доступний у звіті нижче."
    
    input_file = BufferedInputFile(chart_buf.getvalue(), filename="chart.png")
    await message.answer_photo(input_file, caption=caption, parse_mode="HTML")
    await message.answer("Щоб отримати повний PDF-звіт та стратегію, заповніть дані:", reply_markup=get_lead_magnet_keyboard())
    await state.set_state(LeadMagnetStates.waiting_for_name)

@router.callback_query(F.data == "get_report")
async def start_lead_magnet(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введіть ваше ім'я для звіту:")
    await state.set_state(LeadMagnetStates.waiting_for_name)
    await callback.answer()

@router.message(LeadMagnetStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(user_name=message.text)
    await message.answer("Введіть ваш номер телефону:")
    await state.set_state(LeadMagnetStates.waiting_for_phone)

@router.message(LeadMagnetStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(user_phone=message.text)
    await message.answer("Введіть ваш Email (туди прийде PDF):")
    await state.set_state(LeadMagnetStates.waiting_for_email)

@router.message(LeadMagnetStates.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    email = message.text
    await state.update_data(user_email=email)
    
    # Generate PDF
    await message.answer("⏳ Генерую PDF файл (~10-20 секунд)...")
    
    data = await state.get_data()
    scoring_result = data.get("scoring_result") 
    # Use real objects
    
    # Re-create chart for PDF (buffer was consumed? Yes usually seek(0) helps but better recreate)
    # Actually we stored result, can recreate.
    
    # Generate Strategy Logic (Stub)
    strategy_text = await ai_service.generate_report_strategy(scoring_result['archetype_scores'])
    
    # Chart
    chart_buf = create_radar_chart(scoring_result['archetype_scores'])
    
    try:
        pdf_buf = generate_pdf_report(
            user_name=data.get("user_name"),
            user_phone=data.get("user_phone", "Не вказано"),
            meta_archetype_title=data.get("meta_title", "Архетипний Профіль"),
            scoring_data=scoring_result,
            strategy_content=strategy_text,
            chart_buffer=chart_buf
        )
    except Exception as e:
        import logging
        logging.error(f"PDF Generation Failed: {e}")
        await message.answer("❌ Сталася помилка при генерації PDF. Але ваші результати збережені, ми надішлемо їх пізніше.")
        return
    
    pdf_file = BufferedInputFile(pdf_buf.getvalue(), filename=f"Archetype_{data.get('user_name')}.pdf")
    
    # Send via Telegram
    await message.answer_document(pdf_file, caption="Ваш персональний звіт готовий!")
    
    # Send via Email
    await send_report_email(
        to_email=email,
        user_name=data.get("user_name"),
        user_phone=data.get("user_phone", "Не вказано"),
        pdf_buf=pdf_buf,
        filename=f"Archetype_{data.get('user_name')}.pdf"
    )
    
    await message.answer("✅ Також я щойно відправив цей звіт на вашу пошту. Перевірте папку 'Вхідні' (або 'Спам').")
    
    await state.clear()
