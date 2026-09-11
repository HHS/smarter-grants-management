import uuid

from tests.db.models.factories import (
    AnnouncementAssistanceListingFactory,
    AnnouncementFactory,
    AnnouncementSummaryFactory,
    ApplicationPackageFactory,
)


def test_announcement_get_200(
    client,
    db_session,
    api_key_headers,
    assistance_listing,
):
    announcement = AnnouncementFactory.create(announcement_assistance_listings=[])
    AnnouncementAssistanceListingFactory.create(
        announcement=announcement, assistance_listing=assistance_listing
    )

    response = client.get(
        f"/v1/announcements/{announcement.announcement_id}",
        headers=api_key_headers,
    )

    assert response.status_code == 200

    data = response.get_json()["data"]
    assert data["announcement_id"] == str(announcement.announcement_id)
    assert data["announcement_number"] == announcement.announcement_number
    assert data["announcement_title"] == announcement.announcement_title
    assert data["tagline"] == announcement.tagline
    assert data["purpose_statement"] == announcement.purpose_statement
    assert data["category"] == announcement.category.value

    assistance_listings = data["announcement_assistance_listings"]
    assert len(assistance_listings) == 1
    assert (
        assistance_listings[0]["assistance_listing_number"]
        == assistance_listing.assistance_listing_number
    )


