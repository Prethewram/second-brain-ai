from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Profile(Base):

    __tablename__ = "profiles"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    name = Column(
        String(255),
        nullable=True,
    )

    occupation = Column(
        String(255),
        nullable=True,
    )

    company = Column(
        String(255),
        nullable=True,
    )

    timezone = Column(
        String(100),
        nullable=True,
    )

    language = Column(
        String(100),
        nullable=True,
    )

    bio = Column(
        String(1000),
        nullable=True,
    )

    goals = Column(
        String(1000),
        nullable=True,
    )

    interests = Column(
        String(1000),
        nullable=True,
    )

    skills = Column(
        String(1000),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    user = relationship(
        "User",
        back_populates="profile",
    )
