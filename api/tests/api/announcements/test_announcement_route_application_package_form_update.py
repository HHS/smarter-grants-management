import uuid

from sqlalchemy import select

from src.constants.lookup_constants import AnnouncementAuditEvent
from src.db.models.announcement_models import AnnouncementAudit
from tests.db.models.factories import ApplicationPackageFactory, ApplicationPackageFormFactory


def test_application_package_form_update_200(client, api_key_headers, db_session):
    package = ApplicationPackageFactory.create(application_package_forms=[])

    request = {
        "forms": [
            {"form_id": 1, "is_required": True},
            {"form_id": 2, "is_required": True},
            {"form_id": 3, "is_required": False},
        ]
    }

    resp = client.put(
        f"/v1/announcements/{package.announcement_id}/application-packages/{package.application_package_id}/forms",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    db_session.refresh(package)

    db_forms = sorted(package.application_package_forms, key=lambda form: form.form_id)
    assert len(db_forms) == 3

    assert db_forms[0].form_id == 1
    assert db_forms[0].is_required is True

    assert db_forms[1].form_id == 2
    assert db_forms[1].is_required is True

    assert db_forms[2].form_id == 3
    assert db_forms[2].is_required is False


def test_application_package_form_update_change_existing_200(client, api_key_headers, db_session):
    package = ApplicationPackageFactory.create(application_package_forms=[])

    # 1 is going to be unmodified
    # 2 will be new
    # 3 will change to non-required
    # 4 will be deleted
    ApplicationPackageFormFactory.create(application_package=package, form_id=1, is_required=True)
    ApplicationPackageFormFactory.create(application_package=package, form_id=3, is_required=True)
    ApplicationPackageFormFactory.create(application_package=package, form_id=4, is_required=True)

    request = {
        "forms": [
            {"form_id": 1, "is_required": True},
            {"form_id": 2, "is_required": True},
            {"form_id": 3, "is_required": False},
        ]
    }

    resp = client.put(
        f"/v1/announcements/{package.announcement_id}/application-packages/{package.application_package_id}/forms",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    db_session.refresh(package)

    db_forms = sorted(package.application_package_forms, key=lambda form: form.form_id)
    assert len(db_forms) == 3

    assert db_forms[0].form_id == 1
    assert db_forms[0].is_required is True

    assert db_forms[1].form_id == 2
    assert db_forms[1].is_required is True

    assert db_forms[2].form_id == 3
    assert db_forms[2].is_required is False


def test_application_package_form_update_package_not_found_404(client, api_key_headers):
    request = {"forms": [{"form_id": 1, "is_required": True}]}

    resp = client.put(
        f"/v1/announcements/{uuid.uuid4()}/application-packages/{uuid.uuid4()}/forms",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_application_package_form_update_bad_api_key_401(client):
    request = {"forms": [{"form_id": 1, "is_required": True}]}

    resp = client.put(
        f"/v1/announcements/{uuid.uuid4()}/application-packages/{uuid.uuid4()}/forms",
        json=request,
        headers={"X-API-Key": "hello i am a key"},
    )
    assert resp.status_code == 401


def test_application_package_form_update_no_api_key_401(client):
    request = {"forms": [{"form_id": 1, "is_required": True}]}

    resp = client.put(
        f"/v1/announcements/{uuid.uuid4()}/application-packages/{uuid.uuid4()}/forms", json=request
    )
    assert resp.status_code == 401


def test_application_package_form_update_records_audit(client, api_key_headers, db_session):
    package = ApplicationPackageFactory.create(application_package_forms=[])

    # 1 is going to be unmodified
    # 2 will be new
    # 3 will change to non-required
    # 4 will be deleted
    ApplicationPackageFormFactory.create(application_package=package, form_id=1, is_required=True)
    ApplicationPackageFormFactory.create(application_package=package, form_id=3, is_required=True)
    ApplicationPackageFormFactory.create(application_package=package, form_id=4, is_required=True)

    request = {
        "forms": [
            {"form_id": 1, "is_required": True},
            {"form_id": 2, "is_required": True},
            {"form_id": 3, "is_required": False},
        ]
    }

    resp = client.put(
        f"/v1/announcements/{package.announcement_id}/application-packages/{package.application_package_id}/forms",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    audit_rows = (
        db_session.execute(
            select(AnnouncementAudit).where(
                AnnouncementAudit.announcement_id == package.announcement_id
            )
        )
        .scalars()
        .all()
    )
    assert len(audit_rows) == 1
    audit = audit_rows[0]
    assert audit.announcement_audit_event == AnnouncementAuditEvent.APPLICATION_PACKAGE_UPDATED
    assert audit.application_package_id == package.application_package_id

    forms_diff = audit.audit_metadata["changed_fields"]["application_package_forms"]
    before_forms = {(f["form_id"], f["is_required"]) for f in forms_diff["before"]}
    after_forms = {(f["form_id"], f["is_required"]) for f in forms_diff["after"]}

    assert before_forms == {(1, True), (3, True), (4, True)}
    assert after_forms == {(1, True), (2, True), (3, False)}
