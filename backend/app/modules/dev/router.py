from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.ai.schemas.actions import Action
from app.db.session import get_db
from app.core.config import settings
from app.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.services.ai.action_engine import ActionEngine


def require_dev_mode():
    if not settings.ENABLE_DEV_ENDPOINTS:
        raise HTTPException(status_code=404, detail="Not Found")


router = APIRouter(
    prefix="/dev",
    tags=["Development"],
    dependencies=[Depends(require_dev_mode)],
    include_in_schema=False,
)


@router.post("/test-action-engine")
def test_action_engine(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    engine = ActionEngine(db)

    actions = [
        Action(
            type="task.create",
            payload={
                "title": "Finish Backend",
                "priority": "high",
                "deadline": "Tomorrow",
            },
        )
    ]

    result = engine.execute(
        user_id=current_user.id,
        actions=actions,
    )
    if result["executed"] != 1:
        raise HTTPException(status_code=500, detail="Test action failed")
    return {"message": "Task created"}
