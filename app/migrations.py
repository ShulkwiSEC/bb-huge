from sqlalchemy import inspect, text

from . import db


MIGRATION_V2_FIRST_SLICE = "20260520_v2_first_slice"
MIGRATION_ASSETS_ENDPOINTS = "20260522_assets_endpoints"


def run_migrations():
    with db.engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(100) PRIMARY KEY,
                    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

        applied = {
            row[0]
            for row in conn.execute(text("SELECT version FROM schema_migrations")).fetchall()
        }

        for version, handler in _migrations():
            if version in applied:
                continue
            handler(conn)
            conn.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                {"version": version},
            )


def _migrations():
    return [
        (MIGRATION_V2_FIRST_SLICE, _migration_v2_first_slice),
        (MIGRATION_ASSETS_ENDPOINTS, _migration_assets_endpoints),
    ]


def _migration_v2_first_slice(conn):
    inspector = inspect(conn)
    if "findings" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("findings")}
    _add_column_if_missing(
        conn,
        columns,
        "hypothesis_id",
        "ALTER TABLE findings ADD COLUMN hypothesis_id INTEGER",
    )
    _add_column_if_missing(
        conn,
        columns,
        "confidence",
        "ALTER TABLE findings ADD COLUMN confidence VARCHAR(20) DEFAULT 'high'",
    )


def _migration_assets_endpoints(conn):
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id INTEGER NOT NULL REFERENCES programs(id),
                kind VARCHAR(50) NOT NULL DEFAULT 'other',
                identifier VARCHAR(500) NOT NULL,
                environment VARCHAR(20) NOT NULL DEFAULT 'unknown',
                notes TEXT NOT NULL DEFAULT '',
                active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS endpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL REFERENCES assets(id),
                method VARCHAR(20) NOT NULL DEFAULT 'GET',
                path VARCHAR(1000) NOT NULL,
                protocol VARCHAR(20) NOT NULL DEFAULT 'https',
                content_type VARCHAR(100),
                auth_required BOOLEAN,
                discovered_by VARCHAR(100),
                notes TEXT NOT NULL DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )


def _add_column_if_missing(conn, columns, name, sql):
    if name in columns:
        return
    conn.execute(text(sql))
    columns.add(name)
