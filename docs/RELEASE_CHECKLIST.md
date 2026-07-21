# Release Checklist

1. Copy `.env.example` to `.env` and review values.
2. Install dependencies with `pip install -r requirements.txt`.
3. Back up the existing database with `python -m app.cli backup`.
4. Run `alembic upgrade head`.
5. Run `pytest -q`.
6. Start the application and check `/health`.
7. Run one manual discovery and one saved campaign.
8. Review `git diff`, commit and push the feature branch.
