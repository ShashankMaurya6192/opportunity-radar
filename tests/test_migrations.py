from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_fresh_database_migrates_to_head(tmp_path: Path) -> None:
    database_path = tmp_path / "fresh.db"
    database_url = f"sqlite:///{database_path.as_posix()}"

    env = os.environ.copy()
    env["OR_DATABASE_URL"] = database_url

    migration = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "alembic.ini",
            "upgrade",
            "head",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert migration.returncode == 0, (
        "Fresh-database migration failed.\n"
        f"STDOUT:\n{migration.stdout}\n"
        f"STDERR:\n{migration.stderr}"
    )

    verification_code = r'''
from sqlalchemy import inspect
from app.database import Base, engine
import app.models  # noqa: F401

inspector = inspect(engine)
database_tables = set(inspector.get_table_names())
problems = []

for table_name, table in Base.metadata.tables.items():
    if table_name not in database_tables:
        problems.append(f"missing table: {table_name}")
        continue

    actual_columns = {
        column["name"]
        for column in inspector.get_columns(table_name)
    }

    for column in table.columns:
        if column.name not in actual_columns:
            problems.append(
                f"missing column: {table_name}.{column.name}"
            )

if problems:
    raise SystemExit("\n".join(problems))

print("schema-ok")
'''

    verification = subprocess.run(
        [sys.executable, "-c", verification_code],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert verification.returncode == 0, (
        "Migrated schema does not match SQLAlchemy models.\n"
        f"STDOUT:\n{verification.stdout}\n"
        f"STDERR:\n{verification.stderr}"
    )
    assert "schema-ok" in verification.stdout
