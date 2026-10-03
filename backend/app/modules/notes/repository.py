from sqlalchemy.orm import Session

from app.core.base_repository import BaseRepository
from app.models.notes import Note


class NoteRepository(BaseRepository[Note]):

    def __init__(self, db: Session):

        super().__init__(db, Note)

    def create(
        self,
        user_id: int,
        title: str,
        content: str,
        category: str = "general",
        source: str = "manual",
    ) -> Note:

        return super().create(
            user_id=user_id,
            title=title,
            content=content,
            category=category,
            source=source,
        )

    def get(
        self,
        note_id: int,
    ) -> Note | None:

        # Preserve the existing note_id keyword for repository callers.
        return super().get(note_id)

    def list_by_user(
        self,
        user_id: int,
    ) -> list[Note]:

        return (
            self.db.query(Note)
            .filter(
                Note.user_id == user_id,
                Note.is_archived.is_(False),
            )
            .order_by(Note.created_at.desc())
            .all()
        )

    def update(
        self,
        note: Note,
    ) -> Note:

        return super().update(note)

    def archive(
        self,
        note: Note,
    ) -> Note:

        note.is_archived = True

        return self.update(note)

    def delete(
        self,
        note: Note,
    ) -> None:

        return super().delete(note)
