# Project setup and verification

## Windows

From PowerShell in the project root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
```

To set up and immediately start the app:

```powershell
.\setup.ps1 -Run
```

## Manual startup

```powershell
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## What CI verifies

GitHub Actions runs on every push and pull request using Python 3.11 and 3.12. It installs dependencies, upgrades a brand-new SQLite database through the complete Alembic chain, and runs the full test suite.

The migration test compares every SQLAlchemy table and column with the schema produced from an empty database. This catches missing migrations, broken revision chains, and model/schema drift.
