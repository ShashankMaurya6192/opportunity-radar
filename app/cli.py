from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from .config import settings
from .database import Base, SessionLocal, engine
from .models import DiscoveryCampaign, UserProfile


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if not db.get(UserProfile, 1):
            db.add(UserProfile(id=1))
        db.commit()
    print("Database initialized.")


def seed() -> None:
    init_db()
    defaults = [
        ("Remote Python companies", "Python backend development", "Remote"),
        ("Django agencies UK", "Django development agency", "United Kingdom"),
        ("AI automation startups", "AI automation startup", "United States"),
    ]
    with SessionLocal() as db:
        for name, query, country in defaults:
            exists = db.scalar(select(DiscoveryCampaign).where(DiscoveryCampaign.name == name))
            if not exists:
                db.add(DiscoveryCampaign(name=name, query=query, country=country, result_limit=15))
        db.commit()
    print("Demo discovery campaigns created.")


def backup() -> None:
    if not settings.database_url.startswith("sqlite:///"):
        raise SystemExit("Automatic backup currently supports SQLite databases only.")
    source = Path(settings.database_url.removeprefix("sqlite:///"))
    if not source.exists():
        raise SystemExit(f"Database not found: {source}")
    destination = Path("backups") / f"opportunity-radar-{datetime.now():%Y%m%d-%H%M%S}.db"
    destination.parent.mkdir(exist_ok=True)
    shutil.copy2(source, destination)
    print(f"Backup created: {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    parser.add_argument("command", choices=["init-db", "seed", "backup"])
    args = parser.parse_args()
    {"init-db": init_db, "seed": seed, "backup": backup}[args.command]()


if __name__ == "__main__":
    main()
