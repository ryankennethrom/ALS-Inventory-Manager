from pathlib import Path

def get_migrations() -> list[str]:
    migrations_file = Path("./Resources/Database/migrations.data")

    # Create parent directories if they don't exist
    migrations_file.parent.mkdir(parents=True, exist_ok=True)

    # Create the file if it doesn't exist
    migrations_file.touch(exist_ok=True)

    # Return migrations as a list of strings
    with migrations_file.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines()]
