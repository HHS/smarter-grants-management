"""Tests for announcement summary timestamp validation based on forecast status."""

from datetime import timedelta

from src.constants.lookup_constants import ApplicantType, FundingCategory, FundingInstrument
from src.util import datetime_util
from tests.db.models.factories import AnnouncementFactory, AnnouncementSummaryFactory


def build_forecast_summary_request(
    include_forecasted_post_timestamp: bool = True,
    include_post_timestamp: bool = False,
) -> dict:
    """Build a forecast summary request with optional timestamp fields."""
    request = {
        "summary_description": "A forecast summary for testing.",
        "is_cost_sharing": False,
        "award_floor": 10_000,
        "award_ceiling": 100_000,
        "funding_categories": [FundingCategory.AGRICULTURE],
        "funding_instruments": [FundingInstrument.GRANT],
        "applicant_types": [ApplicantType.STATE_GOVERNMENTS],
        "agency_contact_description": None,
        "agency_email_address": None,
        "agency_email_address_description": None,
        "is_forecast": True,
    }

    if include_forecasted_post_timestamp:
        request["forecasted_post_timestamp"] = (
            datetime_util.utcnow() + timedelta(days=30)
        ).isoformat()

    if include_post_timestamp:
        request["post_timestamp"] = datetime_util.utcnow().isoformat()

    return request


def build_non_forecast_summary_request(
    include_post_timestamp: bool = True,
    include_forecasted_post_timestamp: bool = False,
) -> dict:
    """Build a non-forecast summary request with optional timestamp fields."""
    request = {
        "summary_description": "A non-forecast summary for testing.",
        "is_cost_sharing": False,
        "award_floor": 10_000,
        "award_ceiling": 100_000,
        "funding_categories": [FundingCategory.AGRICULTURE],
        "funding_instruments": [FundingInstrument.GRANT],
        "applicant_types": [ApplicantType.STATE_GOVERNMENTS],
        "agency_contact_description": None,
        "agency_email_address": None,
        "agency_email_address_description": None,
        "is_forecast": False,
    }

    if include_post_timestamp:
        request["post_timestamp"] = datetime_util.utcnow().isoformat()
        request["close_timestamp"] = (datetime_util.utcnow() + timedelta(days=30)).isoformat()

    if include_forecasted_post_timestamp:
        request["forecasted_post_timestamp"] = (
            datetime_util.utcnow() + timedelta(days=30)
        ).isoformat()

    return request


class TestForecastSummaryTimestampValidation:
    """Test timestamp validation for forecast summaries."""

    def test_create_forecast_with_forecasted_post_timestamp_200(
        self,
        client,
        api_key_headers,
    ):
        """Creating a forecast with forecasted_post_timestamp and no post_timestamp succeeds."""
        announcement = AnnouncementFactory.create()
        request = build_forecast_summary_request(
            include_forecasted_post_timestamp=True,
            include_post_timestamp=False,
        )

        response = client.post(
            f"/v1/announcements/{announcement.announcement_id}/summaries",
            json=request,
            headers=api_key_headers,
        )

        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["is_forecast"] is True
        assert data["forecasted_post_timestamp"] is not None
        assert data["post_timestamp"] is None

    def test_create_forecast_without_forecasted_post_timestamp_422(
        self,
        client,
        api_key_headers,
    ):
        """Creating a forecast without forecasted_post_timestamp returns 422."""
        announcement = AnnouncementFactory.create()
        request = build_forecast_summary_request(
            include_forecasted_post_timestamp=False,
            include_post_timestamp=False,
        )

        response = client.post(
            f"/v1/announcements/{announcement.announcement_id}/summaries",
            json=request,
            headers=api_key_headers,
        )

        assert response.status_code == 422
        assert (
            "forecasted_post_timestamp is required for forecast summaries"
            in response.get_json()["message"]
        )

    def test_create_forecast_with_only_post_timestamp_422(
        self,
        client,
        api_key_headers,
    ):
        """Creating a forecast with only post_timestamp (no forecasted_post_timestamp) returns 422."""
        announcement = AnnouncementFactory.create()
        request = build_forecast_summary_request(
            include_forecasted_post_timestamp=False,
            include_post_timestamp=True,
        )

        response = client.post(
            f"/v1/announcements/{announcement.announcement_id}/summaries",
            json=request,
            headers=api_key_headers,
        )

        assert response.status_code == 422
        assert (
            "forecasted_post_timestamp is required for forecast summaries"
            in response.get_json()["message"]
        )

    def test_update_forecast_without_forecasted_post_timestamp_but_existing_200(
        self,
        client,
        api_key_headers,
    ):
        """Updating a forecast without providing forecasted_post_timestamp but with existing value succeeds."""
        summary = AnnouncementSummaryFactory.create(
            is_forecast=True,
            forecasted_post_timestamp=datetime_util.utcnow() + timedelta(days=30),
        )
        request = {
            "summary_description": "Updated description",
            "is_cost_sharing": summary.is_cost_sharing,
            "award_floor": summary.award_floor,
            "award_ceiling": summary.award_ceiling,
            "funding_categories": list(summary.funding_categories),
            "funding_instruments": list(summary.funding_instruments),
            "applicant_types": list(summary.applicant_types),
            "agency_contact_description": summary.agency_contact_description,
            "agency_email_address": summary.agency_email_address,
            "agency_email_address_description": summary.agency_email_address_description,
        }

        response = client.put(
            f"/v1/announcements/{summary.announcement_id}/summaries/"
            f"{summary.announcement_summary_id}",
            json=request,
            headers=api_key_headers,
        )

        assert response.status_code == 200
        assert response.get_json()["data"]["summary_description"] == "Updated description"

    def test_update_forecast_clearing_forecasted_post_timestamp_422(
        self,
        client,
        api_key_headers,
    ):
        """Updating a forecast by setting forecasted_post_timestamp to None returns 422."""
        summary = AnnouncementSummaryFactory.create(
            is_forecast=True,
            forecasted_post_timestamp=datetime_util.utcnow() + timedelta(days=30),
        )
        request = {
            "summary_description": summary.summary_description,
            "is_cost_sharing": summary.is_cost_sharing,
            "post_timestamp": summary.post_timestamp,
            "close_timestamp": summary.close_timestamp,
            "award_floor": summary.award_floor,
            "award_ceiling": summary.award_ceiling,
            "funding_categories": list(summary.funding_categories),
            "funding_instruments": list(summary.funding_instruments),
            "applicant_types": list(summary.applicant_types),
            "agency_contact_description": summary.agency_contact_description,
            "agency_email_address": summary.agency_email_address,
            "agency_email_address_description": summary.agency_email_address_description,
            "forecasted_post_timestamp": None,
        }

        response = client.put(
            f"/v1/announcements/{summary.announcement_id}/summaries/"
            f"{summary.announcement_summary_id}",
            json=request,
            headers=api_key_headers,
        )

        assert response.status_code == 422
        assert (
            "forecasted_post_timestamp is required for forecast summaries"
            in response.get_json()["message"]
        )


