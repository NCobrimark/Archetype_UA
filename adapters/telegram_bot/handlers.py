import io
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, BufferedInputFile

from ...core.engine import ArchetypeEngine
from ...adapters.db_repo import db_repo
from ...reports.chart_maker import create_radar_chart
from ...reports.pdf_generator import generate_pdf_report
from ...core.ai_service import ai_service
from ...core.models import UserSession, Question
from .states import TestStates, LeadMagnetStates
from .keyboards import get_question_keyboard, get_lead_magnet_keyboard

router = Router()
engine = ArchetypeEngine() # Loads questions

# Temporary storage for simple session flow if not using DB logic strictly every step
# But we should use FSM data.

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # 1. Create User/Session
    user = await db_repo.get_or_create_user(message.from_user.id, message.from_user.full_name)
    session = await db_repo.create_session(user.id)
    
    await state.update_data(session_id=session.id, current_q_index=0)
    
    # 2. Send Intro
    await message.answer("Вітаю! Це тест на Архетипи. 36 питань допоможуть визначити ваш профіль.")
    
    # 3. Send Q1
    await send_question(message, 1)
    await state.set_state(TestStates.answering_questions)

async def send_question(message: types.Message, q_id: int):
    q = engine.questions.get(q_id)
    if not q:
        return # Error?
    
    text = f"<b>{q.id}. {q.text}</b>\n\n{q.context}\n\n<i>{q.coaching_question}</i>"
    kb = get_question_keyboard(q.options)
    await message.answer(text,  reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("ans:"))
async def process_answer(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    q_index = data.get("current_q_index", 0)
    session_id = data.get("session_id")
    
    option_id = callback.data.split(":")[1]
    
    # Save Answer
    # q_id is index + 1
    current_q_id = q_index + 1
    
    # For MVP assume q_id maps 1-36
    await db_repo.save_answer(session_id, current_q_id, option_id)
    await callback.answer() # Ack
    
    # Next Question
    next_q_index = q_index + 1
    next_q_id = next_q_index + 1
    
    if next_q_id in engine.questions:
        await state.update_data(current_q_index=next_q_index)
        # Edit message to show selected? Or send new?
        # User requested conversation style somewhat implicitly. New message is safer.
        await callback.message.edit_reply_markup(reply_markup=None) # Remove buttons from old
        await send_question(callback.message, next_q_id)
    else:
        # Finish
        await finish_test(callback.message, state)

async def finish_test(message: types.Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")
    
    # Calc scores
    # We need to reload session with answers from DB
    session_obj = await db_repo.get_session_with_answers(session_id)
    # Convert DB session to Pydantic UserSession? 
    # Or Engine adapts. For MVP engine takes Pydantic models.
    # We need a mapper.
    # Quick fix: Construct UserSession from DB object manually
    from ...core.models import UserSession as PydanticSession, UserAnswer
    
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
    
    # AI Synthesis if needed
    meta_title = None
    if engine.needs_meta_archetype(result):
        # Call AI
        # This should be async and allow user to wait?
        await message.answer("⏳ Аналізую ваші результати за допомогою AI...")
        # For MVP Sync call or await
        primary_names = [a.value for a in result.primary_cluster]
        ai_res = await ai_service.synthesize_meta_archetype(primary_names)
        meta_title = ai_res.get("title")
        # Store for PDF
        await state.update_data(meta_title=meta_title)
    
    # Generate Chart
    chart_buf = create_radar_chart(result.archetype_scores)
    
    # Send Results
    caption = f"🏁 <b>Тест завершено!</b>\n\n"
    if meta_title:
        caption += f"🔮 <b>Ваш Мета-Архетип:</b> {meta_title}\n\n"
    else:
        # Show top 3
        top = result.primary_cluster[:3]
        caption += f"Ваші топ архетипи: {', '.join([t.ukrainian_name for t in top])}\n\n"
        
    caption += "Сильні сторони та опис доступні у повному звіті."
    
    input_file = BufferedInputFile(chart_buf.getvalue(), filename="chart.png")
    
    await message.answer_photo(input_file, caption=caption, parse_mode="HTML")
    await message.answer("Отримайте стратегію:", reply_markup=get_lead_magnet_keyboard())
    await state.set_state(LeadMagnetStates.waiting_for_name)

@router.callback_query(F.data == "get_report")
async def start_lead_magnet(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введіть ваше ім'я для звіту:")
    await state.set_state(LeadMagnetStates.waiting_for_name)
    await callback.answer()

@router.message(LeadMagnetStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(user_name=message.text)
    await message.answer("Введіть ваш Email (туди прийде PDF):")
    await state.set_state(LeadMagnetStates.waiting_for_email)

@router.message(LeadMagnetStates.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    email = message.text
    # Basic validation?
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
    
    pdf_buf = generate_pdf_report(
        user_name=data.get("user_name"),
        meta_archetype_title=data.get("meta_title", "Archetype Profile"),
        scoring_data=scoring_result,
        strategy_content=strategy_text,
        chart_buffer=chart_buf
    )
    
    pdf_file = BufferedInputFile(pdf_buf.getvalue(), filename="Archetype_Strategy.pdf")
    
    # Send
    await message.answer_document(pdf_file, caption="Ваш персональний звіт готовий!")
    # Also send to Admin?
    # await bot.send_document(ADMIN_ID, pdf_file)
    
    await state.clear()
