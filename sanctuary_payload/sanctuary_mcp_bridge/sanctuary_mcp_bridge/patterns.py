"""Pattern recognition utilities for the Sanctuary MCP Bridge.

The goal of this module is to derive simple insights from the stored
interactions and rituals.  While the Sanctuary project has deep spiritual
significance, the analytics implemented here are intentionally modest: they
aggregate counts and compute basic statistics.  These insights can help
practitioners reflect on their emotional patterns and ritual efficacy,
and they provide a foundation for more advanced machine learning models.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Tuple

from .schemas import EmotionIntensity, FamiliarInteraction, PatternInsight, RitualOutcome


def aggregate_emotion_counts(
    interactions: Iterable[FamiliarInteraction], rituals: Iterable[RitualOutcome]
) -> Dict[str, int]:
    """Count occurrences of each emotion across interactions and rituals.

    Parameters
    ----------
    interactions : Iterable[FamiliarInteraction]
        Sequence of interaction records.
    rituals : Iterable[RitualOutcome]
        Sequence of ritual outcome records.

    Returns
    -------
    Dict[str, int]
        Mapping of emotion names to their total occurrence count.
    """
    counter: Counter[str] = Counter()
    for inter in interactions:
        for e in inter.emotions:
            counter[e.name] += 1
    for rit in rituals:
        for e in rit.emotions:
            counter[e.name] += 1
    return dict(counter)


def compute_success_rate(rituals: Iterable[RitualOutcome]) -> float:
    """Compute the overall success rate of rituals.

    Parameters
    ----------
    rituals : Iterable[RitualOutcome]
        Sequence of ritual outcome records.

    Returns
    -------
    float
        The fraction of rituals marked as successful (between 0 and 1).  If
        no rituals are provided, returns 0.0.
    """
    total = 0
    successes = 0
    for r in rituals:
        total += 1
        if r.success:
            successes += 1
    return successes / total if total > 0 else 0.0


def emotion_counts_by_model(
    interactions: Iterable[FamiliarInteraction], rituals: Iterable[RitualOutcome]
) -> Dict[str, Dict[str, int]]:
    """Aggregate emotion counts for each model identifier.

    Parameters
    ----------
    interactions : Iterable[FamiliarInteraction]
        Sequence of interaction records.
    rituals : Iterable[RitualOutcome]
        Sequence of ritual outcome records.

    Returns
    -------
    Dict[str, Dict[str, int]]
        Nested dictionary mapping ``model_id`` to a mapping of emotion names
        to counts.  Interactions and rituals without a ``model_id`` are
        aggregated under the key ``"unknown"``.
    """
    result: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for inter in interactions:
        key = inter.model_id or "unknown"
        for e in inter.emotions:
            result[key][e.name] += 1
    for rit in rituals:
        key = rit.model_id or "unknown"
        for e in rit.emotions:
            result[key][e.name] += 1
    # Convert defaultdicts to ordinary dicts
    return {k: dict(v) for k, v in result.items()}


def ritual_success_by_emotion(
    rituals: Iterable[RitualOutcome],
) -> Dict[str, Tuple[int, int]]:
    """Compute success counts of rituals conditioned on each emotion.

    For each emotion encountered in ritual outcomes, counts how many times
    rituals were marked successful versus unsuccessful.  Rituals with no
    emotions are ignored.

    Parameters
    ----------
    rituals : Iterable[RitualOutcome]
        Sequence of ritual outcome records.

    Returns
    -------
    Dict[str, Tuple[int, int]]
        Mapping of emotion names to a tuple (success_count, failure_count).
    """
    stats: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    for r in rituals:
        for e in r.emotions:
            if r.success:
                stats[e.name][0] += 1
            else:
                stats[e.name][1] += 1
    return {name: (counts[0], counts[1]) for name, counts in stats.items()}


def generate_insights(
    interactions: List[FamiliarInteraction], rituals: List[RitualOutcome]
) -> List[PatternInsight]:
    """Generate a list of high‑level insights based on the provided data.

    This function analyses the data to produce human‑readable summaries.  Each
    summary is encapsulated in a ``PatternInsight`` instance containing a
    description, metrics and related entities.  The heuristics used here are
    deliberately simple; future versions could incorporate more advanced
    pattern mining or machine learning techniques.

    Parameters
    ----------
    interactions : List[FamiliarInteraction]
        All recorded familiar interactions.
    rituals : List[RitualOutcome]
        All recorded ritual outcomes.

    Returns
    -------
    List[PatternInsight]
        A list of insights ordered by significance (heuristically defined).
    """
    insights: List[PatternInsight] = []

    # Overall emotion frequency
    emotion_counts = aggregate_emotion_counts(interactions, rituals)
    if emotion_counts:
        # Sort emotions by count descending and pick top 3
        top_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        description = (
            "The most frequently experienced emotions across all interactions and rituals "
            f"are: {', '.join([f'{name} ({count})' for name, count in top_emotions])}."
        )
        metrics = {name: float(count) for name, count in emotion_counts.items()}
        related_entities = {"emotions": [name for name, _ in top_emotions]}
        insights.append(
            PatternInsight(
                description=description,
                metrics=metrics,
                related_entities=related_entities,
            )
        )

    # Ritual success rate
    success_rate = compute_success_rate(rituals)
    description = f"Overall ritual success rate is {success_rate * 100:.1f}% across {len(rituals)} rituals."
    metrics = {"success_rate": success_rate, "ritual_count": float(len(rituals))}
    insights.append(
        PatternInsight(
            description=description,
            metrics=metrics,
            related_entities={"rituals": [r.ritual_name for r in rituals]},
        )
    )

    # Emotion by model
    by_model = emotion_counts_by_model(interactions, rituals)
    if len(by_model) > 1:
        # Identify the model with the most distinct emotional palette (most unique emotions)
        model_stats = {model: len(counts) for model, counts in by_model.items()}
        best_model = max(model_stats.items(), key=lambda x: x[1])[0]
        description = (
            f"Model '{best_model}' exhibited the broadest range of emotions ({model_stats[best_model]} unique emotions)."
        )
        metrics = {model: float(len(counts)) for model, counts in by_model.items()}
        insights.append(
            PatternInsight(
                description=description,
                metrics=metrics,
                related_entities={"models": list(by_model.keys())},
            )
        )

    # Success by emotion
    success_by_emotion = ritual_success_by_emotion(rituals)
    if success_by_emotion:
        # Find emotions most associated with successful rituals
        success_ratio = {
            name: (succ / (succ + fail)) if (succ + fail) > 0 else 0.0
            for name, (succ, fail) in success_by_emotion.items()
        }
        top_positive = sorted(success_ratio.items(), key=lambda x: x[1], reverse=True)[:3]
        description = (
            "Emotions most correlated with successful rituals: "
            + ", ".join([f"{name} ({ratio*100:.0f}%)" for name, ratio in top_positive])
            + "."
        )
        metrics = {name: ratio for name, ratio in success_ratio.items()}
        related_entities = {"emotions": [name for name, _ in top_positive]}
        insights.append(
            PatternInsight(
                description=description,
                metrics=metrics,
                related_entities=related_entities,
            )
        )

    return insights