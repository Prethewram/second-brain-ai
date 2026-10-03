"""Check the safety properties relied on by the rest of the test suite."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.profile import Profile
from app.models.user import User


@pytest.mark.parametrize("run", [1, 2])
def test_commits_do_not_leak_between_tests(db_session, run):
    assert db_session.query(User).count() == 0
    db_session.add(User(name="Test", email="same@example.com", password_hash="unused"))
    db_session.commit()
    assert db_session.query(User).count() == 1


def test_test_database_enforces_foreign_keys(db_session):
    db_session.add(Profile(user_id=999))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_live_ai_calls_are_blocked():
    from app.ai.client import AIClient

    with pytest.raises(AssertionError, match="Live AI calls are forbidden"):
        AIClient().chat([{"role": "user", "content": "Test"}])
