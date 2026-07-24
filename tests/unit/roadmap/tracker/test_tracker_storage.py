from pathlib import Path
import tempfile
import unittest

from roadmap.tracker.models import TrackerRecord, TrackerRecordKind, TrackerStatus
from roadmap.tracker.storage import TrackerStore, TrackerStorageError


class StorageTests(unittest.TestCase):
    def test_round_trip(self):
        record = TrackerRecord(
            tracker_id="npp-trk-1",
            kind=TrackerRecordKind.TRACKER_MILESTONE,
            title="Operational hardening",
            status=TrackerStatus.PLANNED,
            created_at="2026-07-24T13:00:00+02:00",
            updated_at="2026-07-24T13:00:00+02:00",
            display_number="M009",
        )
        with tempfile.TemporaryDirectory() as directory:
            store = TrackerStore(Path(directory) / "records.json")
            store.save((record,))
            loaded = store.load()
            self.assertEqual(loaded, (record,))

    def test_protected_architecture_filename(self):
        with self.assertRaises(TrackerStorageError):
            TrackerStore(Path("ROADMAP.md"))


if __name__ == "__main__":
    unittest.main()
