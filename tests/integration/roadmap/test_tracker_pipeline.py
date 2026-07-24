from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from roadmap.tracker.architecture import ArchitectureSnapshot
from roadmap.tracker.engine import TrackerEngine
from roadmap.tracker.storage import TrackerStore


class TrackerPipelineTests(unittest.TestCase):
    def test_engine_builds_root_tracker_file(self):
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
            output = directory / "ROADMAP_TRACKER.md"
            roadmap.write_text("# Roadmap\n", encoding="utf-8")
            engine = TrackerEngine(TrackerStore(directory / "data" / "records.json"))
            result = engine.build(
                architecture,
                roadmap_path=roadmap,
                output=output,
                generated_at="2026-07-24T13:00:00+02:00",
            )
            self.assertTrue(output.exists())
            self.assertTrue(result.validation.is_valid)


if __name__ == "__main__":
    unittest.main()
