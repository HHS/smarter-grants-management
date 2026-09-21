import uuid
from datetime import datetime, timezone

import pytest

from src.constants.lookup_constants import AnnouncementAuditEvent
from tests.db.models.factories import AnnouncementAuditFactory, AnnouncementFactory

API_URL = "/v1/announcements"

DEFAULT_PAGINATION = {"pagination": {"page_offset": 1, "page_size": 25}}


def _make_datetime(hour: int) -> datetime:
    return datetime(2026, 7, 1, hour, 0, 0, tzinfo=timezone.utc)


####################################
# Fixtures
####################################


@pytest.fixture
def announcement(enable_factory_create):
    return AnnouncementFactory.create()


####################################
# 200 Tests
####################################


class TestAnnouncementAuditEvents200:

    def test_audit_events_empty_200(self, client, db_session, api_key_headers, announcement):
        """No audit rows returns an empty list"""
        resp = client.post(
            f"{API_URL}/{announcement.announcement_id}/audit_events",
            headers=api_key_headers,
            json=DEFAULT_PAGINATION,
        )

        assert resp.status_code == 200
        assert resp.get_json()["data"] == []
        assert resp.get_json()["pagination_info"]["total_records"] == 0
        assert resp.get_json()["pagination_info"]["total_pages"] == 0

    def test_audit_events_all_event_types_200(
        self, client, db_session, api_key_headers, announcement
    ):
        """Returns every related-record type in descending order with the right nested data"""
        created = AnnouncementAuditFactory.create(
            announcement=announcement,
            announcement_audit_event=AnnouncementAuditEvent.ANNOUNCEMENT_CREATED,
            created_at=_make_datetime(hour=1),
        )
        summary_event = AnnouncementAuditFactory.create(
            announcement=announcement, is_summary_event=True, created_at=_make_datetime(hour=2)
        )
        attachment_event = AnnouncementAuditFactory.create(
            announcement=announcement, is_attachment_event=True, created_at=_make_datetime(hour=3)
        )
        package_event = AnnouncementAuditFactory.create(
            announcement=announcement, is_package_event=True, created_at=_make_datetime(hour=4)
        )
        instruction_event = AnnouncementAuditFactory.create(
            announcement=announcement, is_instruction_event=True, created_at=_make_datetime(hour=5)
        )

        events_asc = [created, summary_event, attachment_event, package_event, instruction_event]

        resp = client.post(
            f"{API_URL}/{announcement.announcement_id}/audit_events",
            headers=api_key_headers,
            json=DEFAULT_PAGINATION,
        )

        assert resp.status_code == 200
        results = resp.json["data"]
        assert len(results) == 5

        # Default sort is descending by created_at
        for result, event in zip(results, events_asc[::-1], strict=True):
            assert result["announcement_audit_id"] == str(event.announcement_audit_id)
            assert result["announcement_audit_event"] == event.announcement_audit_event
            assert result["created_at"] == event.created_at.isoformat()
            assert result["user"] == {"user_id": str(event.user_id), "email": event.user.email}

        results_by_id = {r["announcement_audit_id"]: r for r in results}

        summary_result = results_by_id[str(summary_event.announcement_audit_id)]
        assert summary_result["announcement_summary"]["announcement_summary_id"] == str(
            summary_event.announcement_summary_id
        )
        assert summary_result["announcement_attachment"] is None
        assert summary_result["application_package"] is None
        assert summary_result["application_package_instruction"] is None

        attachment_result = results_by_id[str(attachment_event.announcement_audit_id)]
        assert attachment_result["announcement_attachment"]["announcement_attachment_id"] == str(
            attachment_event.announcement_attachment_id
        )
        assert (
            attachment_result["announcement_attachment"]["file_name"]
            == attachment_event.announcement_attachment.file_attachment.file_name
        )
        assert attachment_result["announcement_summary"] is None

        package_result = results_by_id[str(package_event.announcement_audit_id)]
        assert package_result["application_package"]["application_package_id"] == str(
            package_event.application_package_id
        )
        assert package_result["announcement_summary"] is None

        instruction_result = results_by_id[str(instruction_event.announcement_audit_id)]
        assert instruction_result["application_package_instruction"][
            "application_package_instruction_id"
        ] == str(instruction_event.application_package_instruction_id)
        assert (
            instruction_result["application_package_instruction"]["file_name"]
            == instruction_event.application_package_instruction.file_attachment.file_name
        )
        assert instruction_result["announcement_summary"] is None

        pagination = resp.get_json()["pagination_info"]
        assert pagination["total_records"] == 5
        assert pagination["sort_order"] == [
            {"order_by": "created_at", "sort_direction": "descending"}
        ]

    def test_audit_events_filter_event_200(self, client, db_session, api_key_headers, announcement):
        """Filtering by event type returns only matching rows"""
        events_map = {
            AnnouncementAuditEvent.ANNOUNCEMENT_CREATED: AnnouncementAuditFactory.create(
                announcement=announcement,
                announcement_audit_event=AnnouncementAuditEvent.ANNOUNCEMENT_CREATED,
            ),
            AnnouncementAuditEvent.ANNOUNCEMENT_UPDATED: AnnouncementAuditFactory.create(
                announcement=announcement,
                announcement_audit_event=AnnouncementAuditEvent.ANNOUNCEMENT_UPDATED,
            ),
        }

        scenarios = [
            list(events_map.keys()),
            [AnnouncementAuditEvent.ANNOUNCEMENT_CREATED],
        ]

        for event_group in scenarios:
            resp = client.post(
                f"{API_URL}/{announcement.announcement_id}/audit_events",
                headers=api_key_headers,
                json={
                    "pagination": {"page_offset": 1, "page_size": 25},
                    "filters": {"announcement_audit_event": {"one_of": event_group}},
                },
            )

            assert resp.status_code == 200
            results = resp.json["data"]

            result_ids = {r["announcement_audit_id"] for r in results}
            expected_ids = {
                str(events_map[event_type].announcement_audit_id) for event_type in event_group
            }

            assert len(result_ids) == len(expected_ids)
            assert result_ids == expected_ids

    def test_audit_events_pagination_200(self, client, db_session, api_key_headers, announcement):
        """Pagination and sort order work correctly"""

        # Create 9 events with descending timestamps to match default descending sort
        audit_events = []
        for i in range(9, 0, -1):
            audit_events.append(
                AnnouncementAuditFactory.create(
                    announcement=announcement, created_at=_make_datetime(hour=i)
                )
            )

        scenarios = [
            # Fetch all (descending)
            ({"page_offset": 1, "page_size": 25}, audit_events),
            # Ascending sort
            (
                {
                    "page_offset": 1,
                    "page_size": 25,
                    "sort_order": [{"order_by": "created_at", "sort_direction": "ascending"}],
                },
                audit_events[::-1],
            ),
            # Second page of 3
            ({"page_offset": 2, "page_size": 3}, audit_events[3:6]),
            # Past the end
            ({"page_offset": 10, "page_size": 10}, []),
        ]

        for pagination, expected_events in scenarios:
            resp = client.post(
                f"{API_URL}/{announcement.announcement_id}/audit_events",
                headers=api_key_headers,
                json={"pagination": pagination},
            )

            assert resp.status_code == 200
            result_ids = [r["announcement_audit_id"] for r in resp.json["data"]]
            expected_ids = [str(e.announcement_audit_id) for e in expected_events]
            assert result_ids == expected_ids, f"Mismatch for pagination {pagination}"


