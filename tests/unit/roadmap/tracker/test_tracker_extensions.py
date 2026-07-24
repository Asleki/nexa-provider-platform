from types import SimpleNamespace
import unittest

from roadmap.tracker.architecture import ArchitectureSnapshot
from roadmap.tracker.extensions import resolve_display_numbers
from roadmap.tracker.models import TrackerRecord, TrackerRecordKind, TrackerStatus


class ExtensionTests(unittest.TestCase):
    def setUp(self):
        m = SimpleNamespace(
            record_id="npp-rm-m008-13", number="M008.13", title="Registry Tests",
            status="PLANNED", sequence=1, depth=1, parent_number="M008"
        )
        self.architecture = ArchitectureSnapshot.from_roadmap(
            SimpleNamespace(metadata=SimpleNamespace(title="NPP", version="1"), milestones=(m,))
        )

    def test_extension_number_uses_current_architecture_number(self):
        record = TrackerRecord(
            tracker_id="npp-trk-ext-1",
            kind=TrackerRecordKind.EXTENSION,
            title="Contract Tests",
            status=TrackerStatus.COMPLETED,
            created_at="2026-07-24T13:00:00+02:00",
            updated_at="2026-07-24T14:00:00+02:00",
            architecture_record_id="npp-rm-m008-13",
            local_segment=1,
        )
        numbers = resolve_display_numbers(self.architecture, (record,))
        self.assertEqual(numbers[record.tracker_id], "M008.13.1")


if __name__ == "__main__":
    unittest.main()
