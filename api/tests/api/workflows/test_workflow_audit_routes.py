import uuid

from src.auth.api_jwt_auth import create_jwt_for_user
from src.constants.lookup_constants import Privilege
from tests.db.models.factories import ProgramWorkflowFactory, UserFactory, WorkflowAuditFactory
from tests.workflow.workflow_test_util import create_approver

#################################
#
# Tests for POST /v1/workflows/<workflow_id>/audit.
#
#################################


def post_audit(client, workflow_id, payload: dict, headers: dict | None = None):
    return client.post(f"/v1/workflows/{workflow_id}/audit", json=payload, headers=headers or {})


class TestWorkflowAuditEndpoint:

    def test_get_workflow_audit_200(self, client, db_session, enable_factory_create):
        """Pagination info is correct, and the default sort is descending by created_at."""
        workflow = ProgramWorkflowFactory.create()
        approver = create_approver(
            db_session,
            workflow.resource.concrete_resource.grant_office,
            privileges=[Privilege.VIEW_PROGRAM],
        )
        token, _ = create_jwt_for_user(approver, db_session)

        audits = [WorkflowAuditFactory.create(workflow=workflow) for _ in range(5)]
        db_session.commit()

        response = post_audit(
            client,
            workflow.workflow_id,
            {"pagination": {"page_offset": 1, "page_size": 3}},
            {"X-MGMT-Token": token},
        )

        assert response.status_code == 200, response.json
        assert response.json["pagination_info"]["page_offset"] == 1
        assert response.json["pagination_info"]["page_size"] == 3
        assert response.json["pagination_info"]["total_records"] == 5
        assert response.json["pagination_info"]["total_pages"] == 2

        data = response.json["data"]
        assert len(data) == 3
        for i in range(len(data) - 1):
            assert data[i]["created_at"] >= data[i + 1]["created_at"]

        returned_ids = {a["workflow_audit_id"] for a in data}
        assert returned_ids.issubset({str(a.workflow_audit_id) for a in audits})

    def test_get_workflow_audit_custom_sort_200(self, client, db_session, enable_factory_create):
        """An explicit ascending sort_order is honored, proving ordering is actually applied."""
        workflow = ProgramWorkflowFactory.create()
        approver = create_approver(
            db_session,
            workflow.resource.concrete_resource.grant_office,
            privileges=[Privilege.VIEW_PROGRAM],
        )
        token, _ = create_jwt_for_user(approver, db_session)

        for _ in range(4):
            WorkflowAuditFactory.create(workflow=workflow)
        db_session.commit()

        response = post_audit(
            client,
            workflow.workflow_id,
            {
                "pagination": {
                    "page_offset": 1,
                    "page_size": 10,
                    "sort_order": [{"order_by": "created_at", "sort_direction": "ascending"}],
                }
            },
            {"X-MGMT-Token": token},
        )

        assert response.status_code == 200, response.json
        data = response.json["data"]
        assert len(data) == 4
        for i in range(len(data) - 1):
            assert data[i]["created_at"] <= data[i + 1]["created_at"]

    def test_get_workflow_audit_not_found_404(self, client, db_session, enable_factory_create):
        non_existent_id = uuid.uuid4()
        user = UserFactory.create()
        token, _ = create_jwt_for_user(user, db_session)
        db_session.commit()

        response = post_audit(
            client,
            non_existent_id,
            {"pagination": {"page_offset": 1, "page_size": 10}},
            {"X-MGMT-Token": token},
        )

        assert response.status_code == 404
        assert f"Could not find Workflow with ID {non_existent_id}" in response.json["message"]

    def test_get_workflow_audit_wrong_privilege_403(
        self, client, db_session, enable_factory_create
    ):
        workflow = ProgramWorkflowFactory.create()
        user = create_approver(
            db_session,
            workflow.resource.concrete_resource.grant_office,
            privileges=[Privilege.UPDATE_PROGRAM],
        )
        token, _ = create_jwt_for_user(user, db_session)
        db_session.commit()

        response = post_audit(
            client,
            workflow.workflow_id,
            {"pagination": {"page_offset": 1, "page_size": 10}},
            {"X-MGMT-Token": token},
        )

        assert response.status_code == 403
        assert response.json["message"] == "Forbidden"
