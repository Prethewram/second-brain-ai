from app.common.exceptions import ValidationException
from app.core.base_service import BaseService
from app.modules.notes.repository import NoteRepository


class NoteService(BaseService):

    def __init__(self, db):

        super().__init__(NoteRepository(db))

    @staticmethod
    def _validate_text(value, field, max_length=None):
        if not isinstance(value, str) or not value.strip():
            raise ValidationException(f"{field} cannot be empty.")
        value = value.strip()
        if max_length is not None and len(value) > max_length:
            raise ValidationException(f"{field} cannot exceed {max_length} characters.")
        return value

    def create_note(
        self,
        user_id: int,
        title: str,
        content: str,
        category: str = "general",
        source: str = "manual",
    ):

        title = self._validate_text(title, "Title", 255)
        content = self._validate_text(content, "Content")
        category = self._validate_text(category, "Category", 100).lower()
        source = self._validate_text(source, "Source", 50)

        return self.repository.create(
            user_id=user_id,
            title=title,
            content=content,
            category=category,
            source=source,
        )

    def get_note(
        self,
        user_id: int,
        note_id: int,
    ):

        note = self.get_or_404(note_id)

        self.verify_owner(
            note,
            user_id,
        )

        return note

    def list_notes(
        self,
        user_id: int,
    ):

        return self.repository.list_by_user(user_id)

    def update_note(
        self,
        user_id: int,
        note_id: int,
        **kwargs,
    ):

        note = self.get_note(
            user_id=user_id,
            note_id=note_id,
        )

        # Validate the whole patch before mutating the session's tracked object.
        changes = {}
        for field, max_length in (("title", 255), ("content", None), ("category", 100)):
            if kwargs.get(field) is not None:
                value = self._validate_text(
                    kwargs[field], field.capitalize(), max_length
                )
                changes[field] = value.lower() if field == "category" else value
        if kwargs.get("is_archived") is not None:
            if not isinstance(kwargs["is_archived"], bool):
                raise ValidationException("Archived status must be a boolean.")
            changes["is_archived"] = kwargs["is_archived"]
        self.update_fields(note, changes)
        return self.repository.update(note)

    def archive_note(
        self,
        user_id: int,
        note_id: int,
    ):

        note = self.get_note(
            user_id=user_id,
            note_id=note_id,
        )

        return self.repository.archive(note)

    def delete_note(
        self,
        user_id: int,
        note_id: int,
    ):

        note = self.get_note(
            user_id=user_id,
            note_id=note_id,
        )

        self.repository.delete(note)