####################################
# 401 Tests
####################################


class TestAnnouncementAuditEvents401:

    def test_audit_events_bad_api_key_401(self, client):
        resp = client.post(
            f"{API_URL}/{uuid.uuid4()}/audit_events",
            headers={"X-API-Key": "bad key"},
            json=DEFAULT_PAGINATION,
        )

        assert resp.status_code == 401

    def test_audit_events_no_api_key_401(self, client):
        resp = client.post(
            f"{API_URL}/{uuid.uuid4()}/audit_events",
            json=DEFAULT_PAGINATION,
        )

        assert resp.status_code == 401


####################################
# 404 Tests
####################################


class TestAnnouncementAuditEvents404:

    def test_audit_events_announcement_not_found_404(
        self, client, db_session, api_key_headers, enable_factory_create
    ):
        resp = client.post(
            f"{API_URL}/{uuid.uuid4()}/audit_events",
            headers=api_key_headers,
            json=DEFAULT_PAGINATION,
        )

        assert resp.status_code == 404


####################################
# 422 Tests
####################################


class TestAnnouncementAuditEvents422:

    def test_audit_events_missing_pagination_422(self, client, api_key_headers):
        resp = client.post(
            f"{API_URL}/{uuid.uuid4()}/audit_events",
            headers=api_key_headers,
            json={},
        )

        assert resp.status_code == 422

    def test_audit_events_invalid_sort_field_422(self, client, api_key_headers):
        resp = client.post(
            f"{API_URL}/{uuid.uuid4()}/audit_events",
            headers=api_key_headers,
            json={
                "pagination": {
                    "page_offset": 1,
                    "page_size": 25,
                    "sort_order": [{"order_by": "not_a_field", "sort_direction": "descending"}],
                }
            },
        )

        assert resp.status_code == 422
