"""Canonical difficulty levels and their gameplay constraints."""

from dataclasses import dataclass
from enum import Enum


class Difficulty(str, Enum):
    VERY_EASY = "Very Easy"
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    EXTREME_HARD = "Extreme Hard"


@dataclass(frozen=True)
class DifficultyProfile:
    difficulty: Difficulty
    time_limit_seconds: int
    points_multiplier: int
    magnitude: int
    description: str


PROFILES = {
    Difficulty.VERY_EASY: DifficultyProfile(
        Difficulty.VERY_EASY, 90, 1, 1, "One-step problems with friendly numbers."
    ),
    Difficulty.EASY: DifficultyProfile(
        Difficulty.EASY, 60, 2, 2, "Short calculations with common values."
    ),
    Difficulty.MEDIUM: DifficultyProfile(
        Difficulty.MEDIUM, 45, 3, 3, "Everyday multi-step reasoning."
    ),
    Difficulty.HARD: DifficultyProfile(
        Difficulty.HARD, 30, 4, 4, "Larger numbers and less obvious operations."
    ),
    Difficulty.EXTREME_HARD: DifficultyProfile(
        Difficulty.EXTREME_HARD,
        20,
        5,
        5,
        "Fast, multi-step problems that reward precision.",
    ),
}


def profile_for(difficulty: Difficulty) -> DifficultyProfile:
    return PROFILES[difficulty]
