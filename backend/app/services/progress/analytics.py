from typing import List, Dict, Any
from app.schemas.pydantic_models import SubjectMastery, ProgressSummaryResponse

class ProgressAnalyticsService:
    """
    Analyzes student test performance, tracks weak topics, and generates MPSC study guidance.
    """

    @staticmethod
    def calculate_subject_mastery(tests_data: List[Dict[str, Any]]) -> List[SubjectMastery]:
        """
        Aggregates test question performance per subject.
        """
        subject_stats: Dict[str, Dict[str, int]] = {}

        for t in tests_data:
            subj = t.get("subject_name", "General")
            if subj not in subject_stats:
                subject_stats[subj] = {"attempted": 0, "correct": 0}
            
            subject_stats[subj]["attempted"] += t.get("total_questions", 0)
            subject_stats[subj]["correct"] += t.get("correct_count", 0)

        results: List[SubjectMastery] = []
        for subj, stats in subject_stats.items():
            attempted = stats["attempted"]
            correct = stats["correct"]
            mastery = round((correct / attempted * 100.0), 1) if attempted > 0 else 0.0
            is_weak = mastery < 60.0 and attempted >= 5

            if is_weak:
                rec = f"⚠️ {subj} विषयामध्ये अचूकता {mastery}% आहे. या विषयाचे संदर्भ पुस्तक व मागील वर्षांचे PYQs पुन्हा अभ्यासा."
            elif mastery >= 80.0:
                rec = f"🌟 {subj} मध्ये उत्तम प्रगती ({mastery}%). चालू घडामोडींशी जोडलेली उजळणी सुरू ठेवा."
            else:
                rec = f"📌 {subj} मध्ये सरावाची गरज आहे ({mastery}%). अधिक सराव चाचण्या सोडवा."

            results.append(SubjectMastery(
                subject_name=subj,
                attempted=attempted,
                correct=correct,
                mastery_percentage=mastery,
                is_weak_area=is_weak,
                recommendation_mr=rec
            ))

        return results

progress_analytics = ProgressAnalyticsService()
