"""Transfer Uploader with idempotency and retry mechanics (PRD Section 22 & 23).
Never deletes local files upon transfer completion (Rule 20).
"""

import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import httpx

from core.logger import get_logger
from config.config_manager import get_config
from database.models import PhotoModel, PhotoStatus, TransferModel, TransferStatus
from database.repositories import PhotoRepository, TransferRepository

logger = get_logger(__name__)


class TransferUploader:
    """Manages offline queue processing and idempotent uploads."""

    def __init__(
        self,
        photo_repo: Optional[PhotoRepository] = None,
        transfer_repo: Optional[TransferRepository] = None
    ):
        self.photo_repo = photo_repo
        self.transfer_repo = transfer_repo
        self.config = get_config()

    def check_server_connectivity(self, server_url: Optional[str] = None) -> Tuple[bool, str]:
        """Pings server to check network availability before uploading (PRD Section 22)."""
        url = server_url or self.config.get("transfer", "server_url", "http://127.0.0.1:8000/api/v1")
        health_url = f"{url.rstrip('/')}/health"
        timeout = float(self.config.get("transfer", "timeout_seconds", 10))

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(health_url)
                if resp.status_code in (200, 204):
                    return True, "Server terhubung dan siap menerima data."
                return False, f"Server merespon dengan status {resp.status_code}."
        except httpx.ConnectError:
            return False, "Server tidak dapat diakses. Data tetap tersimpan aman di disk lokal."
        except Exception as e:
            return False, f"Gagal menghubungi server: {e}"

    test_connection = check_server_connectivity

    def upload_photo(
        self,
        photo: Any,
        server_url: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Uploads photo, metadata, and checksum with idempotency guarantees (PRD Section 23)."""
        if isinstance(photo, int):
            if not self.photo_repo:
                return False, "PhotoRepository tidak tersedia."
            photo_obj = self.photo_repo.get_by_id(photo)
            if not photo_obj:
                return False, f"Photo ID {photo} tidak ditemukan."
            photo = photo_obj

        url = server_url or self.config.get("transfer", "server_url", "http://127.0.0.1:8000/api/v1")
        upload_endpoint = f"{url.rstrip('/')}/core-photos/upload"
        max_retries = int(self.config.get("transfer", "max_retries", 3))
        timeout = float(self.config.get("transfer", "timeout_seconds", 30))

        jpg_path = Path(photo.jpg_path) if photo.jpg_path else None
        if not jpg_path or not jpg_path.exists():
            return False, f"File JPG tidak ditemukan di path: {photo.jpg_path}"

        meta_path = jpg_path.with_suffix(".json")
        meta_content = meta_path.read_text(encoding="utf-8") if meta_path.exists() else "{}"

        # Initialize transfer record in DB
        transfer = None
        if self.transfer_repo:
            transfer = self.transfer_repo.get_by_photo_id(photo.id)
            if not transfer:
                transfer = self.transfer_repo.create(TransferModel(
                    photo_id=photo.id,
                    server_url=url,
                    status=TransferStatus.UPLOADING.value
                ))
            else:
                self.transfer_repo.update_status(transfer.id, TransferStatus.UPLOADING)

        if self.photo_repo:
            self.photo_repo.update_status(photo.id, PhotoStatus.TRANSFERRING)

        # Idempotency token: derived uniquely from hole_id + tray + md5_raw
        idempotency_key = f"{photo.session_id}_{photo.hole_id}_{photo.tray_number}_{photo.md5_raw}"

        headers = {
            "X-Idempotency-Key": idempotency_key,
            "X-Photo-MD5": photo.md5_jpg,
            "X-Raw-MD5": photo.md5_raw,
        }

        api_key = self.config.get("transfer", "api_key", "")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        attempt = 0
        last_error = ""

        while attempt < max_retries:
            attempt += 1
            try:
                logger.info("Upload attempt %d/%d for photo %s", attempt, max_retries, photo.filename_base)
                with open(jpg_path, "rb") as f_jpg:
                    files = {
                        "photo": (jpg_path.name, f_jpg, "image/jpeg"),
                    }
                    data = {
                        "metadata": meta_content,
                        "hole_id": photo.hole_id,
                        "tray_number": photo.tray_number,
                        "interval_from": str(photo.interval_from),
                        "interval_to": str(photo.interval_to),
                    }

                    with httpx.Client(timeout=timeout) as client:
                        resp = client.post(upload_endpoint, data=data, files=files, headers=headers)

                        if resp.status_code in (200, 201, 409):
                            # 200/201: Success, 409: Already exists on server (idempotent success)
                            if self.transfer_repo and transfer and transfer.id:
                                self.transfer_repo.update_status(
                                    transfer.id,
                                    TransferStatus.SUCCESS,
                                    response_code=resp.status_code,
                                    response_body=resp.text[:500]
                                )
                            if self.photo_repo and photo.id:
                                self.photo_repo.update_status(photo.id, PhotoStatus.TRANSFERRED)

                            logger.info("Photo %s transferred successfully (Status %d)", photo.filename_base, resp.status_code)
                            return True, "Berhasil ditransfer ke server."
                        else:
                            last_error = f"Server merespon error: HTTP {resp.status_code}"
            except Exception as e:
                last_error = f"Jaringan terputus / timeout: {e}"
                logger.warning("Upload attempt %d failed: %s", attempt, e)
                time.sleep(1.0)

        # If all retries failed
        if self.transfer_repo and transfer and transfer.id:
            self.transfer_repo.update_status(
                transfer.id,
                TransferStatus.FAILED,
                error_message=last_error
            )
        if self.photo_repo and photo.id:
            self.photo_repo.update_status(photo.id, PhotoStatus.TRANSFER_FAILED)

        return False, last_error
