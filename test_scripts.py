"""Unit tests for daily_digest.py and daily_report.py."""

from __future__ import annotations

import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers – stub out the 'requests' module so daily_digest can be imported
# without installing it.
# ---------------------------------------------------------------------------

def _stub_requests() -> None:
    """Insert a minimal requests stub into sys.modules if not already present."""
    if "requests" not in sys.modules:
        stub = types.ModuleType("requests")
        stub.get = MagicMock()   # type: ignore[attr-defined]
        stub.post = MagicMock()  # type: ignore[attr-defined]
        stub.delete = MagicMock()  # type: ignore[attr-defined]
        sys.modules["requests"] = stub


_stub_requests()

import daily_digest  # noqa: E402  (after stub)
import daily_report  # noqa: E402


# ---------------------------------------------------------------------------
# daily_report tests
# ---------------------------------------------------------------------------

class TestGenerateReport(unittest.TestCase):
    def test_contains_date(self) -> None:
        report = daily_report.generate_report()
        # Should contain the current UTC date in ISO-ish format
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.assertIn(today, report)

    def test_contains_metrics(self) -> None:
        report = daily_report.generate_report()
        self.assertIn("Metric A", report)
        self.assertIn("Metric B", report)


# ---------------------------------------------------------------------------
# daily_digest – _target_channels
# ---------------------------------------------------------------------------

def _make_issue(labels: list[str]) -> dict:
    return {"labels": [{"name": n} for n in labels]}


class TestTargetChannels(unittest.TestCase):
    def test_default_is_handoffs(self) -> None:
        issue = _make_issue(["agent-update"])
        self.assertEqual(daily_digest._target_channels(issue), {"handoffs"})

    def test_explicit_handoffs(self) -> None:
        issue = _make_issue(["agent-update", "target:handoffs"])
        self.assertEqual(daily_digest._target_channels(issue), {"handoffs"})

    def test_general(self) -> None:
        issue = _make_issue(["agent-update", "target:general"])
        self.assertEqual(daily_digest._target_channels(issue), {"general"})

    def test_both(self) -> None:
        issue = _make_issue(["agent-update", "target:both"])
        self.assertEqual(daily_digest._target_channels(issue), {"handoffs", "general"})


# ---------------------------------------------------------------------------
# daily_digest – _format_entry
# ---------------------------------------------------------------------------

class TestFormatEntry(unittest.TestCase):
    def _sample_issue(self) -> dict:
        return {
            "title": "Test Update",
            "user": {"login": "agent42"},
            "html_url": "https://github.com/example/repo/issues/1",
            "body": "Short body.",
            "labels": [{"name": "agent-update"}],
        }

    def test_title_in_output(self) -> None:
        entry = daily_digest._format_entry(self._sample_issue())
        self.assertIn("Test Update", entry)

    def test_author_in_output(self) -> None:
        entry = daily_digest._format_entry(self._sample_issue())
        self.assertIn("@agent42", entry)

    def test_url_in_output(self) -> None:
        entry = daily_digest._format_entry(self._sample_issue())
        self.assertIn("https://github.com/example/repo/issues/1", entry)

    def test_body_excerpt(self) -> None:
        entry = daily_digest._format_entry(self._sample_issue())
        self.assertIn("Short body.", entry)

    def test_long_body_truncated(self) -> None:
        issue = self._sample_issue()
        issue["body"] = "x" * 300
        entry = daily_digest._format_entry(issue)
        self.assertIn("…", entry)

    def test_no_body(self) -> None:
        issue = self._sample_issue()
        issue["body"] = None
        # Should not raise
        entry = daily_digest._format_entry(issue)
        self.assertIn("Test Update", entry)


# ---------------------------------------------------------------------------
# daily_digest – _build_digest
# ---------------------------------------------------------------------------

class TestBuildDigest(unittest.TestCase):
    def test_header_present(self) -> None:
        issues = [
            {
                "title": "A",
                "user": {"login": "u"},
                "html_url": "http://x",
                "body": "",
                "labels": [],
            }
        ]
        digest = daily_digest._build_digest(issues)
        self.assertIn("Agent Update Digest", digest)

    def test_separator_between_multiple_issues(self) -> None:
        issues = [
            {
                "title": f"Issue {i}",
                "user": {"login": "u"},
                "html_url": "http://x",
                "body": "",
                "labels": [],
            }
            for i in range(2)
        ]
        digest = daily_digest._build_digest(issues)
        self.assertIn("---", digest)


if __name__ == "__main__":
    unittest.main()
