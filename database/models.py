"""Data models and enums for Core Photo database layer."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class PhotoStatus(str, Enum):
    """Explicit lifecycle status for a core photo (PRD Section 18)."""
    DRAFT = "DRAFT"
    CAPTURED = "CAPTURED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    VALID = "VALID"
    INVALID = "INVALID"
    READY_TO_TRANSFER = "READY_TO_TRANSFER"
    TRANSFERRING = "TRANSFERRING"
    TRANSFERRED = "TRANSFERRED"
    TRANSFER_FAILED = "TRANSFER_FAILED"
    SUPERSEDED = "SUPERSEDED"


class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class TransferStatus(str, Enum):
    PENDING = "PENDING"
    UPLOADING = "UPLOADING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


@dataclass
class SessionModel:
    id: str  # e.g. UUID or site_date key
    site: str
    date: str
    operator: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = SessionStatus.ACTIVE.value


@dataclass
class TrayModel:
    id: Optional[int] = None
    session_id: str = ""
    hole_id: str = ""
    tray_id: str = ""
    interval_from: float = 0.0
    interval_to: float = 0.0
    tray_rows: int = 1
    tray_length: float = 0.0
    tray_width: float = 0.0
    comments: str = ""
    status: str = "IN_PROGRESS"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PhotoModel:
    id: Optional[int] = None
    session_id: str = ""
    tray_id: Optional[int] = None
    hole_id: str = ""
    tray_number: str = ""
    interval_from: float = 0.0
    interval_to: float = 0.0
    filename_base: str = ""
    raw_path: str = ""
    jpg_path: str = ""
    thumbnail_path: str = ""
    md5_raw: str = ""
    md5_jpg: str = ""
    crop_x: int = 0
    crop_y: int = 0
    crop_w: int = 300
    crop_h: int = 200
    camera_model: str = ""
    camera_serial: str = ""
    status: str = PhotoStatus.DRAFT.value
    is_active: int = 1  # 1 for active candidate, 0 if superseded by retake
    captured_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def timestamp(self) -> str:
        """Convenience property for display."""
        return self.captured_at or self.created_at or ""


@dataclass
class CameraDeviceModel:
    id: Optional[int] = None
    name: str = ""
    adapter_type: str = "webcam"
    vendor_info: str = ""
    serial_number: str = ""
    capabilities_json: str = "{}"
    last_connected_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TransferModel:
    id: Optional[int] = None
    photo_id: int = 0
    server_url: str = ""
    status: str = TransferStatus.PENDING.value
    attempt_count: int = 0
    last_attempt_at: Optional[str] = None
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    transferred_at: Optional[str] = None


@dataclass
class ValidationResultModel:
    id: Optional[int] = None
    target_type: str = "photo"  # photo, tray, session
    target_id: str = ""
    is_valid: int = 1
    rule_name: str = ""
    message: str = ""
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ApplicationEventModel:
    id: Optional[int] = None
    session_id: str = ""
    event_type: str = "INFO"
    description: str = ""
    details_json: str = "{}"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
