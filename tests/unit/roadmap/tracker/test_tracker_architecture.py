from types import SimpleNamespace
import unittest

from roadmap.tracker.architecture import ArchitectureSnapshot


class ArchitectureSnapshotTests(unittest.TestCase):
    def test_snapshot_is_deterministic_and_dynamic(self):
        metadata = SimpleNamespace(title="NPP", version="1")
        milestone = SimpleNamespace(
            record_id="npp-rm-one",
            number="M001",
            title="Changed Architecture Title",
            status=SimpleNamespace(value="COMPLETED"),
            sequence=1,
            depth=0,
            parent_number=None,
        )
        snapshot = ArchitectureSnapshot.from_roadmap(
            SimpleNamespace(metadata=metadata, milestones=(milestone,))
        )
        self.assertEqual(snapshot.require_record("npp-rm-one").title, "Changed Architecture Title")
        self.assertEqual(snapshot.completed, 1)
        self.assertEqual(snapshot.percentage, 100.0)


if __name__ == "__main__":
    unittest.main()