def test_announcement_get_with_package_and_forms(
    client,
    db_session,
    api_key_headers,
    assistance_listing,
):
    announcement = AnnouncementFactory.create(announcement_assistance_listings=[])
    AnnouncementAssistanceListingFactory.create(
        announcement=announcement, assistance_listing=assistance_listing
    )
    forecast = AnnouncementSummaryFactory.create(announcement=announcement, is_forecast=True)
    non_forecast = AnnouncementSummaryFactory.create(announcement=announcement, is_forecast=False)
    application_package = ApplicationPackageFactory.create(
        announcement=announcement,
        announcement_assistance_listing=announcement.announcement_assistance_listings[0],
    )

    response = client.get(
        f"/v1/announcements/{announcement.announcement_id}",
        headers=api_key_headers,
    )

    assert response.status_code == 200

    data = response.get_json()["data"]
    assert data["announcement_id"] == str(announcement.announcement_id)
    assert data["announcement_number"] == announcement.announcement_number
    assert data["announcement_title"] == announcement.announcement_title
    assert data["tagline"] == announcement.tagline
    assert data["purpose_statement"] == announcement.purpose_statement
    assert data["category"] == announcement.category.value

    assistance_listings = data["announcement_assistance_listings"]
    assert len(assistance_listings) == 1
    assert (
        assistance_listings[0]["assistance_listing_number"]
        == assistance_listing.assistance_listing_number
    )

    forecast_resp = data["forecast_summary"]
    assert forecast_resp["announcement_summary_id"] == str(forecast.announcement_summary_id)
    assert forecast_resp["summary_description"] == forecast.summary_description
    assert forecast_resp["is_cost_sharing"] == forecast.is_cost_sharing
    assert forecast_resp["is_forecast"] == forecast.is_forecast
    assert forecast_resp["close_timestamp"] is None
    assert forecast_resp["close_timestamp_description"] is None
    assert forecast_resp["post_timestamp"] == forecast.post_timestamp.isoformat()
    assert forecast_resp["archive_timestamp"] == forecast.archive_timestamp.isoformat()
    assert forecast_resp["expected_number_of_awards"] == forecast.expected_number_of_awards
    assert (
        forecast_resp["estimated_total_program_funding"] == forecast.estimated_total_program_funding
    )
    assert forecast_resp["award_floor"] == forecast.award_floor
    assert forecast_resp["award_ceiling"] == forecast.award_ceiling
    assert forecast_resp["additional_info_url"] == forecast.additional_info_url
    assert (
        forecast_resp["additional_info_url_description"] == forecast.additional_info_url_description
    )
    assert (
        forecast_resp["forecasted_post_timestamp"] == forecast.forecasted_post_timestamp.isoformat()
    )
    assert (
        forecast_resp["forecasted_close_timestamp"]
        == forecast.forecasted_close_timestamp.isoformat()
    )
    assert (
        forecast_resp["forecasted_close_timestamp_description"]
        == forecast.forecasted_close_timestamp_description
    )
    if forecast.estimated_award_date:
        assert forecast_resp["estimated_award_date"] == forecast.estimated_award_date.isoformat()
    else:
        assert forecast_resp["estimated_award_date"] is None
    if forecast.estimated_project_start_date:
        assert (
            forecast_resp["estimated_project_start_date"]
            == forecast.estimated_project_start_date.isoformat()
        )
    else:
        assert forecast_resp["estimated_project_start_date"] is None
    assert forecast_resp["fiscal_year"] == forecast.fiscal_year
    assert forecast_resp["funding_category_description"] == forecast.funding_category_description
    assert (
        forecast_resp["applicant_eligibility_description"]
        == forecast.applicant_eligibility_description
    )
    assert forecast_resp["agency_contact_description"] == forecast.agency_contact_description
    assert forecast_resp["agency_email_address"] == forecast.agency_email_address
    assert forecast_resp["funding_instruments"] == forecast.funding_instruments
    assert forecast_resp["funding_categories"] == forecast.funding_categories
    assert forecast_resp["applicant_types"] == forecast.applicant_types

    non_forecast_resp = data["non_forecast_summary"]
    assert non_forecast_resp["announcement_summary_id"] == str(non_forecast.announcement_summary_id)
    assert non_forecast_resp["summary_description"] == non_forecast.summary_description
    assert non_forecast_resp["is_cost_sharing"] == non_forecast.is_cost_sharing
    assert non_forecast_resp["is_forecast"] == non_forecast.is_forecast
    assert non_forecast_resp["close_timestamp"] == non_forecast.close_timestamp.isoformat()
    assert (
        non_forecast_resp["close_timestamp_description"] == non_forecast.close_timestamp_description
    )
    assert non_forecast_resp["post_timestamp"] == non_forecast.post_timestamp.isoformat()
    assert non_forecast_resp["archive_timestamp"] == non_forecast.archive_timestamp.isoformat()
    assert non_forecast_resp["expected_number_of_awards"] == non_forecast.expected_number_of_awards
    assert (
        non_forecast_resp["estimated_total_program_funding"]
        == non_forecast.estimated_total_program_funding
    )
    assert non_forecast_resp["award_floor"] == non_forecast.award_floor
    assert non_forecast_resp["award_ceiling"] == non_forecast.award_ceiling
    assert non_forecast_resp["additional_info_url"] == non_forecast.additional_info_url
    assert (
        non_forecast_resp["additional_info_url_description"]
        == non_forecast.additional_info_url_description
    )
    assert non_forecast_resp["forecasted_post_timestamp"] is None
    assert non_forecast_resp["forecasted_close_timestamp"] is None
    assert non_forecast_resp["forecasted_close_timestamp_description"] is None
    if non_forecast.estimated_award_date:
        assert (
            non_forecast_resp["estimated_award_date"]
            == non_forecast.estimated_award_date.isoformat()
        )
    else:
        assert non_forecast_resp["estimated_award_date"] is None
    if non_forecast.estimated_project_start_date:
        assert (
            non_forecast_resp["estimated_project_start_date"]
            == non_forecast.estimated_project_start_date.isoformat()
        )
    else:
        assert non_forecast_resp["estimated_project_start_date"] is None
    assert non_forecast_resp["fiscal_year"] == non_forecast.fiscal_year
    assert (
        non_forecast_resp["funding_category_description"]
        == non_forecast.funding_category_description
    )
    assert (
        non_forecast_resp["applicant_eligibility_description"]
        == non_forecast.applicant_eligibility_description
    )
    assert (
        non_forecast_resp["agency_contact_description"] == non_forecast.agency_contact_description
    )
    assert non_forecast_resp["agency_email_address"] == non_forecast.agency_email_address
    assert non_forecast_resp["funding_instruments"] == non_forecast.funding_instruments
    assert non_forecast_resp["funding_categories"] == non_forecast.funding_categories
    assert non_forecast_resp["applicant_types"] == non_forecast.applicant_types

    application_package_resp = data["application_packages"][0]
    assert application_package_resp["application_package_id"] == str(
        application_package.application_package_id
    )
    assert (
        application_package_resp["public_application_package_id"]
        == application_package.public_application_package_id
    )
    assert (
        application_package_resp["application_package_title"]
        == application_package.application_package_title
    )
    assert (
        application_package_resp["opening_timestamp"]
        == application_package.opening_timestamp.isoformat()
    )
    assert (
        application_package_resp["closing_timestamp"]
        == application_package.closing_timestamp.isoformat()
    )
    assert application_package_resp["contact_info"] == application_package.contact_info
    assert (
        application_package_resp["announcement_assistance_listing"]["assistance_listing_number"]
        == application_package.announcement_assistance_listing.assistance_listing.assistance_listing_number
    )


def test_announcement_get_404(
    client,
    api_key_headers,
):
    response = client.get(
        f"/v1/announcements/{uuid.uuid4()}",
        headers=api_key_headers,
    )

    assert response.status_code == 404
    assert "Could not find announcement with ID" in response.get_json()["message"]


def test_announcement_get_no_auth_401(client):
    response = client.get(f"/v1/announcements/{uuid.uuid4()}")

    assert response.status_code == 401
