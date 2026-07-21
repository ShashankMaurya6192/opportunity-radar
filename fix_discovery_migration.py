from pathlib import Path
import re

path = Path("alembic/versions/20260721_01_discovery_engine.py")
text = path.read_text(encoding="utf-8")

updated = re.sub(
    r",\s*insert_(?:after|before)\s*=\s*[\"'][^\"']+[\"']",
    "",
    text,
)

if updated == text:
    print("No insert_after/insert_before arguments found.")
else:
    path.write_text(updated, encoding="utf-8")
    print("Removed SQLite column-ordering hints successfully.")
