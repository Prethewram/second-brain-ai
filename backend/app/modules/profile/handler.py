from app.modules.profile.schemas import (
    ProfileUpdate,
)
from app.modules.profile.service import (
    ProfileService,
)
from app.services.ai.handlers.base_handler import BaseHandler


class ProfileHandler(BaseHandler):

    def __init__(self, db):

        super().__init__(ProfileService(db))

    def execute(
        self,
        user_id: int,
        payload: dict,
    ):

        profile = ProfileUpdate(**payload)

        self.service.upsert_profile(
            user_id=user_id,
            profile=profile,
        )
