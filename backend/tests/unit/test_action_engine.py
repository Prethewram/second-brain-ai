import logging
from unittest.mock import Mock, call

import pytest

from app.ai.schemas.actions import Action
from app.services.ai.action_engine import ActionEngine


def make_engine(handlers):
    registry = Mock()
    registry.get.side_effect = handlers.get
    return ActionEngine(db=None, registry=registry)


def test_registered_action_receives_user_and_payload(caplog):
    handler = Mock()
    payload = {"title": "Finish backend", "priority": "high"}
    engine = make_engine({"task.create": handler})
    with caplog.at_level(logging.INFO, logger="secondbrain"):
        result = engine.execute(42, [Action(type="task.create", payload=payload)])
    handler.execute.assert_called_once_with(user_id=42, payload=payload)
    assert result == {"executed": 1, "failed": 0, "skipped": 0}
    assert "Executed action 'task.create' successfully" in caplog.text


def test_unknown_action_is_skipped_and_later_action_runs(caplog):
    handler = Mock()
    engine = make_engine({"note.create": handler})
    with caplog.at_level(logging.WARNING, logger="secondbrain"):
        result = engine.execute(
            7,
            [
                Action(type="unknown.action"),
                Action(type="note.create", payload={"title": "Idea"}),
            ],
        )
    handler.execute.assert_called_once_with(user_id=7, payload={"title": "Idea"})
    assert result == {"executed": 1, "failed": 0, "skipped": 1}
    assert "No handler registered for action 'unknown.action'" in caplog.text


def test_failure_does_not_stop_subsequent_actions(caplog):
    failing = Mock()
    failing.execute.side_effect = ValueError("Invalid task")
    successful = Mock()
    engine = make_engine({"task.create": failing, "note.create": successful})
    with caplog.at_level(logging.ERROR, logger="secondbrain"):
        result = engine.execute(
            7,
            [
                Action(type="task.create"),
                Action(type="note.create", payload={"title": "Keep going"}),
            ],
        )
    successful.execute.assert_called_once_with(
        user_id=7, payload={"title": "Keep going"}
    )
    assert result == {"executed": 1, "failed": 1, "skipped": 0}
    assert any(
        record.exc_info and "task.create" in record.message for record in caplog.records
    )


def test_empty_actions_return_zero_counts(caplog):
    engine = make_engine({})
    with caplog.at_level(logging.INFO, logger="secondbrain"):
        result = engine.execute(7, [])
    engine.registry.get.assert_not_called()
    assert result == {"executed": 0, "failed": 0, "skipped": 0}
    assert "executed=0, failed=0, skipped=0" in caplog.text


def test_repeated_actions_execute_in_order_and_counts_reset():
    handler = Mock()
    engine = make_engine({"note.create": handler})
    actions = [
        Action(type="note.create", payload={"title": title})
        for title in ["First", "Second"]
    ]
    assert engine.execute(7, actions) == {"executed": 2, "failed": 0, "skipped": 0}
    assert handler.execute.call_args_list == [
        call(user_id=7, payload={"title": "First"}),
        call(user_id=7, payload={"title": "Second"}),
    ]
    assert engine.execute(7, []) == {"executed": 0, "failed": 0, "skipped": 0}


def test_mixed_batch_reports_each_outcome_once(caplog):
    failing = Mock()
    failing.execute.side_effect = RuntimeError("Handler failed")
    successful = Mock()
    engine = make_engine({"task.create": failing, "note.create": successful})
    with caplog.at_level(logging.INFO, logger="secondbrain"):
        result = engine.execute(
            7,
            [
                Action(type="task.create"),
                Action(type="unsupported"),
                Action(type="note.create"),
                Action(type="note.create"),
            ],
        )
    assert result == {"executed": 2, "failed": 1, "skipped": 1}
    assert failing.execute.call_count == 1
    assert successful.execute.call_count == 2
    assert "executed=2, failed=1, skipped=1" in caplog.text


def test_database_failure_is_rolled_back_and_later_real_action_succeeds(db_session):
    from app.models.memory import Memory
    from app.models.user import User
    from app.services.ai.registry import HandlerRegistry

    user = User(name="Test", email="test@example.com", password_hash="unused")
    db_session.add(user)
    db_session.commit()
    user_id = user.id
    registry = HandlerRegistry(db_session)
    failing = Mock()

    def invalid_insert(**kwargs):
        db_session.add(Memory(user_id=user_id, content=None))
        db_session.commit()  # Real NOT NULL violation leaves the session unusable.

    failing.execute.side_effect = invalid_insert
    registry._handlers["test.database-failure"] = failing
    result = ActionEngine(db_session, registry).execute(
        user_id,
        [
            Action(type="memory.create", payload={"content": "Before"}),
            Action(type="test.database-failure"),
            Action(type="memory.create", payload={"content": "After"}),
        ],
    )
    assert result == {"executed": 2, "failed": 1, "skipped": 0}
    assert [m.content for m in db_session.query(Memory).order_by(Memory.id)] == [
        "Before",
        "After",
    ]


def test_handler_failure_discards_pending_changes_before_next_action(db_session):
    from app.models.user import User

    failing, successful = Mock(), Mock()

    def fail_after_staging(**kwargs):
        db_session.add(
            User(
                name="Uncommitted", email="pending@example.com", password_hash="unused"
            )
        )
        raise ValueError("Rejected action")

    def commit_next_action(**kwargs):
        db_session.add(
            User(name="Valid", email="valid@example.com", password_hash="unused")
        )
        db_session.commit()

    failing.execute.side_effect = fail_after_staging
    successful.execute.side_effect = commit_next_action
    registry = Mock()
    registry.get.side_effect = {"fail": failing, "success": successful}.get
    result = ActionEngine(db_session, registry).execute(
        1, [Action(type="fail"), Action(type="success")]
    )
    assert result == {"executed": 1, "failed": 1, "skipped": 0}
    assert [user.name for user in db_session.query(User)] == ["Valid"]


def test_rollback_failure_stops_execution_and_is_logged(caplog):
    db = Mock()
    db.rollback.side_effect = RuntimeError("Connection lost")
    failing, successful = Mock(), Mock()
    failing.execute.side_effect = ValueError("Action failed")
    registry = Mock()
    registry.get.side_effect = {"fail": failing, "success": successful}.get
    with caplog.at_level(logging.ERROR, logger="secondbrain"):
        with pytest.raises(RuntimeError, match="Connection lost"):
            ActionEngine(db, registry).execute(
                1, [Action(type="fail"), Action(type="success")]
            )
    successful.execute.assert_not_called()
    assert "rollback" in caplog.text.lower()
