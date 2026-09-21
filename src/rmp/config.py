"""Project configuration helpers."""

import os

from dotenv import load_dotenv


def get_database_config() -> dict[str, str | int]:
    """Return Supabase PostgreSQL connection settings."""
    load_dotenv()

    config = {
        "host": os.getenv("SUPABASE_DB_HOST"),
        "port": int(os.getenv("SUPABASE_DB_PORT", "5432")),
        "database": os.getenv("SUPABASE_DB_NAME", "postgres"),
        "user": os.getenv("SUPABASE_DB_USER"),
        "password": os.getenv("SUPABASE_DB_PASSWORD"),
    }

    required_fields = ["host", "database", "user", "password"]
    missing = [field for field in required_fields if not config[field]]

    if missing:
        raise RuntimeError(
            "Missing required database configuration: " + ", ".join(missing)
        )

    return config
