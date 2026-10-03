import pytest

from app.core.base_repository import BaseRepository
from app.core.base_service import BaseService
from app.models.task import Task
from app.models.user import User


@pytest.fixture
def repository(db_session):
    users = [
        User(name=name, email=f"{name}@example.com", password_hash="unused")
        for name in ("owner", "other")
    ]
    db_session.add_all(users)
    db_session.commit()
    repository = BaseRepository(db_session, Task)
    repository.create(user_id=users[0].id, title="Shared", priority="high")
    repository.create(
        user_id=users[0].id, title="Second", priority="low", deadline="Friday"
    )
    repository.create(user_id=users[1].id, title="Shared", priority="low")
    return repository, users


def test_get_by_combines_filters_and_returns_none_for_missing(repository):
    repo, users = repository
    task = repo.get_by(user_id=users[0].id, title="Shared")
    assert task.priority == "high"
    assert repo.get_by(user_id=users[0].id, title="Missing") is None
    assert repo.get_by(user_id=users[0].id, title="Shared", priority="low") is None


def test_list_by_is_scoped_and_combines_filters(repository):
    repo, users = repository
    assert {task.title for task in repo.list_by(user_id=users[0].id)} == {
        "Shared",
        "Second",
    }
    assert [
        task.title for task in repo.list_by(user_id=users[0].id, priority="low")
    ] == ["Second"]
    assert repo.list_by(user_id=users[0].id, priority="medium") == []


def test_exists_returns_boolean_and_honors_all_filters(repository):
    repo, users = repository
    assert repo.exists(user_id=users[0].id, title="Shared") is True
    assert repo.exists(user_id=users[0].id, title="Shared", priority="low") is False


def test_null_filters_match_nullable_fields(repository):
    repo, users = repository
    assert [
        task.title for task in repo.list_by(user_id=users[0].id, deadline=None)
    ] == ["Shared"]
    assert repo.exists(user_id=users[0].id, deadline=None) is True


def test_unfiltered_helpers_and_existing_list(repository):
    repo, _ = repository
    assert len(repo.list()) == 3
    assert len(repo.list_by()) == 3
    assert repo.get_by() is not None
    assert repo.exists() is True


def test_helpers_on_empty_table(db_session):
    repo = BaseRepository(db_session, Task)
    assert repo.exists() is False
    assert repo.get_by() is None
    assert repo.list_by() == []


def test_base_service_helpers_delegate_to_real_repository(repository):
    repo, users = repository
    service = BaseService(repo)
    task = service.get_by(user_id=users[0].id, title="Shared")
    assert task.priority == "high"
    assert service.exists(user_id=users[0].id, priority="high") is True
    assert service.exists(user_id=users[1].id, priority="high") is False
    assert len(service.list_by(user_id=users[0].id)) == 2
