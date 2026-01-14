import json
import os
from typing import List, Dict, Tuple
from collections import defaultdict
from .models import UserSession, ScoringResult, ArchetypeType, Question, QuestionOption

MAX_SCORE_THRESHOLD = 2
SECONDARY_SCORE_THRESHOLD_START = 3
SECONDARY_SCORE_THRESHOLD_END = 5
SECONDARY_PERCENTAGE_DIFF = 0.10

class ArchetypeEngine:
    def __init__(self, questions_path: str = "data/questions.json"):
        self.questions: Dict[int, Question] = {}
        self.load_questions(questions_path)

    def load_questions(self, path: str):
        # Determine strict absolute path relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_path = os.path.join(base_dir, "data", "questions.json")
        
        if not os.path.exists(target_path):
            print(f"CRITICAL ERROR: Questions file not found at {target_path}")
            # Try plain relative just in case
            if os.path.exists("data/questions.json"):
                target_path = "data/questions.json"
        
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for q_data in data:
                    q = Question(**q_data)
                    self.questions[q.id] = q
            print(f"Loaded {len(self.questions)} questions from {target_path}.")
        except Exception as e:
            print(f"Error loading questions from {target_path}: {e}")

    def calculate_scores(self, session: UserSession) -> ScoringResult:
        scores: Dict[ArchetypeType, int] = defaultdict(int)
        
        for ans in session.answers:
            if ans.question_id in self.questions:
                question = self.questions[ans.question_id]
                # Find the selected option
                selected_opt = next((opt for opt in question.options if opt.id == ans.selected_option_id), None)
                if selected_opt and selected_opt.archetype:
                    # Enum conversion might be needed if JSON has string "Innocent" but Enum is ArchetypeType.INNOCENT
                    # Pydantic handles str to Enum usually if exact match.
                    scores[selected_opt.archetype] += selected_opt.points
                    
        return self.process_results(scores)

    def process_results(self, raw_scores: Dict[ArchetypeType, int]) -> ScoringResult:
        if not raw_scores:
             return ScoringResult(archetype_scores={}, primary_cluster=[], secondary_cluster=[])
        
        # Ensure we have scores for all archetypes (even 0) for the chart?
        # Or just relevant ones. Let's keep sparse or fill 0?
        # Fill 0 for safety
        for arch in ArchetypeType:
            if arch not in raw_scores:
                raw_scores[arch] = 0
                
        max_score = max(raw_scores.values())
        
        # Primary Cluster: [Max, Max - 2]
        primary = [
            arch for arch, score in raw_scores.items() 
            if score >= (max_score - MAX_SCORE_THRESHOLD)
        ]
        
        # Secondary Cluster: [Max - 3, Max - 5] AND < 10% diff logic
        # User Logic: "difference with previous group < 10%"
        # Let's calculate average of Primary.
        avg_primary = sum(raw_scores[a] for a in primary) / len(primary)
        
        secondary_candidates = [
            arch for arch, score in raw_scores.items()
            if (max_score - SECONDARY_SCORE_THRESHOLD_END) <= score <= (max_score - SECONDARY_SCORE_THRESHOLD_START)
        ]
        
        secondary = []
        if secondary_candidates:
            avg_secondary = sum(raw_scores[a] for a in secondary_candidates) / len(secondary_candidates)
            diff = (avg_primary - avg_secondary) / avg_primary
            if diff < SECONDARY_PERCENTAGE_DIFF:
                secondary = secondary_candidates
        
        # Sort desc
        primary.sort(key=lambda x: raw_scores[x], reverse=True)
        secondary.sort(key=lambda x: raw_scores[x], reverse=True)
        
        return ScoringResult(
            archetype_scores=raw_scores,
            primary_cluster=primary,
            secondary_cluster=secondary,
            meta_archetype_title=None
        )

    def needs_meta_archetype(self, result: ScoringResult) -> bool:
        # User feedback: > 2 archetypes
        return len(result.primary_cluster) > 2

