from math import ceil

from pydantic import BaseModel


class PaginationParams(BaseModel):

    page: int = 1

    limit: int = 20


class PaginatedResponse(BaseModel):

    items: list

    total: int

    page: int

    limit: int

    pages: int

    has_next: bool

    has_previous: bool


def paginate(
    query,
    page: int,
    limit: int,
):

    total = query.count()

    items = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": ceil(total / limit) if total else 1,
        "has_next": page * limit < total,
        "has_previous": page > 1,
    }
