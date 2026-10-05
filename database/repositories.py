"""Repository implementations for database entities.
Strictly uses parameterized queries to prevent SQL injection.
Provides clean abstraction so UI/services never touch raw SQL.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.logger import get_logger
from .db import DatabaseManager
from .models import (
    ApplicationEventModel,
    CameraDeviceModel,
    PhotoModel,
    PhotoStatus,
    SessionModel,
    SessionStatus,
    TransferModel,
    TransferStatus,
    TrayModel,
    ValidationResultModel,
)

logger = get_logger(__name__)


class SessionRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create(self, session: SessionModel) -> SessionModel:
        now = datetime.now().isoformat()
        self.db.execute_write(
            """
            INSERT INTO sessions (id, site, date, operator, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session.id, session.site, session.date, session.operator, session.status, now, now)
        )
        session.created_at = now
        session.updated_at = now
        return session

    def get_by_id(self, session_id: str) -> Optional[SessionModel]:
        row = self.db.execute_one(
            "SELECT id, site, date, operator, status, created_at, updated_at FROM sessions WHERE id = ?",
            (session_id,)
        )
        if not row:
            return None
        return SessionModel(
            id=row["id"],
            site=row["site"],
            date=row["date"],
            operator=row["operator"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_active(self) -> Optional[SessionModel]:
        row = self.db.execute_one(
            "SELECT id, site, date, operator, status, created_at, updated_at FROM sessions WHERE status = ? ORDER BY updated_at DESC LIMIT 1",
            (SessionStatus.ACTIVE.value,)
        )
        if not row:
            return None
        return SessionModel(
            id=row["id"],
            site=row["site"],
            date=row["date"],
            operator=row["operator"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def update_status(self, session_id: str, status: SessionStatus) -> bool:
        now = datetime.now().isoformat()
        count = self.db.execute_write(
            "UPDATE sessions SET status = ?, updated_at = ? WHERE id = ?",
            (status.value, now, session_id)
        )
        return count > 0

    def list_all(self) -> List[SessionModel]:
        rows = self.db.execute_query(
            "SELECT id, site, date, operator, status, created_at, updated_at FROM sessions ORDER BY created_at DESC"
        )
        return [
            SessionModel(
                id=r["id"],
                site=r["site"],
                date=r["date"],
                operator=r["operator"],
                status=r["status"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]


class TrayRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create(self, tray: TrayModel) -> TrayModel:
        now = datetime.now().isoformat()
        tray_id = self.db.execute_write(
            """
            INSERT INTO trays (session_id, hole_id, tray_id, interval_from, interval_to,
                               tray_rows, tray_length, tray_width, comments, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tray.session_id,
                tray.hole_id,
                tray.tray_id,
                tray.interval_from,
                tray.interval_to,
                tray.tray_rows,
                tray.tray_length,
                tray.tray_width,
                tray.comments,
                tray.status,
                now,
            )
        )
        tray.id = tray_id
        tray.created_at = now
        return tray

    def get_by_id(self, tray_pk: int) -> Optional[TrayModel]:
        row = self.db.execute_one(
            "SELECT * FROM trays WHERE id = ?",
            (tray_pk,)
        )
        if not row:
            return None
        return self._row_to_model(row)

    def get_by_hole_and_tray(self, session_id: str, hole_id: str, tray_id: str) -> Optional[TrayModel]:
        row = self.db.execute_one(
            "SELECT * FROM trays WHERE session_id = ? AND hole_id = ? AND tray_id = ? ORDER BY id DESC LIMIT 1",
            (session_id, hole_id, tray_id)
        )
        if not row:
            return None
        return self._row_to_model(row)

    def list_by_session(self, session_id: str) -> List[TrayModel]:
        rows = self.db.execute_query(
            "SELECT * FROM trays WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        )
        return [self._row_to_model(r) for r in rows]

    def _row_to_model(self, row: Any) -> TrayModel:
        return TrayModel(
            id=row["id"],
            session_id=row["session_id"],
            hole_id=row["hole_id"],
            tray_id=row["tray_id"],
            interval_from=row["interval_from"],
            interval_to=row["interval_to"],
            tray_rows=row["tray_rows"],
            tray_length=row["tray_length"],
            tray_width=row["tray_width"],
            comments=row["comments"] or "",
            status=row["status"],
            created_at=row["created_at"],
        )


class PhotoRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create(self, photo: PhotoModel) -> PhotoModel:
        now = datetime.now().isoformat()
        photo_id = self.db.execute_write(
            """
            INSERT INTO photos (
                session_id, tray_id, hole_id, tray_number, interval_from, interval_to,
                filename_base, raw_path, jpg_path, thumbnail_path, md5_raw, md5_jpg,
                crop_x, crop_y, crop_w, crop_h, camera_model, camera_serial,
                status, is_active, captured_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                photo.session_id,
                photo.tray_id,
                photo.hole_id,
                photo.tray_number,
                photo.interval_from,
                photo.interval_to,
                photo.filename_base,
                photo.raw_path,
                photo.jpg_path,
                photo.thumbnail_path,
                photo.md5_raw,
                photo.md5_jpg,
                photo.crop_x,
                photo.crop_y,
                photo.crop_w,
                photo.crop_h,
                photo.camera_model,
                photo.camera_serial,
                photo.status,
                photo.is_active,
                photo.captured_at,
                now,
                now,
            )
        )
        photo.id = photo_id
        photo.created_at = now
        photo.updated_at = now
        return photo

    def get_by_id(self, photo_id: int) -> Optional[PhotoModel]:
        row = self.db.execute_one("SELECT * FROM photos WHERE id = ?", (photo_id,))
        if not row:
            return None
        return self._row_to_model(row)

    def update_status(self, photo_id: int, status: PhotoStatus) -> bool:
        now = datetime.now().isoformat()
        count = self.db.execute_write(
            "UPDATE photos SET status = ?, updated_at = ? WHERE id = ?",
            (status.value, now, photo_id)
        )
        return count > 0

    def update_processed_data(
        self,
        photo_id: int,
        jpg_path: str,
        thumbnail_path: str,
        md5_raw: str,
        md5_jpg: str,
        status: PhotoStatus
    ) -> bool:
        now = datetime.now().isoformat()
        count = self.db.execute_write(
            """
            UPDATE photos
            SET jpg_path = ?, thumbnail_path = ?, md5_raw = ?, md5_jpg = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (jpg_path, thumbnail_path, md5_raw, md5_jpg, status.value, now, photo_id)
        )
        return count > 0

    def mark_as_superseded(self, photo_id: int) -> bool:
        """Marks previous capture as superseded (PRD Section 14)."""
        now = datetime.now().isoformat()
        count = self.db.execute_write(
            "UPDATE photos SET is_active = 0, status = ?, updated_at = ? WHERE id = ?",
            (PhotoStatus.SUPERSEDED.value, now, photo_id)
        )
        return count > 0

    def get_active_for_tray(self, session_id: str, hole_id: str, tray_number: str) -> Optional[PhotoModel]:
        row = self.db.execute_one(
            """
            SELECT * FROM photos
            WHERE session_id = ? AND hole_id = ? AND tray_number = ? AND is_active = 1
            ORDER BY id DESC LIMIT 1
            """,
            (session_id, hole_id, tray_number)
        )
        if not row:
            return None
        return self._row_to_model(row)

    def list_by_session(self, session_id: str, active_only: bool = True) -> List[PhotoModel]:
        if active_only:
            rows = self.db.execute_query(
                "SELECT * FROM photos WHERE session_id = ? AND is_active = 1 ORDER BY id DESC",
                (session_id,)
            )
        else:
            rows = self.db.execute_query(
                "SELECT * FROM photos WHERE session_id = ? ORDER BY id DESC",
                (session_id,)
            )
        return [self._row_to_model(r) for r in rows]

    def search(
        self,
        hole_id: Optional[str] = None,
        tray_number: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[PhotoModel]:
        """Search photos with parameterized queries (PRD Section 21)."""
        clauses = ["is_active = 1"]
        params: List[Any] = []

        if hole_id:
            clauses.append("hole_id LIKE ?")
            params.append(f"%{hole_id}%")
        if tray_number:
            clauses.append("tray_number LIKE ?")
            params.append(f"%{tray_number}%")
        if status:
            clauses.append("status = ?")
            params.append(status)

        query = f"SELECT * FROM photos WHERE {' AND '.join(clauses)} ORDER BY id DESC"
        rows = self.db.execute_query(query, tuple(params))
        return [self._row_to_model(r) for r in rows]

    def get_incomplete_photos(self) -> List[PhotoModel]:
        """Finds photos where RAW was saved but processing did not complete (PRD Section 19)."""
        rows = self.db.execute_query(
            """
            SELECT * FROM photos
            WHERE raw_path IS NOT NULL AND raw_path != ''
              AND (jpg_path IS NULL OR jpg_path = '' OR status IN ('CAPTURED', 'PROCESSING'))
              AND is_active = 1
            """
        )
        return [self._row_to_model(r) for r in rows]

    def _row_to_model(self, row: Any) -> PhotoModel:
        return PhotoModel(
            id=row["id"],
            session_id=row["session_id"],
            tray_id=row["tray_id"],
            hole_id=row["hole_id"],
            tray_number=row["tray_number"],
            interval_from=row["interval_from"],
            interval_to=row["interval_to"],
            filename_base=row["filename_base"],
            raw_path=row["raw_path"] or "",
            jpg_path=row["jpg_path"] or "",
            thumbnail_path=row["thumbnail_path"] or "",
            md5_raw=row["md5_raw"] or "",
            md5_jpg=row["md5_jpg"] or "",
            crop_x=row["crop_x"],
            crop_y=row["crop_y"],
            crop_w=row["crop_w"],
            crop_h=row["crop_h"],
            camera_model=row["camera_model"] or "",
            camera_serial=row["camera_serial"] or "",
            status=row["status"],
            is_active=row["is_active"],
            captured_at=row["captured_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class TransferRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create(self, transfer: TransferModel) -> TransferModel:
        transfer_id = self.db.execute_write(
            """
            INSERT INTO transfers (photo_id, server_url, status, attempt_count,
                                   last_attempt_at, response_code, response_body, error_message, transferred_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transfer.photo_id,
                transfer.server_url,
                transfer.status,
                transfer.attempt_count,
                transfer.last_attempt_at,
                transfer.response_code,
                transfer.response_body,
                transfer.error_message,
                transfer.transferred_at,
            )
        )
        transfer.id = transfer_id
        return transfer

    def get_by_photo_id(self, photo_id: int) -> Optional[TransferModel]:
        row = self.db.execute_one(
            "SELECT * FROM transfers WHERE photo_id = ? ORDER BY id DESC LIMIT 1",
            (photo_id,)
        )
        if not row:
            return None
        return self._row_to_model(row)

    def update_status(
        self,
        transfer_id: int,
        status: TransferStatus,
        response_code: Optional[int] = None,
        response_body: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        now = datetime.now().isoformat()
        transferred_at = now if status == TransferStatus.SUCCESS else None
        count = self.db.execute_write(
            """
            UPDATE transfers
            SET status = ?, attempt_count = attempt_count + 1, last_attempt_at = ?,
                response_code = ?, response_body = ?, error_message = ?, transferred_at = coalesce(?, transferred_at)
            WHERE id = ?
            """,
            (status.value, now, response_code, response_body, error_message, transferred_at, transfer_id)
        )
        return count > 0

    def get_pending(self) -> List[TransferModel]:
        rows = self.db.execute_query(
            "SELECT * FROM transfers WHERE status IN (?, ?) ORDER BY id ASC",
            (TransferStatus.PENDING.value, TransferStatus.FAILED.value)
        )
        return [self._row_to_model(r) for r in rows]

    def _row_to_model(self, row: Any) -> TransferModel:
        return TransferModel(
            id=row["id"],
            photo_id=row["photo_id"],
            server_url=row["server_url"],
            status=row["status"],
            attempt_count=row["attempt_count"],
            last_attempt_at=row["last_attempt_at"],
            response_code=row["response_code"],
            response_body=row["response_body"],
            error_message=row["error_message"],
            transferred_at=row["transferred_at"],
        )


class ValidationRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def add_result(self, result: ValidationResultModel) -> ValidationResultModel:
        now = datetime.now().isoformat()
        res_id = self.db.execute_write(
            """
            INSERT INTO validation_results (target_type, target_id, is_valid, rule_name, message, checked_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (result.target_type, result.target_id, result.is_valid, result.rule_name, result.message, now)
        )
        result.id = res_id
        result.checked_at = now
        return result

    def get_for_target(self, target_type: str, target_id: str) -> List[ValidationResultModel]:
        rows = self.db.execute_query(
            "SELECT * FROM validation_results WHERE target_type = ? AND target_id = ? ORDER BY id DESC",
            (target_type, target_id)
        )
        return [
            ValidationResultModel(
                id=r["id"],
                target_type=r["target_type"],
                target_id=r["target_id"],
                is_valid=r["is_valid"],
                rule_name=r["rule_name"],
                message=r["message"],
                checked_at=r["checked_at"],
            )
            for r in rows
        ]

    def clear_for_target(self, target_type: str, target_id: str) -> None:
        self.db.execute_write(
            "DELETE FROM validation_results WHERE target_type = ? AND target_id = ?",
            (target_type, target_id)
        )


class EventRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def log_event(
        self,
        session_id: str,
        event_type: str,
        description: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        now = datetime.now().isoformat()
        details_str = json.dumps(details or {})
        self.db.execute_write(
            """
            INSERT INTO application_events (session_id, event_type, description, details_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, event_type, description, details_str, now)
        )

    def get_events(self, session_id: Optional[str] = None, limit: int = 100) -> List[ApplicationEventModel]:
        if session_id:
            rows = self.db.execute_query(
                "SELECT * FROM application_events WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit)
            )
        else:
            rows = self.db.execute_query(
                "SELECT * FROM application_events ORDER BY id DESC LIMIT ?",
                (limit,)
            )
        return [
            ApplicationEventModel(
                id=r["id"],
                session_id=r["session_id"] or "",
                event_type=r["event_type"],
                description=r["description"],
                details_json=r["details_json"],
                created_at=r["created_at"],
            )
            for r in rows
        ]
