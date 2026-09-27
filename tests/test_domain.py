from decimal import Decimal
import random

import pytest

from mathblitz.domain.activities import list_activities
from mathblitz.domain.difficulty import Difficulty, profile_for
from mathblitz.domain.scoring import answers_match, points_for_correct_answer


def test_requested_difficulty_levels_are_canonical() -> None:
    assert [level.value for level in Difficulty] == [
        "Very Easy",
        "Easy",
        "Medium",
        "Hard",
        "Extreme Hard",
    ]


@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_every_activity_generates_a_solvable_task(difficulty: Difficulty) -> None:
    for index, activity in enumerate(list_activities()):
        assert activity.variant_estimate >= 10000
        task = activity.generator.generate(difficulty, random.Random(index))
        assert task.prompt
        assert task.hint
        assert isinstance(task.correct_answer, Decimal)
        assert task.answer_mode in {"integer", "currency", "decimal", "choice"}


def test_difficulty_increases_base_score_and_reduces_time() -> None:
    profiles = [profile_for(level) for level in Difficulty]
    assert [profile.time_limit_seconds for profile in profiles] == [90, 60, 45, 30, 20]
    assert points_for_correct_answer(Difficulty.EXTREME_HARD, 20) > points_for_correct_answer(
        Difficulty.VERY_EASY, 20
    )


def test_currency_answer_accepts_cent_rounding_only() -> None:
    assert answers_match(Decimal("14.50"), Decimal("14.499"), "currency")
    assert not answers_match(Decimal("14.50"), Decimal("14.48"), "currency")
    assert not answers_match(Decimal("4"), Decimal("4.01"), "integer")
