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
    limit = action_limit(level)
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


def action_limit(level: Level) -> int:
    """Gold/Mastery action threshold (explicit mastery cap or reference)."""
    return level.mastery.max_actions or level.reference_actions


def describe_mastery(level: Level) -> str:
    """One-line summary of what Mastery requires for a level."""
    m = level.mastery
    bits: list[str] = []
    if m.required_keys:
        bits.append("use " + " ".join(m.required_keys))
    if m.required_families:
        bits.append("use " + "/".join(m.required_families) + " motions")
    if m.min_families:
        bits.append(f"use {m.min_families}+ motion families")
    if m.single_search:
        bits.append("a single search")
    bits.append("no hints")
    limit = action_limit(level)
    if limit:
        bits.append(f"≤ {limit} actions")
    return "Mastery needs: " + ", ".join(bits)


def mastery_gaps(level: Level, stats: AttemptStats) -> list[str]:
    """Human-readable reasons a completed attempt missed Mastery (or more).

    Empty means nothing blocked Mastery — but only meaningful alongside a
    Mastery rank, since lower ranks stop at earlier gates.
    """
    gaps: list[str] = []
    if not stats.completed:
        return ["level incomplete"]
    if stats.invalid:
        gaps.append(
            f"{stats.invalid} invalid command{'s' if stats.invalid != 1 else ''}"
        )
    limit = action_limit(level)
    if limit and stats.actions > limit:
        gaps.append(f"{stats.actions} actions (limit {limit})")
    m = level.mastery
    missing_keys = [k for k in m.required_keys if k not in stats.keys_used]
    if missing_keys:
        gaps.append("never used " + " ".join(missing_keys))
    missing_fams = [f for f in m.required_families if f not in stats.families_used]
    if missing_fams:
        gaps.append("never used " + "/".join(missing_fams) + " motions")
    if m.min_families and len(stats.families_used) < m.min_families:
        gaps.append(
            f"only {len(stats.families_used)} motion families "
            f"(need {m.min_families})"
        )
    if m.single_search and stats.search_count != 1:
        gaps.append(f"{stats.search_count} searches (need exactly 1)")
    if stats.hints_used:
        gaps.append(
            f"{stats.hints_used} hint{'s' if stats.hints_used != 1 else ''} used"
        )
    return gaps
