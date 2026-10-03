import json
from unittest.mock import Mock

import pytest

from app.ai.schemas.actions import Action
from app.common.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.profile import Profile
from app.models.user import User
from app.modules.profile.schemas import ProfileCreate, ProfileUpdate
from app.modules.profile.service import ProfileService
from app.services.ai.action_engine import ActionEngine
from app.services.ai.analyzer import AIAnalyzer


@pytest.fixture
def users(db_session):
    users = [
        User(name=name, email=f"{name}@example.com", password_hash="unused")
        for name in ("owner", "other")
    ]
    db_session.add_all(users)
    db_session.commit()
    return users


@pytest.fixture
def service(db_session):
    return ProfileService(db_session)


def test_create_and_get_persist_all_fields(service, users, db_session):
    data = dict(
        name="Ada",
        occupation="Engineer",
        company="Example",
        timezone="Asia/Calcutta",
        language="English",
        bio="Bio",
        goals="Goals",
        interests="Interests",
        skills="Python",
    )
    profile = service.create_profile(users[0].id, ProfileCreate(**data))
    db_session.expire_all()
    stored = service.get_profile(users[0].id)
    assert stored.id == profile.id
    assert stored.user_id == users[0].id
    assert {field: getattr(stored, field) for field in data} == data


def test_empty_profile_is_allowed(service, users):
    profile = service.create_profile(users[0].id, ProfileCreate())
    assert profile.name is None
    assert profile.bio is None


def test_duplicate_creation_is_rejected_without_modifying_existing(
    service, users, db_session
):
    service.create_profile(users[0].id, ProfileCreate(name="Original"))
    with pytest.raises(ConflictException):
        service.create_profile(users[0].id, ProfileCreate(name="Changed"))
    assert db_session.query(Profile).count() == 1
    assert service.get_profile(users[0].id).name == "Original"


@pytest.mark.parametrize("operation", ["get", "update", "delete"])
def test_missing_profile(service, users, operation):
    with pytest.raises(NotFoundException):
        if operation == "update":
            service.update_profile(users[0].id, ProfileUpdate(name="New"))
        else:
            getattr(service, f"{operation}_profile")(users[0].id)


def test_partial_update_preserves_omitted_fields_and_null_clears_supplied_field(
    service, users, db_session
):
    service.create_profile(
        users[0].id, ProfileCreate(name="Original", company="Example", skills="Python")
    )
    service.update_profile(users[0].id, ProfileUpdate(name="Updated", company=None))
    db_session.expire_all()
    stored = service.get_profile(users[0].id)
    assert (stored.name, stored.company, stored.skills) == ("Updated", None, "Python")


def test_upsert_creates_then_updates_same_profile(service, users, db_session):
    profile = service.upsert_profile(users[0].id, ProfileUpdate(company="Example"))
    updated = service.upsert_profile(users[0].id, ProfileUpdate(skills="Python"))
    assert updated.id == profile.id
    db_session.expire_all()
    assert (updated.company, updated.skills) == ("Example", "Python")
    assert db_session.query(Profile).count() == 1


def test_delete_removes_profile_and_allows_recreation(service, users, db_session):
    service.create_profile(users[0].id, ProfileCreate(name="Original"))
    service.delete_profile(users[0].id)
    assert db_session.query(Profile).count() == 0
    assert service.create_profile(users[0].id, ProfileCreate(name="New")).name == "New"


def test_users_profiles_are_isolated(service, users, db_session):
    service.create_profile(users[0].id, ProfileCreate(name="Owner"))
    with pytest.raises(NotFoundException):
        service.get_profile(users[1].id)
    service.upsert_profile(users[1].id, ProfileUpdate(name="Other"))
    service.update_profile(users[1].id, ProfileUpdate(company="Other company"))
    service.delete_profile(users[1].id)
    db_session.expire_all()
    assert service.get_profile(users[0].id).name == "Owner"
    assert service.get_profile(users[0].id).company is None


@pytest.mark.parametrize(
    "field,limit",
    [
        ("name", 255),
        ("occupation", 255),
        ("company", 255),
        ("timezone", 100),
        ("language", 100),
        ("bio", 1000),
        ("goals", 1000),
        ("interests", 1000),
        ("skills", 1000),
    ],
)
def test_column_lengths_are_validated_on_create(
    service, users, db_session, field, limit
):
    with pytest.raises(ValidationException):
        service.create_profile(users[0].id, ProfileCreate(**{field: "x" * (limit + 1)}))
    assert db_session.query(Profile).count() == 0
    profile = service.create_profile(users[0].id, ProfileCreate(**{field: "x" * limit}))
    assert len(getattr(profile, field)) == limit


@pytest.mark.parametrize("operation", ["update", "upsert"])
def test_invalid_update_leaves_object_and_database_unchanged(
    service, users, db_session, operation
):
    profile = service.create_profile(
        users[0].id, ProfileCreate(name="Original", bio="Original bio")
    )
    with pytest.raises(ValidationException):
        getattr(service, f"{operation}_profile")(
            users[0].id,
            ProfileUpdate(name="Changed", bio="x" * 1001),
        )
    assert profile.name == "Original"
    db_session.commit()
    db_session.expire_all()
    assert service.get_profile(users[0].id).bio == "Original bio"


def test_invalid_upsert_does_not_create(service, users, db_session):
    with pytest.raises(ValidationException):
        service.upsert_profile(users[0].id, ProfileUpdate(company="x" * 256))
    assert db_session.query(Profile).count() == 0


def test_service_rejects_non_string_fields_even_when_schema_validation_is_bypassed(
    service, users
):
    with pytest.warns(UserWarning, match="Pydantic serializer warnings"):
        with pytest.raises(ValidationException):
            service.create_profile(users[0].id, ProfileCreate.model_construct(name=123))


def test_ai_profile_actions_validate_and_upsert(users, db_session):
    result = ActionEngine(db_session).execute(
        users[0].id,
        [
            Action(type="profile.update", payload={"name": "Ada"}),
            Action(type="profile.update", payload={"company": "x" * 256}),
            Action(type="profile.update", payload={"skills": "Python"}),
        ],
    )
    assert result == {"executed": 2, "failed": 1, "skipped": 0}
    profile = db_session.query(Profile).one()
    assert (profile.name, profile.skills, profile.company) == ("Ada", "Python", None)


def test_analyzer_retains_profile_actions_and_describes_all_registered_actions(
    monkeypatch, users, db_session
):
    ai = Mock()
    ai.chat.return_value = json.dumps(
        {
            "actions": [
                {"type": "profile.update", "payload": {"occupation": "Engineer"}},
                {"type": "unknown.action", "payload": {}},
            ]
        }
    )
    monkeypatch.setattr("app.services.ai.analyzer.AIClient", lambda: ai)
    analysis = AIAnalyzer().analyze("I work as an engineer")
    assert [action.type for action in analysis.actions] == ["profile.update"]
    prompt = ai.chat.call_args.args[0][0]["content"]
    for action_type in (
        "memory.create",
        "task.create",
        "note.create",
        "profile.update",
    ):
        assert action_type in prompt
    result = ActionEngine(db_session).execute(users[0].id, analysis.actions)
    assert result["executed"] == 1
    assert db_session.query(Profile).one().occupation == "Engineer"
