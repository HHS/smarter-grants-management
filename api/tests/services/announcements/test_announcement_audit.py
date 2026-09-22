import uuid
from datetime import datetime
from types import SimpleNamespace

from src.constants.lookup_constants import AnnouncementCategory
from src.services.announcements.announcement_audit import build_changed_fields, snapshot_fields


def test_snapshot_fields_none_object_returns_all_none():
    result = snapshot_fields(None, ["announcement_title", "tagline"])

    assert result == {"announcement_title": None, "tagline": None}


def test_snapshot_fields_reads_plain_attributes():
    obj = SimpleNamespace(
        announcement_title="Community Health Grant Announcement",
        tagline="Supporting local health initiatives statewide",
    )

    result = snapshot_fields(obj, ["announcement_title", "tagline"])

    assert result == {
        "announcement_title": "Community Health Grant Announcement",
        "tagline": "Supporting local health initiatives statewide",
    }


def test_snapshot_fields_uses_extractor_override():
    obj = SimpleNamespace(
        announcement_assistance_listing=SimpleNamespace(
            assistance_listing_id="10.241-institute-of-rural-partnerships"
        )
    )

    result = snapshot_fields(
        obj,
        ["announcement_assistance_listing_id"],
        extractors={
            "announcement_assistance_listing_id": lambda o: (
                o.announcement_assistance_listing.assistance_listing_id
            ),
        },
    )

    assert result == {
        "announcement_assistance_listing_id": "10.241-institute-of-rural-partnerships"
    }


def test_build_changed_fields_only_includes_changed_keys():
    before = {
        "announcement_title": "Community Health Grant Announcement",
        "tagline": "Supporting local health initiatives statewide",
    }
    after = {
        "announcement_title": "Community Health Grant Announcement (Revised)",
        "tagline": "Supporting local health initiatives statewide",
    }

    result = build_changed_fields(before, after)

    assert result == {
        "changed_fields": {
            "announcement_title": {
                "before": "Community Health Grant Announcement",
                "after": "Community Health Grant Announcement (Revised)",
            },
        }
    }


def test_build_changed_fields_multiple_changed_keys():
    before = {
        "announcement_title": "Community Health Grant Announcement",
        "tagline": "Supporting local health initiatives",
    }
    after = {
        "announcement_title": "Community Health Grant Announcement (Revised)",
        "tagline": "Supporting local health initiatives statewide",
    }

    result = build_changed_fields(before, after)

    assert result == {
        "changed_fields": {
            "announcement_title": {
                "before": "Community Health Grant Announcement",
                "after": "Community Health Grant Announcement (Revised)",
            },
            "tagline": {
                "before": "Supporting local health initiatives",
                "after": "Supporting local health initiatives statewide",
            },
        }
    }


def test_build_changed_fields_before_null_on_create():
    before = {"announcement_title": None}
    after = {"announcement_title": "Community Health Grant Announcement"}

    result = build_changed_fields(before, after)

    assert result["changed_fields"]["announcement_title"] == {
        "before": None,
        "after": "Community Health Grant Announcement",
    }


def test_build_changed_fields_normalizes_uuid():
    original_listing_id = uuid.uuid4()
    revised_listing_id = uuid.uuid4()

    result = build_changed_fields(
        {"announcement_assistance_listing_id": original_listing_id},
        {"announcement_assistance_listing_id": revised_listing_id},
    )

    assert result["changed_fields"]["announcement_assistance_listing_id"] == {
        "before": str(original_listing_id),
        "after": str(revised_listing_id),
    }


def test_build_changed_fields_normalizes_datetime():
    original_opening = datetime(2026, 1, 1, 0, 0, 0)
    revised_opening = datetime(2026, 6, 1, 0, 0, 0)

    result = build_changed_fields(
        {"opening_timestamp": original_opening},
        {"opening_timestamp": revised_opening},
    )

    assert result["changed_fields"]["opening_timestamp"] == {
        "before": original_opening.isoformat(),
        "after": revised_opening.isoformat(),
    }


def test_build_changed_fields_normalizes_str_enum():
    result = build_changed_fields(
        {"category": None},
        {"category": AnnouncementCategory.DISCRETIONARY},
    )

    assert result["changed_fields"]["category"] == {
        "before": None,
        "after": AnnouncementCategory.DISCRETIONARY.value,
    }


def test_build_changed_fields_normalizes_set_as_list():
    result = build_changed_fields(
        {"open_to_applicants": None},
        {"open_to_applicants": {"individual"}},
    )

    assert result["changed_fields"]["open_to_applicants"] == {
        "before": None,
        "after": ["individual"],
    }


def test_build_changed_fields_composite_list_of_dicts():
    before = {
        "application_package_forms": [
            {"form_id": 424, "is_required": True},
        ]
    }
    after = {
        "application_package_forms": [
            {"form_id": 424, "is_required": False},
            {"form_id": 425, "is_required": True},
        ]
    }

    result = build_changed_fields(before, after)

    assert result["changed_fields"]["application_package_forms"] == {
        "before": [{"form_id": 424, "is_required": True}],
        "after": [
            {"form_id": 424, "is_required": False},
            {"form_id": 425, "is_required": True},
        ],
    }


def test_build_changed_fields_no_diff_returns_empty_dict():
    before = {"announcement_title": "Community Health Grant Announcement"}
    after = {"announcement_title": "Community Health Grant Announcement"}

    result = build_changed_fields(before, after)

    assert result == {"changed_fields": {}}
