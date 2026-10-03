from io import StringIO
from pathlib import Path

from alembic import command
from alembic.config import Config


def test_offline_postgres_migrations_generate_without_database_access():
    output = StringIO()
    config = Config(
        str(Path(__file__).resolve().parents[2] / "alembic.ini"), output_buffer=output
    )
    config.attributes["database_url"] = (
        "postgresql://unused:unused@localhost/second_brain_test"
    )
    command.upgrade(config, "head", sql=True)
    sql = output.getvalue()
    assert "CREATE TABLE users" in sql
    assert "CREATE TABLE profiles" in sql
    assert "UPDATE memories SET content = value" in sql
