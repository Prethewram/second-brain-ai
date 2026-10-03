from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.modules.auth.schemas import RegisterRequest
from app.modules.auth.service import create_user


def test_registration_race_rolls_back_and_returns_duplicate_error(
    db_session, monkeypatch
):
    data = RegisterRequest(
        name="Original", email="test@example.com", password="password"
    )
    user = create_user(db_session, data)
    original_query = db_session.query
    first_query = True

    def stale_first_lookup(*args, **kwargs):
        nonlocal first_query
        if first_query:
            first_query = False
            query = Mock()
            query.filter.return_value.first.return_value = None
            return query
        return original_query(*args, **kwargs)

    monkeypatch.setattr(db_session, "query", stale_first_lookup)
    with pytest.raises(ValueError, match="Email already registered"):
        create_user(
            db_session,
            RegisterRequest(name="Changed", email=data.email, password="different"),
        )
    assert original_query(User).count() == 1
    assert db_session.get(User, user.id).name == "Original"
    # The failed registration must not leave the session in a failed transaction.
    db_session.add(
        User(name="Other", email="other@example.com", password_hash="unused")
    )
    db_session.commit()


def test_unrelated_integrity_error_is_not_misreported_as_duplicate(
    db_session, monkeypatch
):
    failure = IntegrityError("insert", {}, RuntimeError("Unrelated constraint"))
    monkeypatch.setattr(db_session, "commit", Mock(side_effect=failure))
    with pytest.raises(IntegrityError) as caught:
        create_user(
            db_session,
            RegisterRequest(name="Test", email="test@example.com", password="password"),
        )
    assert caught.value is failure
    assert db_session.query(User).count() == 0
