from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.profile.schemas import (
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)
from app.modules.profile.service import ProfileService

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)


# get profile
@router.get(
    "",
    response_model=ProfileResponse,
)
def get_profile(
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):

    service = ProfileService(db)

    return service.get_profile(
        current_user.id,
    )


# post
@router.post(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    body: ProfileCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):

    service = ProfileService(db)

    return service.create_profile(
        user_id=current_user.id,
        profile=body,
    )


# update
@router.patch(
    "",
    response_model=ProfileResponse,
)
def update_profile(
    body: ProfileUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):

    service = ProfileService(db)

    return service.upsert_profile(
        user_id=current_user.id,
        profile=body,
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    ProfileService(db).delete_profile(current_user.id)
