from types import SimpleNamespace
import unittest

from roadmap.tracker.architecture import ArchitectureSnapshot
from roadmap.tracker.dashboard import render_record_cards
from roadmap.tracker.extensions import resolve_display_numbers
from roadmap.tracker.models import (
    TrackerRecord,
    TrackerRecordKind,
    TrackerStatus,
)


class TrackerDashboardTests(unittest.TestCase):
    def test_architecture_linked_card_uses_canonical_status_icon(self):
        milestone = SimpleNamespace(
            record_id="npp-rm-m008",
            number="M008",
            title="Master Registry Foundation",
            status=SimpleNamespace(value="PLANNED"),
            sequence=8,
            depth=0,
            parent_number=None,
        )

        architecture = ArchitectureSnapshot.from_roadmap(
            SimpleNamespace(
                metadata=SimpleNamespace(
                    title="Nexa Provider Platform",
                    version="1",
                ),
                milestones=(milestone,),
            )
        )

        record = TrackerRecord(
            tracker_id="npp-trk-m008-render-test",
            kind=TrackerRecordKind.ARCHITECTURE,
            title=None,
            description=(
                "Tests canonical architecture rendering authority."
            ),
            status=TrackerStatus.COMPLETED,
            architecture_record_id="npp-rm-m008",
            parent_tracker_id=None,
            created_at="2026-07-24T13:00:00+00:00",
            updated_at="2026-07-24T14:00:00+00:00",
            commits=(),
            files=(),
            tests=(),
            notes=(),
        )

        records = (record,)
        numbers = resolve_display_numbers(
            architecture,
            records,
        )

        rendered = "\n".join(
            render_record_cards(
                architecture,
                records,
                numbers,
            )
        )

        self.assertIn(
            "### 🟦 M008 — Master Registry Foundation",
            rendered,
        )
        self.assertIn(
            "> **Canonical status:** Planned",
            rendered,
        )
        self.assertIn(
            "> **Tracker execution status:** Completed",
            rendered,
        )
        self.assertNotIn(
            "### ✅ M008 — Master Registry Foundation",
            rendered,
        )

    def test_tracker_only_card_uses_tracker_status_icon(self):
        milestone = SimpleNamespace(
            record_id="npp-rm-m008",
            number="M008",
            title="Master Registry Foundation",
            status=SimpleNamespace(value="PLANNED"),
            sequence=8,
            depth=0,
            parent_number=None,
        )

        architecture = ArchitectureSnapshot.from_roadmap(
            SimpleNamespace(
                metadata=SimpleNamespace(
                    title="Nexa Provider Platform",
                    version="1",
                ),
                milestones=(milestone,),
            )
        )

        record = TrackerRecord(
            tracker_id="npp-trk-m008-extension-one",
            kind=TrackerRecordKind.EXTENSION,
            title="Registry Validation Extension",
            description="Tracker-only engineering extension.",
            status=TrackerStatus.COMPLETED,
            architecture_record_id="npp-rm-m008",
            local_segment=1,
            parent_tracker_id=None,
            created_at="2026-07-24T13:00:00+00:00",
            updated_at="2026-07-24T14:00:00+00:00",
            commits=(),
            files=(),
            tests=(),
            notes=(),
        )

        records = (record,)
        numbers = resolve_display_numbers(
            architecture,
            records,
        )

        rendered = "\n".join(
            render_record_cards(
                architecture,
                records,
                numbers,
            )
        )

        self.assertIn(
            "✅",
            rendered,
        )
        self.assertIn(
            "Registry Validation Extension",
            rendered,
        )
        self.assertIn(
            "> **Status:** Completed",
            rendered,
        )
        self.assertNotIn(
            "> **Canonical status:**",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()