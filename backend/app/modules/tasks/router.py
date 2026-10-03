from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.modules.tasks.schema import TaskCreate, TaskResponse, TaskUpdate
from app.modules.tasks.service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    body: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return TaskService(db).create_task(user_id=user.id, **body.model_dump())


@router.get("", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return TaskService(db).list_tasks(user.id)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return TaskService(db).get_task(user.id, task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    body: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return TaskService(db).update_task(
        user.id, task_id, **body.model_dump(exclude_unset=True)
    )


@router.patch("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return TaskService(db).complete_task(user.id, task_id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    TaskService(db).delete_task(user.id, task_id)
