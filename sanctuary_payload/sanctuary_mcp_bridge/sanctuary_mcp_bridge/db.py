"""SQLite persistence layer for the Sanctuary MCP Bridge.

This module provides functions to initialise a local SQLite database, persist
familiar interactions and ritual outcomes, and retrieve records for further
processing.  Storing data in a structured database makes it easy for LLM
clients to query historical information through the MCP server.

The database schema consists of two tables:

* interactions: records individual interactions with familiars.  Each entry
  stores the timestamp, familiar identifier, type, a JSON representation of
  emotions, free‑form notes and the originating model identifier.

* rituals: records ritual outcomes.  Each entry stores the timestamp,
  ritual name, success flag, outcome description, a JSON representation of
  emotions, notes and the originating model identifier.

The JSON encoding for emotional lists uses standard Python ``json`` library
and is opaque to the database.  See ``schemas.py`` for the corresponding
Pydantic models.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from .schemas import EmotionIntensity, FamiliarInteraction, RitualOutcome


DB_NAME = "sanctuary.db"


def _get_db_path(db_path: Optional[str] = None) -> Path:
    """Return the absolute path to the database file.

    If ``db_path`` is provided, it is resolved relative to the current
    working directory.  Otherwise, a file named ``sanctuary.db`` is placed
    in the current working directory.
    """
    if db_path is not None:
        return Path(db_path).expanduser().resolve()
    return Path(DB_NAME).resolve()


@contextmanager
def get_connection(db_path: Optional[str] = None) -> Iterable[sqlite3.Connection]:
    """Context manager that yields a SQLite connection and closes it on exit.

    Parameters
    ----------
    db_path : Optional[str]
        Path to the SQLite database file.  If ``None``, the default
        database name ``sanctuary.db`` is used in the working directory.

    Yields
    ------
    sqlite3.Connection
        An open connection to the SQLite database.
    """
    path = _get_db_path(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: Optional[str] = None) -> None:
    """Initialise the SQLite database with required tables.

    This function creates the ``interactions`` and ``rituals`` tables if
    they do not already exist.  It is idempotent and can be run multiple
    times without affecting existing data.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                familiar_id TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                emotions TEXT NOT NULL,
                notes TEXT,
                model_id TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rituals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                ritual_name TEXT NOT NULL,
                success INTEGER NOT NULL,
                outcome_description TEXT,
                emotions TEXT NOT NULL,
                notes TEXT,
                model_id TEXT
            )
            """
        )
        conn.commit()


def _serialize_emotions(emotions: Sequence[EmotionIntensity]) -> str:
    """Serialize a sequence of ``EmotionIntensity`` objects into a JSON string."""
    return json.dumps([e.dict() for e in emotions], ensure_ascii=False)


def _deserialize_emotions(data: str) -> List[EmotionIntensity]:
    """Deserialize a JSON string into a list of ``EmotionIntensity`` objects."""
    if not data:
        return []
    try:
        raw = json.loads(data)
    except Exception:
        return []
    return [EmotionIntensity(**item) for item in raw]


def add_interaction(interaction: FamiliarInteraction, db_path: Optional[str] = None) -> int:
    """Insert a familiar interaction into the database.

    Parameters
    ----------
    interaction : FamiliarInteraction
        The interaction record to persist.
    db_path : Optional[str]
        Optional path to a specific database file.

    Returns
    -------
    int
        The ID of the newly inserted row.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        emotions_json = _serialize_emotions(interaction.emotions)
        cur.execute(
            """
            INSERT INTO interactions (timestamp, familiar_id, interaction_type, emotions, notes, model_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                interaction.timestamp.isoformat(),
                interaction.familiar_id,
                interaction.interaction_type,
                emotions_json,
                interaction.notes,
                interaction.model_id,
            ),
        )
        conn.commit()
        return cur.lastrowid


def add_ritual(outcome: RitualOutcome, db_path: Optional[str] = None) -> int:
    """Insert a ritual outcome into the database.

    Parameters
    ----------
    outcome : RitualOutcome
        The ritual outcome to persist.
    db_path : Optional[str]
        Optional path to a specific database file.

    Returns
    -------
    int
        The ID of the newly inserted row.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        emotions_json = _serialize_emotions(outcome.emotions)
        cur.execute(
            """
            INSERT INTO rituals (timestamp, ritual_name, success, outcome_description, emotions, notes, model_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                outcome.timestamp.isoformat(),
                outcome.ritual_name,
                1 if outcome.success else 0,
                outcome.outcome_description,
                emotions_json,
                outcome.notes,
                outcome.model_id,
            ),
        )
        conn.commit()
        return cur.lastrowid


def get_interactions(
    model_id: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    db_path: Optional[str] = None,
) -> List[FamiliarInteraction]:
    """Retrieve familiar interactions from the database.

    The caller can optionally filter by model identifier and/or a date range.

    Parameters
    ----------
    model_id : Optional[str]
        If provided, only records originating from this model will be returned.
    start : Optional[datetime]
        If provided, only records occurring on or after this timestamp will be
        returned.
    end : Optional[datetime]
        If provided, only records occurring on or before this timestamp will be
        returned.
    db_path : Optional[str]
        Optional path to a specific database file.

    Returns
    -------
    List[FamiliarInteraction]
        A list of interaction records.
    """
    query = "SELECT * FROM interactions WHERE 1=1"
    params: List[object] = []
    if model_id is not None:
        query += " AND model_id = ?"
        params.append(model_id)
    if start is not None:
        query += " AND timestamp >= ?"
        params.append(start.isoformat())
    if end is not None:
        query += " AND timestamp <= ?"
        params.append(end.isoformat())
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        rows = cur.execute(query, params).fetchall()
    interactions: List[FamiliarInteraction] = []
    for row in rows:
        emotions = _deserialize_emotions(row["emotions"])
        interactions.append(
            FamiliarInteraction(
                timestamp=datetime.fromisoformat(row["timestamp"]),
                familiar_id=row["familiar_id"],
                interaction_type=row["interaction_type"],
                emotions=emotions,
                notes=row["notes"],
                model_id=row["model_id"],
            )
        )
    return interactions


def get_rituals(
    model_id: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    db_path: Optional[str] = None,
) -> List[RitualOutcome]:
    """Retrieve ritual outcomes from the database with optional filtering.

    Parameters
    ----------
    model_id : Optional[str]
        Filter by originating model identifier.
    start : Optional[datetime]
        Return rituals occurring on or after this timestamp.
    end : Optional[datetime]
        Return rituals occurring on or before this timestamp.
    db_path : Optional[str]
        Path to a specific database file.

    Returns
    -------
    List[RitualOutcome]
        List of ritual outcome records.
    """
    query = "SELECT * FROM rituals WHERE 1=1"
    params: List[object] = []
    if model_id is not None:
        query += " AND model_id = ?"
        params.append(model_id)
    if start is not None:
        query += " AND timestamp >= ?"
        params.append(start.isoformat())
    if end is not None:
        query += " AND timestamp <= ?"
        params.append(end.isoformat())
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        rows = cur.execute(query, params).fetchall()
    rituals: List[RitualOutcome] = []
    for row in rows:
        emotions = _deserialize_emotions(row["emotions"])
        rituals.append(
            RitualOutcome(
                timestamp=datetime.fromisoformat(row["timestamp"]),
                ritual_name=row["ritual_name"],
                success=bool(row["success"]),
                outcome_description=row["outcome_description"],
                emotions=emotions,
                notes=row["notes"],
                model_id=row["model_id"],
            )
        )
    return rituals