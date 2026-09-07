import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from src.constants.lookup_constants import (
    CompetitionOpenToApplicant,
    FileScanStatus,
    OpportunityAuditEvent,
)
from src.db.models.competition_models import Competition, CompetitionInstruction
from src.db.models.file_upload_models import PendingFile
from src.db.models.opportunity_group_audit_models import OpportunityGroupAudit
from src.util import file_util
from tests.db.models.factories import OpportunityFactory, UserApiKeyFactory


def build_competition_request():
    now = datetime.now(UTC)
    return {
        "competition_title": "Test Competition",
        "public_competition_id": "TEST-COMP-001",
        "opening_timestamp": now.isoformat(),
        "closing_timestamp": (now + timedelta(days=30)).isoformat(),
        "grace_period": 24,
        "contact_info": "contact@example.gov",
        "open_to_applicants": [
            CompetitionOpenToApplicant.INDIVIDUAL.value,
            CompetitionOpenToApplicant.ORGANIZATION.value,
        ],
    }


def create_competition(db_session, opportunity):
    now = datetime.now(UTC)
    competition = Competition(
        opportunity=opportunity,
        competition_title="Existing Competition",
        public_competition_id="EXISTING-001",
        opening_timestamp=now,
        closing_timestamp=now + timedelta(days=30),
        grace_period=24,
        contact_info="existing@example.gov",
    )
    competition.open_to_applicants = {CompetitionOpenToApplicant.INDIVIDUAL}
    db_session.add(competition)
    db_session.commit()
    return competition


def create_pending_file(db_session, user, s3_config):
    pending_file_id = uuid.uuid4()
    file_location = file_util.join(
        s3_config.file_scan_bucket_path, "scanned", str(pending_file_id), "instructions.pdf"
    )
    file_util.write_to_file(file_location, "competition instructions")
    pending_file = PendingFile(
        pending_file_id=pending_file_id,
        user=user,
        file_name="Competition Instructions.pdf",
        file_location=file_location,
        mime_type="application/pdf",
        file_scan_status=FileScanStatus.COMPLETE,
    )
    db_session.add(pending_file)
    db_session.commit()
    return pending_file


def test_competition_create_200(client, db_session, enable_factory_create):
    opportunity = OpportunityFactory.create()
    api_key = UserApiKeyFactory.create()
    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/competitions",
        json=build_competition_request(),
        headers={"X-API-Key": api_key.key_id},
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["competition_title"] == "Test Competition"
    assert set(data["open_to_applicants"]) == {
        CompetitionOpenToApplicant.INDIVIDUAL.value,
        CompetitionOpenToApplicant.ORGANIZATION.value,
    }
    competition = db_session.execute(
        select(Competition).where(Competition.competition_id == uuid.UUID(data["competition_id"]))
    ).scalar_one()
    audit = db_session.execute(
        select(OpportunityGroupAudit).where(
            OpportunityGroupAudit.competition_id == competition.competition_id,
            OpportunityGroupAudit.opportunity_audit_event
            == OpportunityAuditEvent.COMPETITION_CREATED,
        )
    ).scalar_one()
    assert audit.opportunity_id == opportunity.opportunity_id


def test_competition_create_unknown_opportunity_404(client, enable_factory_create):
    api_key = UserApiKeyFactory.create()
    response = client.post(
        f"/v1/opportunities/{uuid.uuid4()}/competitions",
        json=build_competition_request(),
        headers={"X-API-Key": api_key.key_id},
    )
    assert response.status_code == 404


def test_competition_create_invalid_timestamps_422(client, enable_factory_create):
    opportunity = OpportunityFactory.create()
    api_key = UserApiKeyFactory.create()
    request = build_competition_request()
    request["opening_timestamp"], request["closing_timestamp"] = (
        request["closing_timestamp"],
        request["opening_timestamp"],
    )
    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/competitions",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert response.status_code == 422


def test_competition_create_no_auth_401(client, enable_factory_create):
    opportunity = OpportunityFactory.create()
    assert (
        client.post(
            f"/v1/opportunities/{opportunity.opportunity_id}/competitions",
            json=build_competition_request(),
        ).status_code
        == 401
    )


