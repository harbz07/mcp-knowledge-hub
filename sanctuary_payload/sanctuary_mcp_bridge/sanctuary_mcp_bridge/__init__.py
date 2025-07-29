"""Top‑level package for the Sanctuary MCP Bridge.

This package exposes utilities for connecting the Sanctuary spiritual ecosystem
to the Model Context Protocol (MCP).  It defines data schemas, persistence
helpers and an MCP server that exposes resources and tools for logging and
querying spiritual interactions.

The MCP integration is intentionally lightweight and modular so that it can
easily be plugged into an existing Sanctuary dashboard or reused by other
applications.  See the documentation in the accompanying report for details
on how to run the server and integrate it into your practice.
"""

from importlib.metadata import version as _version


__all__ = [
    "get_version",
]


def get_version() -> str:
    """Return the package version string.

    If the package metadata is unavailable (for example when installed from a
    source tree without a proper distribution), this function returns "0.0.0".

    Returns
    -------
    str
        The version string.
    """
    try:
        return _version(__name__)
    except Exception:
        return "0.0.0"