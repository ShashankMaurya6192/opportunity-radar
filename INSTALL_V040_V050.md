# Apply v0.4.0 + v0.5.0

From the repository root on branch `feature/project-foundation`:

```bat
python -m app.cli backup
```

Extract this patch into the repository root and allow replacement of files. Then run:

```bat
python apply_release.py
copy .env.example .env
pip install -r requirements.txt
alembic upgrade head
pytest -q
python -m app.cli seed
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/health` and confirm version `0.5.0`.

After validation:

```bat
git status
git add .
git commit -m "Add project foundation and discovery engine"
git push
```

The patch creates `app/main.py.bak` before modifying `app/main.py`. Delete the backup after validation or keep it outside Git.
