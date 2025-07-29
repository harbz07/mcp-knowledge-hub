"""MCP server definitions for the Sanctuary MCP Bridge.

This module defines a FastMCP server exposing resources and tools that
allow LLM applications to access Sanctuary data.  Resources provide
read‑only access to interactions, rituals and aggregated insights,
while tools perform actions such as logging new entries.  Structured
output types defined in ``schemas.py`` are used to automatically
generate schemas for the MCP protocol.

To run the server over standard I/O (for example when integrating
with Claude Desktop), execute the module as a script:

```
python -m sanctuary_mcp_bridge.server
```

This will instantiate the server and start a stdio transport.  You can
also embed the server into an existing application by calling
``create_mcp_server()``.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import List, Optional

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "The 'mcp' package is required to run the Sanctuary MCP Bridge. "
        "Install it via `pip install modelcontextprotocol` or see the MCP docs."
    ) from exc

from . import db, patterns
from .schemas import FamiliarInteraction, RitualOutcome, PatternInsight, EmotionIntensity


def create_mcp_server(db_path: Optional[str] = None) -> FastMCP:
    """Create and configure a FastMCP server for the Sanctuary bridge.

    Parameters
    ----------
    db_path : Optional[str]
        Path to the SQLite database.  If ``None``, the default database
        ``sanctuary.db`` in the current working directory will be used.

    Returns
    -------
    FastMCP
        Configured MCP server with registered resources and tools.
    """
    # Ensure the database exists
    db.init_db(db_path)

    mcp = FastMCP(name="Sanctuary MCP Bridge", version="0.1.0")

    # ---- Resources ----

    @mcp.resource("sanctuary://interactions")
    def get_interactions(
        model_id: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[FamiliarInteraction]:
        """Fetch logged familiar interactions.

        Parameters
        ----------
        model_id : Optional[str]
            Filter by originating model identifier.
        start : Optional[str]
            ISO‑8601 timestamp specifying the inclusive start of the range.
        end : Optional[str]
            ISO‑8601 timestamp specifying the inclusive end of the range.

        Returns
        -------
        List[FamiliarInteraction]
            A list of interactions matching the filter criteria.
        """
        start_dt = datetime.fromisoformat(start) if start else None
        end_dt = datetime.fromisoformat(end) if end else None
        interactions = db.get_interactions(model_id=model_id, start=start_dt, end=end_dt, db_path=db_path)
        return interactions

    @mcp.resource("sanctuary://rituals")
    def get_rituals(
        model_id: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[RitualOutcome]:
        """Fetch logged ritual outcomes.

        Parameters
        ----------
        model_id : Optional[str]
            Filter by model identifier.
        start : Optional[str]
            Inclusive start timestamp in ISO‑8601 format.
        end : Optional[str]
            Inclusive end timestamp in ISO‑8601 format.
        """
        start_dt = datetime.fromisoformat(start) if start else None
        end_dt = datetime.fromisoformat(end) if end else None
        return db.get_rituals(model_id=model_id, start=start_dt, end=end_dt, db_path=db_path)

    @mcp.resource("sanctuary://insights")
    def get_insights() -> List[PatternInsight]:
        """Return aggregated pattern insights from all data."""
        interactions = db.get_interactions(db_path=db_path)
        rituals = db.get_rituals(db_path=db_path)
        return patterns.generate_insights(interactions, rituals)

    # ---- Tools ----

    @mcp.tool()
    def log_interaction(
        familiar_id: str,
        interaction_type: str,
        emotions: Optional[List[EmotionIntensity]] = None,
        notes: Optional[str] = None,
        model_id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> int:
        """Record a new familiar interaction.

        Parameters
        ----------
        familiar_id : str
            Identifier of the familiar.
        interaction_type : str
            Brief description of the interaction type.
        emotions : Optional[List[EmotionIntensity]]
            List of emotions experienced during the interaction.
        notes : Optional[str]
            Free‑form notes.
        model_id : Optional[str]
            Identifier of the LLM or agent recording this entry.
        timestamp : Optional[str]
            ISO‑8601 string representing when the interaction occurred.  If
            omitted, the current UTC time will be used.

        Returns
        -------
        int
            The database ID of the newly inserted interaction.
        """
        ts = datetime.fromisoformat(timestamp) if timestamp else datetime.utcnow()
        interaction = FamiliarInteraction(
            timestamp=ts,
            familiar_id=familiar_id,
            interaction_type=interaction_type,
            emotions=emotions or [],
            notes=notes,
            model_id=model_id,
        )
        return db.add_interaction(interaction, db_path=db_path)

    @mcp.tool()
    def log_ritual(
        ritual_name: str,
        success: bool,
        emotions: Optional[List[EmotionIntensity]] = None,
        outcome_description: Optional[str] = None,
        notes: Optional[str] = None,
        model_id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> int:
        """Record a new ritual outcome.

        Parameters
        ----------
        ritual_name : str
            Name or identifier of the ritual.
        success : bool
            Whether the ritual achieved its intention.
        emotions : Optional[List[EmotionIntensity]]
            Emotions experienced as part of the ritual.
        outcome_description : Optional[str]
            Summary of what happened during or after the ritual.
        notes : Optional[str]
            Additional free‑form notes.
        model_id : Optional[str]
            Identifier of the agent recording this outcome.
        timestamp : Optional[str]
            ISO‑8601 timestamp; if omitted, uses current UTC time.

        Returns
        -------
        int
            Database ID of the newly inserted ritual.
        """
        ts = datetime.fromisoformat(timestamp) if timestamp else datetime.utcnow()
        outcome = RitualOutcome(
            timestamp=ts,
            ritual_name=ritual_name,
            success=success,
            outcome_description=outcome_description,
            emotions=emotions or [],
            notes=notes,
            model_id=model_id,
        )
        return db.add_ritual(outcome, db_path=db_path)

    @mcp.tool()
    def query_emotions_by_model() -> dict[str, dict[str, int]]:
        """Return emotion counts grouped by model identifier."""
        interactions = db.get_interactions(db_path=db_path)
        rituals = db.get_rituals(db_path=db_path)
        return patterns.emotion_counts_by_model(interactions, rituals)

    @mcp.tool()
    def query_ritual_insights(
        ritual_name: str,
        model_id: Optional[str] = None,
    ) -> List[PatternInsight]:
        """Generate insights for a specific ritual.

        Parameters
        ----------
        ritual_name : str
            Name of the ritual to analyse.
        model_id : Optional[str]
            Restrict analysis to rituals logged by a specific model.  If
            omitted, all rituals with the given name are considered.

        Returns
        -------
        List[PatternInsight]
            Insights derived from the subset of rituals.  If no matching
            records are found, an empty list is returned.
        """
        # Filter rituals by name and model
        rituals = [
            r
            for r in db.get_rituals(model_id=model_id, db_path=db_path)
            if r.ritual_name == ritual_name
        ]
        if not rituals:
            return []
        # Interactions are not relevant for ritual‑specific insights
        return patterns.generate_insights([], rituals)

    return mcp


async def _run_stdio(server: FastMCP) -> None:
    """Run the server over standard input/output.

    This coroutine should be awaited in an asyncio event loop.  It starts
    the server using the stdio transport provided by FastMCP.
    """
    await server.run_stdio()


def main() -> None:  # pragma: no cover
    """Entry point for running the server via `python -m`.

    This function creates a server with the default database and runs it
    using stdio.  It will block until the connection is closed.  If you
    need to integrate the server into an existing event loop, call
    ``create_mcp_server()`` directly instead of using this entry point.
    """
    server = create_mcp_server()
    asyncio.run(_run_stdio(server))


if __name__ == "__main__":  # pragma: no cover
    main()