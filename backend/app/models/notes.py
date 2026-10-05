from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.db.database import Base


def utc_now():
    # Existing columns are TIMESTAMP WITHOUT TIME ZONE; keep their UTC convention.
    return datetime.now(UTC).replace(tzinfo=None)


class Note(Base):

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(
        Integer,
        ForeignKey("meetings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    category = Column(
        String(100),
        default="general",
    )

    source = Column(
        String(50),
        default="manual",
    )

    is_archived = Column(
        Boolean,
        default=False,
    )

    created_at = Column(
        DateTime,
        default=utc_now,
    )

    updated_at = Column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )
