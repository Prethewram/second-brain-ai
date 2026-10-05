from app.common.exceptions import NotFoundException
from app.models.meeting import Meeting


def get_owned_meeting(db, user_id, meeting_id):
    meeting = db.query(Meeting).filter_by(id=meeting_id, user_id=user_id).first()
    if meeting is None:
        raise NotFoundException("Meeting not found")
    return meeting
