from datetime import datetime, timedelta
from typing import Tuple

class SpacedRepetitionService:
    """
    SuperMemo SM-2 Spaced Repetition Algorithm for MPSC revision facts.
    """

    @staticmethod
    def calculate_next_review(
        rating: int,  # 1 (complete blackout) to 5 (perfect recall)
        repetition_count: int,
        interval_days: int,
        ease_factor: float
    ) -> Tuple[int, int, float, datetime]:
        """
        Computes (new_repetition_count, new_interval_days, new_ease_factor, next_due_date).
        """
        # Ensure ease factor bounds
        if ease_factor < 1.3:
            ease_factor = 1.3

        if rating >= 3:
            # Successful recall
            if repetition_count == 0:
                interval_days = 1
            elif repetition_count == 1:
                interval_days = 6
            else:
                interval_days = int(round(interval_days * ease_factor))

            repetition_count += 1
        else:
            # Failed recall - reset streak
            repetition_count = 0
            interval_days = 1

        # Update ease factor based on SM-2 formula:
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        ease_factor = ease_factor + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
        if ease_factor < 1.3:
            ease_factor = 1.3

        next_due = datetime.utcnow() + timedelta(days=interval_days)
        return repetition_count, interval_days, ease_factor, next_due

spaced_repetition_service = SpacedRepetitionService()
