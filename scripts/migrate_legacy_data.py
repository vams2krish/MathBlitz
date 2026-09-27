"""Import legacy JSON and CSV data into the relational MathBlitz database."""

from pathlib import Path

from mathblitz.core.settings import Settings
from mathblitz.db.legacy_import import import_legacy_dataset
from mathblitz.db.session import build_engine, build_session_factory, initialize_database


def main() -> None:
    settings = Settings.from_env()
    engine = build_engine(settings.database_url)
    initialize_database(engine)
    sessions = build_session_factory(engine)
    with sessions() as session:
        summary = import_legacy_dataset(session, Path("data"))
    print(
        "Legacy import complete: "
        f"{summary['users']} users, {summary['attempts']} attempts, "
        f"{summary['skipped_attempt_files']} unmatched progress files skipped."
    )


if __name__ == "__main__":
    main()
