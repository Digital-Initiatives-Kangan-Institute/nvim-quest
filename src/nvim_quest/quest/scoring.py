"""Scoring: Bronze / Silver / Gold / Mastery ranks."""

from __future__ import annotations

from .evaluator import AttemptStats
from .models import Level

BRONZE = "Bronze"
SILVER = "Silver"
GOLD = "Gold"
MASTERY = "Mastery"
LOCKED = "Locked"

RANK_ORDER = [LOCKED, BRONZE, SILVER, GOLD, MASTERY]


def rank_attempt(level: Level, stats: AttemptStats) -> str:
    """Rank a finished attempt.

    Bronze: chain complete.
    Silver: + zero invalid commands.
    Gold: + within reference action count.
    Mastery: + required motion families, no hints (+ single-search rule).
    """
    if not stats.completed:
        return LOCKED
    rank = BRONZE
    if stats.invalid == 0:
        rank = SILVER
    else:
        return rank
    limit = level.mastery.max_actions or level.reference_actions
    if limit and stats.actions <= limit:
        rank = GOLD
    else:
        return rank
    if _meets_mastery(level, stats):
        rank = MASTERY
    return rank


def _meets_mastery(level: Level, stats: AttemptStats) -> bool:
    m = level.mastery
    if stats.hints_used > 0:
        return False
    for fam in m.required_families:
        if fam not in stats.families_used:
            return False
    for key in m.required_keys:
        if key not in stats.keys_used:
            return False
    if m.min_families and len(stats.families_used) < m.min_families:
        return False
    if m.single_search and stats.search_count != 1:
        return False
    return True


def is_better(rank_a: str, rank_b: str) -> bool:
    return RANK_ORDER.index(rank_a) > RANK_ORDER.index(rank_b)
