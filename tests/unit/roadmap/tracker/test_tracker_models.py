import unittest

from roadmap.tracker.models import (
    TrackerModelError, TrackerRecord, TrackerRecordKind, TrackerStatus
)


class TrackerModelTests(unittest.TestCase):
    def test_architecture_record_rejects_copied_title(self):
        with self.assertRaises(TrackerModelError):
            TrackerRecord(
                tracker_id="npp-trk-1",
                kind=TrackerRecordKind.ARCHITECTURE,
                title="Copied title",
                status=TrackerStatus.PLANNED,
                created_at="2026-07-24T13:00:00+02:00",
                updated_at="2026-07-24T13:00:00+02:00",
                architecture_record_id="npp-rm-one",
            )

    def test_extension_requires_segment(self):
        with self.assertRaises(TrackerModelError):
            TrackerRecord(
                tracker_id="npp-trk-2",
                kind=TrackerRecordKind.EXTENSION,
                title="Extension",
                status=TrackerStatus.PLANNED,
                created_at="2026-07-24T13:00:00+02:00",
                updated_at="2026-07-24T13:00:00+02:00",
                architecture_record_id="npp-rm-one",
            )


if __name__ == "__main__":
    unittest.main()
