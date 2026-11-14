import json
from pathlib import Path

from scripts.build_guest_catalog import build_catalog


def test_guest_bank_matches_generators_and_contains_32_unique_challenges_per_level():
    checked_in = json.loads(Path("frontend/assets/guest-catalog.json").read_text(encoding="utf-8"))
    assert checked_in == build_catalog()
    prompts = set()
    for levels in checked_in["puzzles"].values():
        assert len(levels) == 5
        for pool in levels.values():
            assert len(pool) == 32
            assert len({entry[0] for entry in pool}) == 32
            for prompt, hint, mode, answer in pool:
                assert prompt and hint
                assert isinstance(answer, (int, float))
                if mode == "choice":
                    assert answer in (1, 2)
                # Some generators reuse the same prompt across difficulty levels.
                prompts.add(prompt)
    assert len(checked_in["puzzles"]) == 12
    assert len(prompts) >= 1850
