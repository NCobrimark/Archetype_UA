from aiogram.fsm.state import State, StatesGroup

class TestStates(StatesGroup):
    answering_questions = State() # Loop for 36 questions
    results_ready = State() # Show radar chart
    
class LeadMagnetStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()
    waiting_for_phone = State()
