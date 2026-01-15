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
        
        for arch in ArchetypeType:
            if arch not in raw_scores:
                raw_scores[arch] = 0
                
        # Sort items by score DESC
        sorted_archs = sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)
        
        primary = []
        if sorted_archs:
            # 1st is always primary
            primary.append(sorted_archs[0][0])
            max_score = sorted_archs[0][1]
            
            # 2nd is primary if within 10% of 1st
            if len(sorted_archs) > 1:
                score2 = sorted_archs[1][1]
                if max_score > 0 and (max_score - score2) / max_score <= 0.10:
                    primary.append(sorted_archs[1][0])
                    
                    # 3rd is primary if within 10% of 2nd
                    if len(sorted_archs) > 2:
                        score3 = sorted_archs[2][1]
                        if score2 > 0 and (score2 - score3) / score2 <= 0.10:
                            primary.append(sorted_archs[2][0])
        
        # Secondary logic remains similar or we can simplify
        secondary = []
        # Let's just take the next 2-3 as secondary for the chart/report
        remain = [a for a, s in sorted_archs if a not in primary]
        secondary = remain[:3]
        
        return ScoringResult(
            archetype_scores=raw_scores,
            primary_cluster=primary,
            secondary_cluster=secondary,
            meta_archetype_title=None
        )

    def needs_meta_archetype(self, result: ScoringResult) -> bool:
        # User feedback: > 2 archetypes
        return len(result.primary_cluster) > 2

