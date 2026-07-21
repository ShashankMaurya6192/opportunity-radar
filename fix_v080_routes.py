from pathlib import Path

main_path = Path("app/main.py")
routes_path = Path("routes_v080.txt")

main_text = main_path.read_text(encoding="utf-8")
routes_text = routes_path.read_text(encoding="utf-8").strip()

if '@app.get("/resume"' in main_text:
    print("v0.8 routes are already present.")
else:
    with main_path.open("a", encoding="utf-8") as file:
        file.write("\n\n")
        file.write(routes_text)
        file.write("\n")

    print("v0.8 routes appended successfully.")
