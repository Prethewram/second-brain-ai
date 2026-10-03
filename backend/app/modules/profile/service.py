from app.common.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)

from app.core.base_service import BaseService
from app.modules.profile.repository import ProfileRepository
from app.modules.profile.schemas import (
    ProfileCreate,
    ProfileUpdate,
)


class ProfileService(BaseService):

    FIELD_LIMITS = {
        "name": 255,
        "occupation": 255,
        "company": 255,
        "timezone": 100,
        "language": 100,
        "bio": 1000,
        "goals": 1000,
        "interests": 1000,
        "skills": 1000,
    }

    def __init__(self, db):

        super().__init__(ProfileRepository(db))

    def _validated_data(self, profile, *, exclude_unset=False):
        data = profile.model_dump(exclude_unset=exclude_unset)
        for field, value in data.items():
            if value is None:
                continue
            if not isinstance(value, str):
                raise ValidationException(
                    f"{field.capitalize()} must be a string or null."
                )
            limit = self.FIELD_LIMITS[field]
            if len(value) > limit:
                raise ValidationException(
                    f"{field.capitalize()} cannot exceed {limit} characters."
                )
        return data

    def create_profile(
        self,
        user_id: int,
        profile: ProfileCreate,
    ):

        existing = self.repository.get_by_user(user_id)

        if existing:
            raise ConflictException("Profile already exists.")

        return self.repository.create(
            user_id=user_id,
            **self._validated_data(profile),
        )

    def get_profile(
        self,
        user_id: int,
    ):

        profile = self.repository.get_by_user(user_id)

        if profile is None:
            raise NotFoundException("Profile not found.")

        return profile

    def update_profile(
        self,
        user_id: int,
        profile: ProfileUpdate,
    ):

        existing = self.get_profile(user_id)

        self.update_fields(
            existing,
            self._validated_data(profile, exclude_unset=True),
        )

        return self.repository.update(existing)

    def upsert_profile(
        self,
        user_id: int,
        profile: ProfileUpdate,
    ):

        data = self._validated_data(profile, exclude_unset=True)
        existing = self.repository.get_by_user(user_id)

        if existing is None:

            return self.repository.create(
                user_id=user_id,
                **data,
            )

        self.update_fields(
            existing,
            data,
        )

        return self.repository.update(existing)

    def delete_profile(
        self,
        user_id: int,
    ):

        profile = self.get_profile(user_id)

        self.repository.delete(profile)