class TestNonForecastSummaryTimestampValidation:
    """Test timestamp validation for non-forecast summaries."""

    def test_create_non_forecast_with_post_timestamp_200(
        self,
        client,
        api_key_headers,
    ):
        """Creating a non-forecast with post_timestamp and no forecasted_post_timestamp succeeds."""
        announcement = AnnouncementFactory.create()
        request = build_non_forecast_summary_request(
            include_post_timestamp=True,
            include_forecasted_post_timestamp=False,
        )

        response = client.post(
            f"/v1/announcements/{announcement.announcement_id}/summaries",
            json=request,
            headers=api_key_headers,
        )

        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["is_forecast"] is False
        assert data["post_timestamp"] is not None

    def test_create_non_forecast_without_post_timestamp_422(
        self,
        client,
        api_key_headers,
    ):
        """Creating a non-forecast without post_timestamp returns 422."""
        announcement = AnnouncementFactory.create()
        request = build_non_forecast_summary_request(
            include_post_timestamp=False,
            include_forecasted_post_timestamp=False,
        )

        response = client.post(
            f"/v1/announcements/{announcement.announcement_id}/summaries",
            json=request,
            headers=api_key_headers,
        )

        assert response.status_code == 422
        assert (
            "post_timestamp is required for non-forecast summaries"
            in response.get_json()["message"]
        )

    def test_create_non_forecast_with_only_forecasted_post_timestamp_422(
        self,
        client,
        api_key_headers,
    ):
        """Creating a non-forecast with only forecasted_post_timestamp (no post_timestamp) returns 422."""
        announcement = AnnouncementFactory.create()
        request = build_non_forecast_summary_request(
            include_post_timestamp=False,
            include_forecasted_post_timestamp=True,
        )

        response = client.post(
            f"/v1/announcements/{announcement.announcement_id}/summaries",
            json=request,
            headers=api_key_headers,
        )

        assert response.status_code == 422
        assert (
            "post_timestamp is required for non-forecast summaries"
            in response.get_json()["message"]
        )

    def test_update_non_forecast_without_post_timestamp_but_existing_200(
        self,
        client,
        api_key_headers,
    ):
        """Updating a non-forecast without providing post_timestamp but with existing value succeeds."""
        summary = AnnouncementSummaryFactory.create(
            is_forecast=False,
            post_timestamp=datetime_util.utcnow(),
        )
        request = {
            "summary_description": "Updated description",
            "is_cost_sharing": summary.is_cost_sharing,
            "award_floor": summary.award_floor,
            "award_ceiling": summary.award_ceiling,
            "funding_categories": list(summary.funding_categories),
            "funding_instruments": list(summary.funding_instruments),
            "applicant_types": list(summary.applicant_types),
            "agency_contact_description": summary.agency_contact_description,
            "agency_email_address": summary.agency_email_address,
            "agency_email_address_description": summary.agency_email_address_description,
        }

        response = client.put(
            f"/v1/announcements/{summary.announcement_id}/summaries/"
            f"{summary.announcement_summary_id}",
            json=request,
            headers=api_key_headers,
        )

        assert response.status_code == 200
        assert response.get_json()["data"]["summary_description"] == "Updated description"

    def test_update_non_forecast_clearing_post_timestamp_422(
        self,
        client,
        api_key_headers,
    ):
        """Updating a non-forecast by setting post_timestamp to None returns 422."""
        summary = AnnouncementSummaryFactory.create(
            is_forecast=False,
            post_timestamp=datetime_util.utcnow(),
        )
        request = {
            "summary_description": summary.summary_description,
            "is_cost_sharing": summary.is_cost_sharing,
            "post_timestamp": None,
            "close_timestamp": summary.close_timestamp,
            "award_floor": summary.award_floor,
            "award_ceiling": summary.award_ceiling,
            "funding_categories": list(summary.funding_categories),
            "funding_instruments": list(summary.funding_instruments),
            "applicant_types": list(summary.applicant_types),
            "agency_contact_description": summary.agency_contact_description,
            "agency_email_address": summary.agency_email_address,
            "agency_email_address_description": summary.agency_email_address_description,
        }

        response = client.put(
            f"/v1/announcements/{summary.announcement_id}/summaries/"
            f"{summary.announcement_summary_id}",
            json=request,
            headers=api_key_headers,
        )

        assert response.status_code == 422
        assert (
            "post_timestamp is required for non-forecast summaries"
            in response.get_json()["message"]
        )
