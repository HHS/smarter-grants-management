import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.adapters import db
from src.adapters.aws import S3Config
from src.api.route_utils import raise_flask_error
from src.db.models.competition_models import Competition, CompetitionInstruction
from src.db.models.file_attachment_models import FileAttachment
from src.db.models.user_models import User
from src.services.files.pending_file_handling_domain_specific import (
    fetch_and_validate_scan_complete_file,
    move_pending_file_to_destination,
)
from src.services.opportunities.authorization import has_access
from src.services.opportunities.get_opportunity import get_opportunity
from src.util import file_util

logger = logging.getLogger(__name__)


def _get_competition(
    db_session: db.Session, opportunity_id: uuid.UUID, competition_id: uuid.UUID
) -> Competition:
    competition = db_session.execute(
        select(Competition).where(
            Competition.competition_id == competition_id,
            Competition.opportunity_id == opportunity_id,
        )
    ).scalar_one_or_none()
    if competition is None:
        raise_flask_error(
            404, f"Competition {competition_id} not found for opportunity {opportunity_id}"
        )
    return competition


def get_competition_instruction_path(
    opportunity_id: uuid.UUID,
    competition_id: uuid.UUID,
    competition_instruction_id: uuid.UUID,
    file_name: str,
) -> str:
    return file_util.join(
        S3Config().draft_files_bucket_path,
        "opportunities",
        str(opportunity_id),
        "competitions",
        str(competition_id),
        "instructions",
        str(competition_instruction_id),
        file_name,
    )


def upload_competition_instruction(
    db_session: db.Session,
    user: User,
    opportunity_id: uuid.UUID,
    competition_id: uuid.UUID,
    pending_file_id: uuid.UUID,
) -> CompetitionInstruction:
    opportunity = get_opportunity(db_session, opportunity_id)
    if not has_access(user, opportunity, "update"):
        raise_flask_error(403, "User does not have access to update this opportunity")
    _get_competition(db_session, opportunity_id, competition_id)
    pending_file = fetch_and_validate_scan_complete_file(db_session, pending_file_id, user)
    instruction_id = uuid.uuid4()
    secure_file_name = file_util.get_file_name(pending_file.file_location)
    file_location = get_competition_instruction_path(
        opportunity_id, competition_id, instruction_id, secure_file_name
    )
    file_attachment = FileAttachment(
        file_location=file_location,
        file_name=pending_file.file_name,
        mime_type=pending_file.mime_type,
        file_description=None,
        file_size_bytes=file_util.get_file_length_bytes(pending_file.file_location),
    )
    instruction = CompetitionInstruction(
        competition_instruction_id=instruction_id,
        competition_id=competition_id,
        file_attachment=file_attachment,
    )
    db_session.add(instruction)
    db_session.flush()
    move_pending_file_to_destination(pending_file, file_location)
    logger.info(
        "Added instruction to competition",
        extra={
            "competition_id": competition_id,
            "opportunity_id": opportunity_id,
            "competition_instruction_id": instruction_id,
        },
    )
    return db_session.execute(
        select(CompetitionInstruction)
        .where(CompetitionInstruction.competition_instruction_id == instruction_id)
        .options(selectinload(CompetitionInstruction.file_attachment))
    ).scalar_one()


def delete_competition_instruction(
    db_session: db.Session,
    user: User,
    opportunity_id: uuid.UUID,
    competition_id: uuid.UUID,
    competition_instruction_id: uuid.UUID,
) -> None:
    opportunity = get_opportunity(db_session, opportunity_id)
    if not has_access(user, opportunity, "update"):
        raise_flask_error(403, "User does not have access to update this opportunity")
    _get_competition(db_session, opportunity_id, competition_id)
    instruction = db_session.execute(
        select(CompetitionInstruction)
        .where(
            CompetitionInstruction.competition_id == competition_id,
            CompetitionInstruction.competition_instruction_id == competition_instruction_id,
        )
        .options(selectinload(CompetitionInstruction.file_attachment))
    ).scalar_one_or_none()
    if instruction is None:
        raise_flask_error(404, "Instruction not found")
    file_attachment = instruction.file_attachment
    file_location = file_attachment.file_location
    db_session.delete(instruction)
    db_session.delete(file_attachment)
    db_session.flush()
    file_util.delete_file(file_location)
    logger.info(
        "Deleted competition instruction",
        extra={
            "opportunity_id": opportunity_id,
            "competition_id": competition_id,
            "competition_instruction_id": competition_instruction_id,
        },
    )
