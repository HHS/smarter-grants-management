import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.adapters import db
from src.adapters.aws import S3Config
from src.api.route_utils import raise_flask_error
from src.db.models.file_attachment_models import FileAttachment
from src.db.models.opportunity_models import Opportunity, OpportunityAttachment
from src.db.models.user_models import User
from src.services.files.pending_file_handling_domain_specific import (
    fetch_and_validate_scan_complete_file,
    move_pending_file_to_destination,
)
from src.services.opportunities.authorization import has_access
from src.services.opportunities.get_opportunity import get_opportunity
from src.util import file_util

logger = logging.getLogger(__name__)


def get_opportunity_attachment_path(
    opportunity: Opportunity,
    opportunity_attachment_id: uuid.UUID,
    file_name: str,
) -> str:
    return file_util.join(
        S3Config().draft_files_bucket_path,
        "opportunities",
        str(opportunity.opportunity_id),
        "attachments",
        str(opportunity_attachment_id),
        file_name,
    )


def create_opportunity_attachment_from_pending_file(
    db_session: db.Session,
    user: User,
    opportunity_id: uuid.UUID,
    pending_file_id: uuid.UUID,
) -> OpportunityAttachment:
    opportunity = get_opportunity(db_session, opportunity_id)

    if not has_access(user, opportunity, "update"):
        raise_flask_error(403, "User does not have access to update this opportunity")

    pending_file = fetch_and_validate_scan_complete_file(
        db_session,
        pending_file_id,
        user,
    )

    opportunity_attachment_id = uuid.uuid4()
    secure_file_name = file_util.get_file_name(pending_file.file_location)
    file_location = get_opportunity_attachment_path(
        opportunity,
        opportunity_attachment_id,
        secure_file_name,
    )
    file_size_bytes = file_util.get_file_length_bytes(pending_file.file_location)

    file_attachment = FileAttachment(
        file_location=file_location,
        file_name=pending_file.file_name,
        mime_type=pending_file.mime_type,
        file_description=None,
        file_size_bytes=file_size_bytes,
    )
    opportunity_attachment = OpportunityAttachment(
        opportunity_attachment_id=opportunity_attachment_id,
        opportunity=opportunity,
        file_attachment=file_attachment,
    )

    db_session.add(opportunity_attachment)
    db_session.flush()

    move_pending_file_to_destination(
        pending_file,
        file_location,
    )

    logger.info(
        "Created opportunity attachment from pending file",
        extra={
            "opportunity_id": opportunity_id,
            "opportunity_attachment_id": opportunity_attachment_id,
            "pending_file_id": pending_file_id,
        },
    )

    return opportunity_attachment


def delete_opportunity_attachment(
    db_session: db.Session,
    user: User,
    opportunity_id: uuid.UUID,
    opportunity_attachment_id: uuid.UUID,
) -> None:
    opportunity = get_opportunity(db_session, opportunity_id)

    if not has_access(user, opportunity, "update"):
        raise_flask_error(403, "User does not have access to update this opportunity")

    opportunity_attachment = db_session.execute(
        select(OpportunityAttachment)
        .where(
            OpportunityAttachment.opportunity_id == opportunity_id,
            OpportunityAttachment.opportunity_attachment_id == opportunity_attachment_id,
        )
        .options(selectinload(OpportunityAttachment.file_attachment))
    ).scalar_one_or_none()

    if opportunity_attachment is None:
        raise_flask_error(404, "Attachment not found")

    file_attachment = opportunity_attachment.file_attachment
    file_location = file_attachment.file_location

    db_session.delete(opportunity_attachment)
    db_session.delete(file_attachment)
    db_session.flush()

    file_util.delete_file(file_location)

    logger.info(
        "Deleted opportunity attachment",
        extra={
            "opportunity_id": opportunity_id,
            "opportunity_attachment_id": opportunity_attachment_id,
        },
    )
