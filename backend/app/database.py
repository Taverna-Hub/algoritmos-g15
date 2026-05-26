from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


OPTIONAL_CAPTURE_COLUMNS = {
    "devices": {
        "channel": "INTEGER",
        "frame_type": "VARCHAR(32)",
        "seen_count": "INTEGER",
    },
    "detections": {
        "channel": "INTEGER",
        "frame_type": "VARCHAR(32)",
        "seen_count": "INTEGER",
    },
}


def ensure_optional_capture_columns():
    """Add optional passive-capture columns to existing development databases."""
    with engine.begin() as connection:
        inspector = inspect(connection)

        for table_name, columns in OPTIONAL_CAPTURE_COLUMNS.items():
            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }

            for column_name, column_type in columns.items():
                if column_name in existing_columns:
                    continue

                connection.execute(
                    text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                )


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
