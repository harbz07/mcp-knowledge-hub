import unittest

from daily_digest import (
    LABEL_TARGET_BOTH,
    LABEL_TARGET_GENERAL,
    _target_channels,
)


class TargetChannelsTests(unittest.TestCase):
    def test_routes_by_target_label(self) -> None:
        issue = {"labels": [{"name": LABEL_TARGET_GENERAL}], "body": ""}
        self.assertEqual(_target_channels(issue), {"general"})

    def test_routes_by_form_target_when_target_labels_missing(self) -> None:
        issue = {
            "labels": [{"name": "agent-update"}],
            "body": "### Target Channel\n\ngeneral",
        }
        self.assertEqual(_target_channels(issue), {"general"})

    def test_routes_to_both_from_form_target(self) -> None:
        issue = {"labels": [], "body": "### Target Channel\n\nboth"}
        self.assertEqual(_target_channels(issue), {"handoffs", "general"})

    def test_label_precedence_over_body_target(self) -> None:
        issue = {
            "labels": [{"name": LABEL_TARGET_BOTH}],
            "body": "### Target Channel\n\ngeneral",
        }
        self.assertEqual(_target_channels(issue), {"handoffs", "general"})


if __name__ == "__main__":
    unittest.main()