def test_competition_update_200(client, db_session, enable_factory_create):
    opportunity = OpportunityFactory.create()
    competition = create_competition(db_session, opportunity)
    api_key = UserApiKeyFactory.create()
    request = build_competition_request()
    request["competition_title"] = "Updated Competition"
    response = client.put(
        f"/v1/opportunities/{opportunity.opportunity_id}/competitions/{competition.competition_id}",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert response.status_code == 200
    db_session.refresh(competition)
    assert competition.competition_title == "Updated Competition"
    audit = db_session.execute(
        select(OpportunityGroupAudit).where(
            OpportunityGroupAudit.competition_id == competition.competition_id,
            OpportunityGroupAudit.opportunity_audit_event
            == OpportunityAuditEvent.COMPETITION_UPDATED,
        )
    ).scalar_one()
    assert audit.audit_metadata["competition_title"]["after"] == "Updated Competition"


def test_competition_update_wrong_opportunity_404(client, db_session, enable_factory_create):
    opportunity = OpportunityFactory.create()
    other = OpportunityFactory.create()
    competition = create_competition(db_session, other)
    api_key = UserApiKeyFactory.create()
    response = client.put(
        f"/v1/opportunities/{opportunity.opportunity_id}/competitions/{competition.competition_id}",
        json=build_competition_request(),
        headers={"X-API-Key": api_key.key_id},
    )
    assert response.status_code == 404


def test_competition_instruction_create_200(client, db_session, enable_factory_create, s3_config):
    opportunity = OpportunityFactory.create()
    competition = create_competition(db_session, opportunity)
    api_key = UserApiKeyFactory.create()
    pending = create_pending_file(db_session, api_key.user, s3_config)
    original = pending.file_location
    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/competitions/{competition.competition_id}/instructions",
        json={"pending_file_id": str(pending.pending_file_id)},
        headers={"X-API-Key": api_key.key_id},
    )
    assert response.status_code == 200
    instruction_id = uuid.UUID(response.get_json()["data"]["competition_instruction_id"])
    instruction = db_session.execute(
        select(CompetitionInstruction).where(
            CompetitionInstruction.competition_instruction_id == instruction_id
        )
    ).scalar_one()
    db_session.refresh(pending)
    assert pending.file_scan_status == FileScanStatus.PROCESSED
    assert not file_util.file_exists(original)
    assert file_util.file_exists(instruction.file_attachment.file_location)


def test_competition_instruction_wrong_opportunity_404(
    client, db_session, enable_factory_create, s3_config
):
    opportunity = OpportunityFactory.create()
    other = OpportunityFactory.create()
    competition = create_competition(db_session, other)
    api_key = UserApiKeyFactory.create()
    pending = create_pending_file(db_session, api_key.user, s3_config)
    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/competitions/{competition.competition_id}/instructions",
        json={"pending_file_id": str(pending.pending_file_id)},
        headers={"X-API-Key": api_key.key_id},
    )
    assert response.status_code == 404


def test_competition_instruction_delete_200(client, db_session, enable_factory_create, s3_config):
    opportunity = OpportunityFactory.create()
    competition = create_competition(db_session, opportunity)
    api_key = UserApiKeyFactory.create()
    pending = create_pending_file(db_session, api_key.user, s3_config)
    create_response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/competitions/{competition.competition_id}/instructions",
        json={"pending_file_id": str(pending.pending_file_id)},
        headers={"X-API-Key": api_key.key_id},
    )
    instruction_id = create_response.get_json()["data"]["competition_instruction_id"]
    response = client.delete(
        f"/v1/opportunities/{opportunity.opportunity_id}/competitions/{competition.competition_id}/instructions/{instruction_id}",
        headers={"X-API-Key": api_key.key_id},
    )
    assert response.status_code == 200
    assert (
        db_session.execute(
            select(CompetitionInstruction).where(
                CompetitionInstruction.competition_instruction_id == uuid.UUID(instruction_id)
            )
        ).scalar_one_or_none()
        is None
    )


def test_competition_instruction_delete_unknown_instruction_404(
    client, db_session, enable_factory_create
):
    opportunity = OpportunityFactory.create()
    competition = create_competition(db_session, opportunity)
    api_key = UserApiKeyFactory.create()
    response = client.delete(
        f"/v1/opportunities/{opportunity.opportunity_id}/competitions/{competition.competition_id}/instructions/{uuid.uuid4()}",
        headers={"X-API-Key": api_key.key_id},
    )
    assert response.status_code == 404
