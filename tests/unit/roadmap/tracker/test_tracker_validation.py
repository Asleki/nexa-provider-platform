from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from roadmap.tracker.architecture import ArchitectureSnapshot
from roadmap.tracker.generator import write_tracker
from roadmap.tracker.validation import validate_synchronization


class SynchronizationTests(unittest.TestCase):
    def test_generated_tracker_matches_roadmap_digest(self):
        m = SimpleNamespace(
            record_id="npp-rm-one", number="M001", title="One", status="COMPLETED",
            sequence=1, depth=0, parent_number=None
        )
        architecture = ArchitectureSnapshot.from_roadmap(
            SimpleNamespace(metadata=SimpleNamespace(title="NPP", version="1"), milestones=(m,))
        )
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            roadmap = directory / "ROADMAP.md"
            tracker = directory / "ROADMAP_TRACKER.md"
            roadmap.write_text("# Roadmap\n", encoding="utf-8")
            write_tracker(
                architecture, (), generated_at="2026-07-24T13:00:00+02:00",
                roadmap_path=roadmap, output=tracker
            )
            report = validate_synchronization(
                architecture=architecture, roadmap_path=roadmap, tracker_path=tracker
            )
            self.assertTrue(report.is_valid)


if __name__ == "__main__":
    unittest.main()
