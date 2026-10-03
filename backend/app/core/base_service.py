from app.common.exceptions import (
    NotFoundException,
    UnauthorizedException,
)


class BaseService:

    def __init__(self, repository):

        self.repository = repository

    def get_or_404(
        self,
        obj_id: int,
    ):

        obj = self.repository.get(obj_id)

        if obj is None:
            raise NotFoundException("Resource not found.")

        return obj

    def verify_owner(
        self,
        obj,
        user_id: int,
    ):

        if obj.user_id != user_id:
            raise UnauthorizedException(
                "You do not have permission to access this resource."
            )

        return obj

    def update_fields(
        self,
        obj,
        data: dict,
    ):

        for field, value in data.items():
            setattr(
                obj,
                field,
                value,
            )

        return obj

    def exists(
        self,
        **filters,
    ) -> bool:

        return self.repository.exists(**filters)

    def get_by(
        self,
        **filters,
    ):

        return self.repository.get_by(**filters)

    def list_by(
        self,
        **filters,
    ):

        return self.repository.list_by(**filters)
