"""Transfer verification and server health check utilities (PRD Section 22)."""

from typing import Optional, Tuple
import httpx
from core.logger import get_logger

logger = get_logger(__name__)


class TransferVerifier:
    """Verifies transfer status against server receipts."""

    @staticmethod
    def verify_server_checksum(server_url: str, photo_filename: str, expected_md5: str) -> Tuple[bool, str]:
        """Queries server verification endpoint to verify stored file integrity."""
        verify_url = f"{server_url.rstrip('/')}/core-photos/verify/{photo_filename}"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(verify_url)
                if resp.status_code == 200:
                    data = resp.json()
                    server_md5 = data.get("md5", "")
                    if server_md5.lower() == expected_md5.lower():
                        return True, "Checksum server cocok 100%."
                    return False, f"Checksum tidak cocok (Lokal: {expected_md5}, Server: {server_md5})"
                return False, f"Server mengembalikan status {resp.status_code}"
        except Exception as e:
            logger.error("Verification query error: %s", e)
            return False, f"Gagal verifikasi dengan server: {e}"
