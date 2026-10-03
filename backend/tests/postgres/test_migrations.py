from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

from app.db.database import Base
import app.models


def test_fresh_upgrade_matches_models(migration_connection):
    connection, config = migration_connection
    command.upgrade(config, "head")
    assert set(inspect(connection).get_table_names()) == set(Base.metadata.tables) | {
        "alembic_version"
    }
    assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []


def test_full_downgrade_and_reupgrade(migration_connection):
    connection, config = migration_connection
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    assert set(inspect(connection).get_table_names()) == {"alembic_version"}
    command.upgrade(config, "head")
    assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []


def test_populated_legacy_memory_upgrade_and_downgrade_preserve_text(
    migration_connection,
):
    connection, config = migration_connection
    command.upgrade(config, "ae6afdf6bbfe")
    connection.execute(
        text(
            "INSERT INTO users (id, name, email, password_hash) VALUES (1, 'Test', 'test@example.com', 'unused')"
        )
    )
    connection.execute(
        text(
            "INSERT INTO memories (user_id, category, key, value, importance) VALUES (1, 'work', 'language', 'Python', 5)"
        )
    )
    connection.commit()
    command.upgrade(config, "head")
    assert connection.execute(text("SELECT content, source FROM memories")).one() == (
        "Python",
        "chat",
    )
    connection.commit()
    command.downgrade(config, "ae6afdf6bbfe")
    assert (
        connection.execute(text("SELECT value FROM memories")).scalar_one() == "Python"
    )
    connection.commit()
    command.upgrade(config, "head")
    assert (
        connection.execute(text("SELECT content FROM memories")).scalar_one()
        == "Python"
    )
