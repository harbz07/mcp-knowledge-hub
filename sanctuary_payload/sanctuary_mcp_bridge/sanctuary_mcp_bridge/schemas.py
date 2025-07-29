"""Data schemas for Sanctuary MCP Bridge.

This module defines structured representations for the core entities used by
the Sanctuary spiritual ecosystem.  Using Pydantic models ensures that
incoming data from LLM clients and internal components is validated and
documented.  These models can be used directly as return types for MCP
resources and tools, enabling automatic schema generation and validation by
the MCP SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field, validator


class EmotionIntensity(BaseModel):
    """Represents a single emotional state with an associated intensity.

    Attributes
    ----------
    name : str
        The name of the emotion (e.g. "joy", "sadness", "gratitude").
    intensity : float
        A normalized score between 0 and 1 indicating how strong the
        emotion was experienced.  0 means absent, 1 means overwhelming.
    """

    name: str = Field(..., description="Name of the emotion")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Intensity on a 0–1 scale")


class FamiliarInteraction(BaseModel):
    """A log entry representing a familiar interaction.

    Familiar interactions are one of the core building blocks of the
    Sanctuary practice.  A familiar might be a metaphorical guide, a
    recurring character in a dream, or any anthropomorphised archetype
    that you engage with during meditation or ritual.  Recording these
    interactions allows different LLMs to build up a shared history and
    recall meaningful details across sessions.

    Attributes
    ----------
    timestamp : datetime
        When the interaction took place.  Timestamps should be in UTC to
        avoid ambiguity across time zones.
    familiar_id : str
        A unique identifier for the familiar (e.g. "owl", "gardener").
    interaction_type : str
        A short description of the interaction (e.g. "vision", "conversation",
        "intuition").
    emotions : List[EmotionIntensity]
        A list of emotional states experienced during the interaction.
    notes : Optional[str]
        Free‑form notes describing details of the experience.  Use this to
        capture narrative information that cannot easily be encoded in
        structured fields.
    model_id : Optional[str]
        (Optional) Identifier for the LLM or source agent that facilitated
        logging this interaction.  If multiple models are used, this field
        helps correlate patterns across LLMs.
    """

    timestamp: datetime = Field(..., description="UTC timestamp of the interaction")
    familiar_id: str = Field(..., description="Identifier of the familiar")
    interaction_type: str = Field(..., description="Type of interaction, e.g. vision, conversation")
    emotions: List[EmotionIntensity] = Field(default_factory=list, description="List of emotions with intensities")
    notes: Optional[str] = Field(None, description="Free form notes about the interaction")
    model_id: Optional[str] = Field(None, description="Identifier of the LLM or agent that recorded this entry")

    @validator("timestamp", pre=True)
    def parse_timestamp(cls, value):
        """Allow timestamp to be provided as ISO string or numeric epoch.

        MCP clients may send timestamps as ISO8601 strings.  This validator
        ensures that such strings are converted to ``datetime`` objects.
        """
        if isinstance(value, (int, float)):
            return datetime.utcfromtimestamp(value)
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value


class RitualOutcome(BaseModel):
    """A log entry representing the outcome of a ritual.

    Rituals are intentional ceremonies or practices performed within the
    Sanctuary.  Tracking outcomes helps refine the practice and supports
    pattern recognition across different contexts and agents.

    Attributes
    ----------
    timestamp : datetime
        When the ritual occurred.
    ritual_name : str
        Name or identifier of the ritual (e.g. "new moon meditation").
    success : bool
        Whether the ritual achieved its intended outcome.  Success can be
        subjective; this field captures the practitioner's assessment.
    outcome_description : Optional[str]
        A brief description of what happened during or after the ritual.
    emotions : List[EmotionIntensity]
        Emotional states experienced as a result of the ritual.
    notes : Optional[str]
        Additional details about the ritual that are relevant for future
        reference.
    model_id : Optional[str]
        Identifier for the model or agent that recorded the outcome.
    """

    timestamp: datetime = Field(..., description="UTC timestamp of the ritual")
    ritual_name: str = Field(..., description="Name of the ritual")
    success: bool = Field(..., description="Whether the ritual met its intention")
    outcome_description: Optional[str] = Field(None, description="Brief description of the ritual's outcome")
    emotions: List[EmotionIntensity] = Field(default_factory=list, description="Emotional states experienced")
    notes: Optional[str] = Field(None, description="Additional notes about the ritual")
    model_id: Optional[str] = Field(None, description="Identifier of the LLM or agent that recorded this entry")

    @validator("timestamp", pre=True)
    def parse_timestamp(cls, value):
        if isinstance(value, (int, float)):
            return datetime.utcfromtimestamp(value)
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value


class PatternInsight(BaseModel):
    """Represents an aggregated insight or pattern discovered from logged data.

    When analysing interactions and rituals, the pattern recognition module
    returns structured insights such as frequently co‑occurring emotions,
    success rates of rituals, or correlations between LLMs and outcomes.

    Attributes
    ----------
    description : str
        Human‑friendly summary of the pattern.
    metrics : dict[str, float]
        Numeric metrics associated with the pattern (e.g. frequency counts,
        percentages).  The keys are descriptive labels.
    related_entities : Optional[dict[str, list[str]]]
        Mapping of entity types (e.g. "rituals", "emotions", "models") to
        lists of identifiers involved in the pattern.
    """

    description: str = Field(..., description="Summary of the pattern")
    metrics: dict[str, float] = Field(default_factory=dict, description="Associated numeric metrics")
    related_entities: Optional[dict[str, List[str]]] = Field(None, description="Entities related to the insight")