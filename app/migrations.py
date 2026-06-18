from sqlalchemy import inspect, text

from . import db


MIGRATION_V2_FIRST_SLICE = "20260520_v2_first_slice"
MIGRATION_ASSETS_ENDPOINTS = "20260522_assets_endpoints"
MIGRATION_PROGRAMS_LOGO = "20260529_programs_logo"
MIGRATION_PROGRAM_SUMMARY = "20260611_program_summary"
MIGRATION_FIELD_COLUMN = "20260611_field_column"
MIGRATION_TECH_STACK = "20260612_tech_stack"
MIGRATION_FEATURES_V3 = "20260618_features_v3"


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
        (MIGRATION_PROGRAMS_LOGO, _migration_programs_logo),
        (MIGRATION_PROGRAM_SUMMARY, _migration_program_summary),
        (MIGRATION_FIELD_COLUMN, _migration_field_column),
        (MIGRATION_TECH_STACK, _migration_tech_stack),
        (MIGRATION_FEATURES_V3, _migration_features_v3),
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


def _migration_programs_logo(conn):
    inspector = inspect(conn)
    if "programs" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("programs")}
    _add_column_if_missing(
        conn,
        columns,
        "logo_url",
        "ALTER TABLE programs ADD COLUMN logo_url VARCHAR(500)",
    )


def _migration_program_summary(conn):
    inspector = inspect(conn)
    if "programs" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("programs")}
    _add_column_if_missing(
        conn,
        columns,
        "summary",
        "ALTER TABLE programs ADD COLUMN summary TEXT NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(
        conn,
        columns,
        "auto_brief",
        "ALTER TABLE programs ADD COLUMN auto_brief TEXT NOT NULL DEFAULT ''",
    )


def _migration_field_column(conn):
    inspector = inspect(conn)

    for table in ("programs", "findings"):
        if table not in inspector.get_table_names():
            continue
        columns = {col["name"] for col in inspector.get_columns(table)}
        _add_column_if_missing(
            conn,
            columns,
            "field",
            f"ALTER TABLE {table} ADD COLUMN field VARCHAR(20) NOT NULL DEFAULT 'web'",
        )


def _migration_tech_stack(conn):
    inspector = inspect(conn)
    if "programs" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("programs")}
    _add_column_if_missing(
        conn,
        columns,
        "tech_stack",
        "ALTER TABLE programs ADD COLUMN tech_stack TEXT NOT NULL DEFAULT '[]'",
    )


def _migration_features_v3(conn):
    inspector = inspect(conn)
    table_names = inspector.get_table_names()

    # 1. related_finding_ids on findings
    if "findings" in table_names:
        columns = {col["name"] for col in inspector.get_columns("findings")}
        _add_column_if_missing(
            conn,
            columns,
            "related_finding_ids",
            "ALTER TABLE findings ADD COLUMN related_finding_ids TEXT NOT NULL DEFAULT '[]'",
        )

    # 2. credentials table
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id INTEGER NOT NULL REFERENCES programs(id),
                label VARCHAR(100) NOT NULL,
                credential_type VARCHAR(50) NOT NULL DEFAULT 'password',
                username_encrypted TEXT,
                secret_encrypted TEXT NOT NULL,
                url VARCHAR(500),
                notes TEXT NOT NULL DEFAULT '',
                active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    # 3. report_drafts table
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS report_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                finding_id INTEGER NOT NULL REFERENCES findings(id),
                version INTEGER NOT NULL DEFAULT 1,
                title TEXT,
                description TEXT NOT NULL DEFAULT '',
                poc TEXT NOT NULL DEFAULT '',
                summary TEXT NOT NULL DEFAULT '',
                impact TEXT NOT NULL DEFAULT '',
                cwe VARCHAR(50),
                cvss FLOAT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    # 4. alert_rules table
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS alert_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id INTEGER REFERENCES programs(id),
                name VARCHAR(200) NOT NULL,
                trigger_event VARCHAR(100) NOT NULL,
                filter_expression TEXT NOT NULL DEFAULT '',
                webhook_url TEXT NOT NULL DEFAULT '',
                discord_channel VARCHAR(200),
                telegram_chat_id VARCHAR(100),
                slack_webhook_url TEXT,
                active BOOLEAN NOT NULL DEFAULT 1,
                last_fired_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    # 5. Scope versioning: add version + deprecated_at to assets
    if "assets" in table_names:
        columns = {col["name"] for col in inspector.get_columns("assets")}
        _add_column_if_missing(
            conn,
            columns,
            "version",
            "ALTER TABLE assets ADD COLUMN version INTEGER NOT NULL DEFAULT 1",
        )
        _add_column_if_missing(
            conn,
            columns,
            "deprecated_at",
            "ALTER TABLE assets ADD COLUMN deprecated_at DATETIME",
        )
