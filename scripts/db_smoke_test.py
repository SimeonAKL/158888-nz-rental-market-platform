"""Minimal Supabase/PostgreSQL connectivity smoke test."""

from sqlalchemy import URL, create_engine, text

from rmp.config import get_database_config


def main() -> None:
    """Connect to PostgreSQL and verify basic database access."""
    config = get_database_config()

    database_url = URL.create(
        drivername="postgresql+psycopg2",
        username=config["user"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
        database=config["database"],
    )

    engine = create_engine(database_url)

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    engine.dispose()
    print(f"Database connection OK: {value}")


if __name__ == "__main__":
    main()
