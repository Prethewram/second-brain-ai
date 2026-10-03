from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.modules.memory.schemas import (
    MemoryResponse,
    MemoryUpdate,
)
from app.modules.memory.service import MemoryService

router = APIRouter(
    prefix="/memory",
    tags=["Memory"],
)


@router.get(
    "",
    response_model=list[MemoryResponse],
)
def list_memories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service = MemoryService(db)

    return service.list_memories(current_user.id)


@router.put(
    "/{memory_id}",
    response_model=MemoryResponse,
)
def update_memory(
    memory_id: int,
    body: MemoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service = MemoryService(db)

    return service.update_memory(
        current_user.id,
        memory_id,
        body,
    )


@router.delete("/{memory_id}")
def delete_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service = MemoryService(db)

    service.delete_memory(
        current_user.id,
        memory_id,
    )

    return {"message": "Memory deleted"}
