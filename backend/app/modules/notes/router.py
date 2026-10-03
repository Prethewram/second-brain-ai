from fastapi import APIRouter, Depends, status

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.notes.schemas import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
)
from app.modules.notes.service import NoteService

router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
)


# create
@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    body: NoteCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):

    service = NoteService(db)

    return service.create_note(
        user_id=current_user.id,
        title=body.title,
        content=body.content,
        category=body.category,
    )


# get
@router.get(
    "",
    response_model=list[NoteResponse],
)
def list_notes(
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):

    service = NoteService(db)

    return service.list_notes(
        current_user.id,
    )


# get by id
@router.get(
    "/{note_id}",
    response_model=NoteResponse,
)
def get_note(
    note_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):

    service = NoteService(db)

    return service.get_note(
        user_id=current_user.id,
        note_id=note_id,
    )


# update
@router.patch(
    "/{note_id}",
    response_model=NoteResponse,
)
def update_note(
    note_id: int,
    body: NoteUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):

    service = NoteService(db)

    return service.update_note(
        user_id=current_user.id,
        note_id=note_id,
        **body.model_dump(exclude_unset=True),
    )


# archive
@router.patch(
    "/{note_id}/archive",
)
def archive_note(
    note_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):

    service = NoteService(db)

    service.archive_note(
        current_user.id,
        note_id,
    )

    return {"message": "Note archived successfully."}


# delete
@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_note(
    note_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):

    service = NoteService(db)

    service.delete_note(
        current_user.id,
        note_id,
    )
