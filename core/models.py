from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime

class ArchetypeType(str, Enum):
    INNOCENT = "Innocent"
    EVERYMAN = "Everyman"
    HERO = "Hero"
    CAREGIVER = "Caregiver"
    EXPLORER = "Explorer"
    LOVER = "Lover"
    OUTLAW = "Outlaw"
    CREATOR = "Creator"
    RULER = "Ruler"
    MAGICIAN = "Magician"
    SAGE = "Sage"
    JESTER = "Jester"

    # Ukrainian mapping
    @property
    def ukrainian_name(self) -> str:
        mapping = {
            "Innocent": "Невинний (Innocent)",
            "Everyman": "Славний Малий (Everyman)",
            "Hero": "Герой (Hero)",
            "Caregiver": "Опікун (Caregiver)",
            "Explorer": "Шукач (Explorer)",
            "Lover": "Коханець (Lover)",
            "Outlaw": "Бунтар (Outlaw)",
            "Creator": "Творець (Creator)",
            "Ruler": "Правитель (Ruler)",
            "Magician": "Маг (Magician)",
            "Sage": "Мудрець (Sage)",
            "Jester": "Блазень (Jester)"
        }
        return mapping.get(self.value, self.value)

class QuestionOption(BaseModel):
    id: str  # "A", "B", ... "F"
    text: str
    archetype: Optional[ArchetypeType] = None  # None for Open Text
    points: int = 2

class Question(BaseModel):
    id: int
    text: str # Keeping it simple, context + coaching question combined or separate?
    context: str
    coaching_question: str
    options: List[QuestionOption]
    domain: str # "Business", "Family", "Social"

class UserAnswer(BaseModel):
    question_id: int
    selected_option_id: str
    open_text_input: Optional[str] = None
    
class ScoringResult(BaseModel):
    archetype_scores: Dict[ArchetypeType, int]
    primary_cluster: List[ArchetypeType]
    secondary_cluster: List[ArchetypeType]
    meta_archetype_title: Optional[str] = None
    
class UserSession(BaseModel):
    user_id: int
    started_at: datetime
    answers: List[UserAnswer] = []
    is_completed: bool = False
