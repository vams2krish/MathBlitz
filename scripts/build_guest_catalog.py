"""Export a reproducible, local-only puzzle bank from the Python generators."""

import argparse
import json
from pathlib import Path
import random

from mathblitz.domain.activities import list_activities
from mathblitz.domain.difficulty import PROFILES
from mathblitz.services import CatalogService


def build_catalog(variants: int = 32) -> dict:
    rng = random.Random(20261114)
    catalog = CatalogService.catalog()
    puzzles = {}
    for activity in list_activities():
        by_level = {}
        for level in PROFILES:
            pool = {}
            for _ in range(variants * 30):
                task = activity.generator.generate(level, rng)
                pool.setdefault(task.prompt, [task.prompt, task.hint, task.answer_mode, float(task.correct_answer)])
                if len(pool) == variants:
                    break
            if len(pool) != variants:
                raise ValueError(f"Not enough unique prompts: {activity.id} / {level.value}")
            by_level[level.value] = list(pool.values())
        puzzles[activity.id] = by_level
    return {**catalog, "puzzles": puzzles}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path, default=Path("frontend/assets/guest-catalog.json"))
    args = parser.parse_args()
    args.output.write_text(json.dumps(build_catalog(), separators=(",", ":")) + "\n", encoding="utf-8")
