from pathlib import Path
import re

path = Path("alembic/versions/20260721_01_discovery_engine.py")
text = path.read_text(encoding="utf-8")

updated = re.sub(
    r",\s*partial_reordering\s*=\s*\[[^\]]*\]",
    "",
    text,
    flags=re.DOTALL,
)

updated = re.sub(
    r",\s*partial_reordering\s*=\s*\([^\)]*\)",
    "",
    updated,
    flags=re.DOTALL,
)

if updated == text:
    print("No partial_reordering argument was removed.")
    print("Current migration content:")
    print(text)
else:
    path.write_text(updated, encoding="utf-8")
    print("Removed partial_reordering successfully.")
