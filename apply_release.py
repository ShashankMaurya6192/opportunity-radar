from __future__ import annotations

from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent


def backup(path: Path) -> None:
    if not path.exists():
        return
    target = path.with_suffix(path.suffix + ".v050.bak")
    if not target.exists():
        shutil.copy2(path, target)


def insert_after_import_block(text: str, imports: str) -> str:
    if "from .services.intelligence import report_from_company" in text:
        return text

    preferred = "from .services.discovery import discover_companies"
    if preferred in text:
        return text.replace(preferred, preferred + "\n" + imports, 1)

    fallback = "from .services.scheduler import scheduler"
    if fallback in text:
        return text.replace(fallback, fallback + "\n" + imports, 1)

    lines = text.splitlines()
    last_import = -1
    for index, line in enumerate(lines):
        if line.startswith(("import ", "from ")):
            last_import = index
    if last_import < 0:
        raise RuntimeError("Could not locate the import block in app/main.py")
    lines[last_import + 1:last_import + 1] = imports.splitlines()
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def patch_models() -> None:
    path = ROOT / "app/models.py"
    if not path.exists():
        raise RuntimeError("app/models.py was not found. Copy the patch into the repository root.")
    backup(path)
    text = path.read_text(encoding="utf-8")

    if "resume_text: Mapped[str]" not in text:
        marker = '    email_signature: Mapped[str] = mapped_column(Text, default="Best regards,\\nShashank")'
        if marker not in text:
            marker = "    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)"
            addition = '    resume_text: Mapped[str] = mapped_column(Text, default="")\n'
            if marker not in text:
                raise RuntimeError("Could not patch UserProfile in app/models.py")
            text = text.replace(marker, addition + marker, 1)
        else:
            text = text.replace(marker, marker + '\n    resume_text: Mapped[str] = mapped_column(Text, default="")', 1)

    if "intelligence_summary: Mapped[str]" not in text:
        marker = '    evidence: Mapped[str] = mapped_column(Text, default="")'
        addition = (
            '\n    intelligence_summary: Mapped[str] = mapped_column(Text, default="")'
            '\n    intelligence_json: Mapped[str] = mapped_column(Text, default="")'
            '\n    company_type: Mapped[str] = mapped_column(String(120), default="")'
            '\n    estimated_size: Mapped[str] = mapped_column(String(80), default="")'
            '\n    hiring_probability: Mapped[int] = mapped_column(Integer, default=0)'
            '\n    engineering_maturity: Mapped[int] = mapped_column(Integer, default=0)'
            '\n    outreach_probability: Mapped[int] = mapped_column(Integer, default=0)'
            '\n    risk_level: Mapped[str] = mapped_column(String(30), default="Low")'
        )
        if marker not in text:
            raise RuntimeError("Could not patch Company in app/models.py")
        text = text.replace(marker, marker + addition, 1)

    if "match_details: Mapped[str]" not in text:
        marker = '    skills: Mapped[str] = mapped_column(Text, default="")'
        addition = (
            '\n    description: Mapped[str] = mapped_column(Text, default="")'
            '\n    match_details: Mapped[str] = mapped_column(Text, default="")'
        )
        if marker not in text:
            raise RuntimeError("Could not patch Job in app/models.py")
        text = text.replace(marker, marker + addition, 1)

    path.write_text(text, encoding="utf-8")


def patch_main() -> None:
    path = ROOT / "app/main.py"
    if not path.exists():
        raise RuntimeError("app/main.py was not found. Copy the patch into the repository root.")
    backup(path)
    text = path.read_text(encoding="utf-8")

    imports = (
        "from .services.intelligence import report_from_company\n"
        "from .services.matching import match_company_jobs\n"
        "from .services.outreach_v2 import build_personalized_outreach"
    )
    text = insert_after_import_block(text, imports)

    if "company.intelligence_summary = intelligence.summary" not in text:
        marker = "    db.commit(); db.refresh(company)\n    return company"
        replacement = (
            "    intelligence = report_from_company(company)\n"
            "    company.intelligence_summary = intelligence.summary\n"
            "    company.intelligence_json = intelligence.as_json()\n"
            "    company.company_type = intelligence.company_type\n"
            "    company.estimated_size = intelligence.estimated_size\n"
            "    company.hiring_probability = intelligence.hiring_probability\n"
            "    company.engineering_maturity = intelligence.engineering_maturity\n"
            "    company.outreach_probability = intelligence.outreach_probability\n"
            "    company.risk_level = intelligence.risk_level\n"
            "    db.commit(); db.refresh(company)\n"
            "    return company"
        )
        if marker not in text:
            raise RuntimeError("Could not patch save_result in app/main.py")
        text = text.replace(marker, replacement, 1)

    if '@app.get("/resume"' not in text:
        routes_path = ROOT / "routes_v080.txt"
        routes = routes_path.read_text(encoding="utf-8")
        marker = '\n@app.get("/health")'
        if marker not in text:
            raise RuntimeError("Could not find the /health route in app/main.py")
        text = text.replace(marker, "\n" + routes.rstrip() + "\n" + marker, 1)

    path.write_text(text, encoding="utf-8")


def patch_navigation() -> None:
    path = ROOT / "app/templates/base.html"
    if not path.exists():
        raise RuntimeError("app/templates/base.html was not found.")
    backup(path)
    text = path.read_text(encoding="utf-8")
    if 'href="/resume"' not in text:
        exact = '<a href="/analytics" class="{{\'active\' if request.url.path==\'/analytics\' else \'\')}}">Analytics</a>'
        addition = exact + '\n<a href="/resume" class="{{\'active\' if request.url.path==\'/resume\' else \'\')}}">Resume Intelligence</a>'
        if exact in text:
            text = text.replace(exact, addition, 1)
        elif ">Analytics</a>" in text:
            text = text.replace(">Analytics</a>", ">Analytics</a>\n<a href=\"/resume\">Resume Intelligence</a>", 1)
        else:
            raise RuntimeError("Could not patch navigation in app/templates/base.html")
    path.write_text(text, encoding="utf-8")


def patch_version() -> None:
    for name in [".env", ".env.example"]:
        path = ROOT / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?m)^APP_VERSION=", text):
            text = re.sub(r"(?m)^APP_VERSION=.*$", "APP_VERSION=0.8.0", text)
        else:
            text += "\nAPP_VERSION=0.8.0\n"
        path.write_text(text, encoding="utf-8")


def ensure_alembic() -> None:
    required = [
        ROOT / "alembic.ini",
        ROOT / "alembic/env.py",
        ROOT / "alembic/script.py.mako",
        ROOT / "alembic/versions/20260721_0002_intelligence_matching_outreach.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Missing Alembic files: " + ", ".join(missing))


def main() -> None:
    patch_models()
    patch_main()
    patch_navigation()
    patch_version()
    ensure_alembic()
    print("Applied Opportunity Radar v0.6.0-v0.8.0 successfully.")
    print("Run: python -m alembic -c alembic.ini upgrade head")
    print("Then: pytest -q")


if __name__ == "__main__":
    main()
