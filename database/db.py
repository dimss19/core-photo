"""SQLite Database Manager with migration engine and thread-safe connections.
Strictly follows secure coding: Parameterized queries only, WAL mode for crash resistance.
"""

import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.logger import get_logger

logger = get_logger(__name__)

MIGRATIONS: Dict[int, List[str]] = {
    1: [
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            site TEXT NOT NULL,
            date TEXT NOT NULL,
            operator TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS trays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            hole_id TEXT NOT NULL,
            tray_id TEXT NOT NULL,
            interval_from REAL NOT NULL,
            interval_to REAL NOT NULL,
            tray_rows INTEGER DEFAULT 1,
            tray_length REAL DEFAULT 0.0,
            tray_width REAL DEFAULT 0.0,
            comments TEXT,
            status TEXT NOT NULL DEFAULT 'IN_PROGRESS',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            tray_id INTEGER,
            hole_id TEXT NOT NULL,
            tray_number TEXT NOT NULL,
            interval_from REAL NOT NULL,
            interval_to REAL NOT NULL,
            filename_base TEXT NOT NULL,
            raw_path TEXT,
            jpg_path TEXT,
            thumbnail_path TEXT,
            md5_raw TEXT,
            md5_jpg TEXT,
            crop_x INTEGER DEFAULT 0,
            crop_y INTEGER DEFAULT 0,
            crop_w INTEGER DEFAULT 300,
            crop_h INTEGER DEFAULT 200,
            camera_model TEXT,
            camera_serial TEXT,
            status TEXT NOT NULL DEFAULT 'DRAFT',
            is_active INTEGER NOT NULL DEFAULT 1,
            captured_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (tray_id) REFERENCES trays(id) ON DELETE SET NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS camera_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            adapter_type TEXT NOT NULL,
            vendor_info TEXT,
            serial_number TEXT,
            capabilities_json TEXT DEFAULT '{}',
            last_connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            photo_id INTEGER NOT NULL,
            server_url TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            attempt_count INTEGER DEFAULT 0,
            last_attempt_at TIMESTAMP,
            response_code INTEGER,
            response_body TEXT,
            error_message TEXT,
            transferred_at TIMESTAMP,
            FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS validation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            is_valid INTEGER NOT NULL,
            rule_name TEXT NOT NULL,
            message TEXT NOT NULL,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS application_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            event_type TEXT NOT NULL,
            description TEXT NOT NULL,
            details_json TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        # Indexes for fast search as required by PRD Section 21
        "CREATE INDEX IF NOT EXISTS idx_photos_hole ON photos(hole_id);",
        "CREATE INDEX IF NOT EXISTS idx_photos_tray ON photos(tray_number);",
        "CREATE INDEX IF NOT EXISTS idx_photos_status ON photos(status);",
        "CREATE INDEX IF NOT EXISTS idx_photos_active ON photos(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_trays_session ON trays(session_id);",
        "CREATE INDEX IF NOT EXISTS idx_transfers_status ON transfers(status);"
    ]
}


class DatabaseManager:
    """Manages SQLite connection lifecycle and schema versioning."""

    _thread_local = threading.local()

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a connection for the current thread with foreign keys and WAL mode."""
        conn_attr = f"_conn_{hash(str(self.db_path))}"
        conn = getattr(self._thread_local, conn_attr, None)
        if conn is None:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            setattr(self._thread_local, conn_attr, conn)
        return conn

    def _migrate(self) -> None:
        """Applies database migrations incrementally in transactions."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            # Ensure schema_migrations exists
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()

            cursor = conn.cursor()
            cursor.execute("SELECT version FROM schema_migrations")
            applied_versions = {row[0] for row in cursor.fetchall()}

            for version, statements in sorted(MIGRATIONS.items()):
                if version not in applied_versions:
                    logger.info("Applying migration version %d for %s", version, self.db_path.name)
                    with conn:
                        for stmt in statements:
                            conn.execute(stmt)
                        conn.execute(
                            "INSERT INTO schema_migrations (version) VALUES (?)",
                            (version,)
                        )
                    logger.info("Migration version %d applied successfully.", version)
        except Exception as e:
            logger.error("Migration failed on %s: %s", self.db_path, e)
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: Tuple[Any, ...] = ()) -> List[sqlite3.Row]:
        """Executes a parameterized SELECT query."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def execute_one(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[sqlite3.Row]:
        """Executes a parameterized query returning a single row."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def execute_write(self, query: str, params: Tuple[Any, ...] = ()) -> int:
        """Executes a parameterized INSERT/UPDATE/DELETE query. Returns lastrowid or rowcount."""
        conn = self.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid or cursor.rowcount

    def execute_script(self, script: str) -> None:
        """Executes multiple SQL statements without parameters (for schema init/tests only)."""
        conn = self.get_connection()
        with conn:
            conn.executescript(script)


_active_db_manager: Optional[DatabaseManager] = None


def get_db(db_path: Optional[Path] = None) -> DatabaseManager:
    """Singleton/current session database accessor."""
    global _active_db_manager
    if db_path is not None:
        _active_db_manager = DatabaseManager(db_path)
    elif _active_db_manager is None:
        # Fallback to default session storage
        from storage.manager import StorageManager
        sm = StorageManager()
        default_db = sm.base_dir / "default.db"
        _active_db_manager = DatabaseManager(default_db)
    return _active_db_manager
