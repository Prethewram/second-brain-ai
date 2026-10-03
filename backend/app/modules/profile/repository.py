from sqlalchemy.orm import Session

from app.core.base_repository import BaseRepository
from app.models.profile import Profile


class ProfileRepository(BaseRepository[Profile]):

    def __init__(self, db: Session):

        super().__init__(db, Profile)

    def create(
        self,
        **kwargs,
    ) -> Profile:

        return super().create(**kwargs)

    def get_by_user(
        self,
        user_id: int,
    ) -> Profile | None:

        return self.db.query(Profile).filter(Profile.user_id == user_id).first()

    def update(
        self,
        profile: Profile,
    ) -> Profile:

        return super().update(profile)

    def delete(
        self,
        profile: Profile,
    ):

        return super().delete(profile)
