import unittest

from roadmap.tracker.files import detect_previous_milestone_impacts
from roadmap.tracker.models import (
    FileEvidence, TrackerRecord, TrackerRecordKind, TrackerStatus
)


class FileImpactTests(unittest.TestCase):
    def test_previous_owner_is_reported(self):
        record = TrackerRecord(
            tracker_id="npp-trk-current",
            kind=TrackerRecordKind.TRACKER_MILESTONE,
            title="Current work",
            status=TrackerStatus.IN_PROGRESS,
            created_at="2026-07-24T13:00:00+02:00",
            updated_at="2026-07-24T13:00:00+02:00",
            display_number="M009",
            files=(
                FileEvidence(
                    path="shared/events/model.py",
                    action="MODIFIED",
                    owning_record_id="npp-rm-m006",
                    reason="Registry compatibility",
                ),
            ),
        )
        impacts = detect_previous_milestone_impacts((record,))
        self.assertEqual(len(impacts), 1)
        self.assertEqual(impacts[0].owning_record_id, "npp-rm-m006")


if __name__ == "__main__":
    unittest.main()
