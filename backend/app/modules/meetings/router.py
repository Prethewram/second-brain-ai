from fastapi import APIRouter, Depends

from app.db.session import get_db
from app.models.meeting import Meeting
from app.models.notes import Note
from app.models.task import Task
from app.modules.auth.dependencies import get_current_user
from app.modules.meetings.schemas import MeetingDetail, MeetingResponse, MeetingWrite
from app.modules.meetings.service import get_owned_meeting
from app.modules.notes.schemas import NoteCreate, NoteResponse
from app.modules.notes.service import NoteService
from app.modules.tasks.schema import TaskCreate, TaskResponse
from app.modules.tasks.service import TaskService

router = APIRouter(prefix="/meetings", tags=["Meeting minutes"])


@router.get("", response_model=list[MeetingResponse])
def list_meetings(db=Depends(get_db), user=Depends(get_current_user)):
    return (
        db.query(Meeting)
        .filter_by(user_id=user.id)
        .order_by(Meeting.created_at.desc(), Meeting.id.desc())
        .all()
    )


@router.post("", response_model=MeetingResponse, status_code=201)
def create_meeting(
    body: MeetingWrite, db=Depends(get_db), user=Depends(get_current_user)
):
    meeting = Meeting(user_id=user.id, **body.model_dump())
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("/{meeting_id}", response_model=MeetingDetail)
def get_meeting(meeting_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    meeting = get_owned_meeting(db, user.id, meeting_id)
    result = MeetingResponse.model_validate(meeting).model_dump()
    result["notes"] = (
        db.query(Note)
        .filter_by(user_id=user.id, meeting_id=meeting.id)
        .order_by(Note.id.desc())
        .all()
    )
    result["tasks"] = (
        db.query(Task)
        .filter_by(user_id=user.id, meeting_id=meeting.id)
        .order_by(Task.id.desc())
        .all()
    )
    return result


@router.put("/{meeting_id}", response_model=MeetingResponse)
def update_meeting(
    meeting_id: int,
    body: MeetingWrite,
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    meeting = get_owned_meeting(db, user.id, meeting_id)
    for key, value in body.model_dump().items():
        setattr(meeting, key, value)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.delete("/{meeting_id}", status_code=204)
def delete_meeting(meeting_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    db.delete(get_owned_meeting(db, user.id, meeting_id))
    db.commit()


@router.post("/{meeting_id}/notes", response_model=NoteResponse, status_code=201)
def add_note(
    meeting_id: int,
    body: NoteCreate,
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    return NoteService(db).create_note(
        user.id, **body.model_dump(), source="meeting", meeting_id=meeting_id
    )


@router.post("/{meeting_id}/tasks", response_model=TaskResponse, status_code=201)
def add_task(
    meeting_id: int,
    body: TaskCreate,
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    return TaskService(db).create_task(
        user.id, **body.model_dump(), meeting_id=meeting_id
    )
