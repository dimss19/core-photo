"""Image processing pipeline (PRD Section 13, 15 & 16).
Decoupled completely from UI.
"""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

from core.logger import get_logger
from config.config_manager import get_config
from storage.manager import SessionPaths
from database.models import PhotoModel, PhotoStatus, TrayModel, SessionModel
from database.repositories import PhotoRepository
from .crop import CropRegion
from .raw import RawHandler
from .thumbnail import ThumbnailGenerator

logger = get_logger(__name__)


def format_core_filename(hole_id: str, tray_number: str, interval_from: float, interval_to: float) -> str:
    """Formats standardized filename according to PRD Section 15.
    Example: Core01_1_000.00_2.60
    """
    clean_hole = str(hole_id).strip().replace(" ", "_")
    clean_tray = str(tray_number).strip().replace(" ", "_")
    # Interval format matching PRD example Core01_1_000.00_2.60
    from_str = f"{interval_from:06.2f}"
    to_str = f"{interval_to:.2f}"
    return f"{clean_hole}_{clean_tray}_{from_str}_{to_str}"


class ImageProcessor:
    """Coordinates image processing pipeline."""

    def __init__(self, photo_repo: Optional[PhotoRepository] = None):
        self.photo_repo = photo_repo
        self.config = get_config()

    def process_capture(
        self,
        raw_bytes: bytes,
        session_paths: SessionPaths,
        session: SessionModel,
        tray: TrayModel,
        crop_region: Optional[CropRegion] = None,
        camera_meta: Optional[Dict[str, Any]] = None,
    ) -> PhotoModel:
        """Executes full capture processing pipeline (PRD Section 13):
        1. Save RAW immediately
        2. Compute RAW MD5
        3. Record initial record in DB (DRAFT / CAPTURED)
        4. Crop & Generate JPG
        5. Generate Thumbnail
        6. Compute JPG MD5
        7. Save metadata sidecar JSON
        8. Update DB record to PROCESSED
        """
        camera_meta = camera_meta or {}
        now = datetime.now()
        timestamp_str = now.isoformat()

        filename_base = format_core_filename(
            tray.hole_id,
            tray.tray_id,
            tray.interval_from,
            tray.interval_to
        )

        # 1. Save RAW immediately
        raw_ext = camera_meta.get("format", "png")
        raw_file = session_paths.raw_dir / f"{filename_base}.{raw_ext}"
        _, md5_raw = RawHandler.save_raw(raw_bytes, raw_file)

        crop_w = self.config.get("imaging", "crop_width", 300)
        crop_h = self.config.get("imaging", "crop_height", 200)

        # 2. Record initial DB record for crash resilience (PRD Section 19)
        photo = PhotoModel(
            session_id=session.id,
            tray_id=tray.id,
            hole_id=tray.hole_id,
            tray_number=tray.tray_id,
            interval_from=tray.interval_from,
            interval_to=tray.interval_to,
            filename_base=filename_base,
            raw_path=str(raw_file),
            jpg_path="",
            thumbnail_path="",
            md5_raw=md5_raw,
            md5_jpg="",
            crop_x=crop_region.x if crop_region else 0,
            crop_y=crop_region.y if crop_region else 0,
            crop_w=crop_region.width if crop_region else crop_w,
            crop_h=crop_region.height if crop_region else crop_h,
            camera_model=camera_meta.get("camera_model", "Unknown Camera"),
            camera_serial=camera_meta.get("camera_serial", "N/A"),
            status=PhotoStatus.CAPTURED.value,
            is_active=1,
            captured_at=timestamp_str,
        )

        if self.photo_repo:
            photo = self.photo_repo.create(photo)
            self.photo_repo.update_status(photo.id, PhotoStatus.PROCESSING)

        try:
            # 3. Decode RAW into RGB
            rgb_array = RawHandler.decode_raw_to_rgb(raw_file)
            pil_img = Image.fromarray(rgb_array)

            # 4. Apply Tray Crop
            if crop_region is None:
                # Default centered crop with standard 300:200 aspect ratio
                w, h = pil_img.size
                cw = min(w, int(h * 1.5))
                ch = int(cw / 1.5)
                cx = (w - cw) // 2
                cy = (h - ch) // 2
                crop_region = CropRegion(x=cx, y=cy, width=cw, height=ch)

            cropped_img = crop_region.apply_to_pil(pil_img, target_size=(crop_w, crop_h))

            display_timestamp = now.strftime("%m/%d/%Y %I:%M:%S %p")

            # Overlay geological metadata slate footer bar (Reference standard)
            slated_img = self.add_metadata_slate_banner(
                img=cropped_img,
                hole_id=tray.hole_id,
                tray_id=tray.tray_id,
                interval_from=tray.interval_from,
                interval_to=tray.interval_to,
                operator=session.operator,
                timestamp_str=display_timestamp,
            )

            # 5. Save JPG
            jpg_file = session_paths.jpg_dir / f"{filename_base}.jpg"
            jpg_quality = self.config.get("imaging", "jpg_quality", 95)
            slated_img.save(str(jpg_file), "JPEG", quality=jpg_quality, optimize=True)
            md5_jpg = RawHandler.calculate_md5(jpg_file)

            # 6. Generate Thumbnail
            thumb_file = session_paths.thumbnail_dir / f"{filename_base}_thumb.jpg"
            thumb_size = tuple(self.config.get("imaging", "thumbnail_size", [150, 100]))
            ThumbnailGenerator.generate(slated_img, thumb_file, size=thumb_size)

            # 7. Write complete metadata sidecar (PRD Section 16)
            metadata = {
                "hole_id": tray.hole_id,
                "tray_id": tray.tray_id,
                "interval_from": tray.interval_from,
                "interval_to": tray.interval_to,
                "path_raw": str(raw_file),
                "path_jpg": str(jpg_file),
                "path_thumbnail": str(thumb_file),
                "comments": tray.comments,
                "date": session.date,
                "operator": session.operator,
                "site": session.site,
                "md5_raw": md5_raw,
                "md5_jpg": md5_jpg,
                "timestamp": timestamp_str,
                "tray_rows": tray.tray_rows,
                "tray_length": tray.tray_length,
                "tray_width": tray.tray_width,
                "tray_crop": {
                    "x": crop_region.x,
                    "y": crop_region.y,
                    "width": crop_region.width,
                    "height": crop_region.height,
                    "output_width": crop_w,
                    "output_height": crop_h,
                },
                "camera_model": photo.camera_model,
                "camera_serial": photo.camera_serial,
                "processing_version": "1.0",
                "application_version": self.config.get("app", "version", "1.0.0"),
            }

            meta_file = session_paths.jpg_dir / f"{filename_base}.json"
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            # Write / append to Hole CSV file matching geological data schema
            try:
                import csv
                clean_hole = str(tray.hole_id).strip().replace(" ", "_")
                csv_file = session_paths.session_dir / f"{clean_hole}.csv"
                write_hdr = not csv_file.exists()
                pw, ph = pil_img.size
                if crop_region and pw > 0 and ph > 0:
                    nx1 = max(0.0, min(1.0, crop_region.x / pw))
                    ny1 = max(0.0, min(1.0, crop_region.y / ph))
                    nx2 = max(0.0, min(1.0, (crop_region.x + crop_region.width) / pw))
                    ny2 = max(0.0, min(1.0, (crop_region.y + crop_region.height) / ph))
                    crop_str = f"{nx1:.4f} {ny1:.4f} {nx2:.4f} {ny2:.4f}"
                else:
                    crop_str = "0.0025 0.3006 0.9645 0.6335"

                with open(csv_file, "a", newline="", encoding="utf-8") as cf:
                    writer = csv.writer(cf)
                    if write_hdr:
                        writer.writerow([
                            "HoleID", "CoreIntervalFrom", "CoreIntervalTo", "TrayID",
                            "Path", "Comments", "Date", "Name", "Site", "MD5",
                            "Timestamp", "TrayRows", "TrayLength", "TrayWidth", "TrayCrop"
                        ])
                    writer.writerow([
                        tray.hole_id,
                        f"{tray.interval_from:g}",
                        f"{tray.interval_to:g}",
                        tray.tray_id,
                        str(jpg_file),
                        tray.comments or "",
                        session.date,
                        session.operator,
                        session.site,
                        md5_jpg,
                        now.strftime("%Y-%m-%d %H:%M:%S"),
                        tray.tray_rows if hasattr(tray, "tray_rows") else 3,
                        tray.tray_length if hasattr(tray, "tray_length") else 700,
                        tray.tray_width if hasattr(tray, "tray_width") else 300,
                        crop_str
                    ])
            except Exception as e:
                logger.warning("Could not append to hole CSV: %s", e)

            # 8. Update DB Record
            photo.jpg_path = str(jpg_file)
            photo.thumbnail_path = str(thumb_file)
            photo.md5_jpg = md5_jpg
            photo.status = PhotoStatus.PROCESSED.value

            if self.photo_repo and photo.id:
                self.photo_repo.update_processed_data(
                    photo.id,
                    str(jpg_file),
                    str(thumb_file),
                    md5_raw,
                    md5_jpg,
                    PhotoStatus.PROCESSED
                )

            logger.info("Successfully processed core photo: %s", filename_base)
            return photo

        except Exception as e:
            logger.error("Processing failed for %s: %s", filename_base, e)
            if self.photo_repo and photo.id:
                self.photo_repo.update_status(photo.id, PhotoStatus.INVALID)
            raise

    @staticmethod
    def add_metadata_slate_banner(
        img: Image.Image,
        hole_id: str,
        tray_id: str,
        interval_from: float,
        interval_to: float,
        operator: str,
        timestamp_str: str,
    ) -> Image.Image:
        """Overlays the industrial core photography metadata slate footer banner."""
        from PIL import ImageDraw, ImageFont
        w, h = img.size
        banner_h = max(18, int(h * 0.08))
        banner_img = img.copy()
        draw = ImageDraw.Draw(banner_img)

        # White banner background with subtle top separator line
        draw.rectangle([0, h - banner_h, w, h], fill=(255, 255, 255))
        draw.line([0, h - banner_h, w, h - banner_h], fill=(210, 215, 220), width=1)

        font_size = max(8, int(banner_h * 0.45))
        font = None
        for font_name in ["segoeui.ttf", "arial.ttf", "calibri.ttf"]:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except Exception:
                pass

        left_text = f"HOLE ID: {hole_id}  TRAY ID: {tray_id}  FROM: {interval_from:g}  TO: {interval_to:g}"
        op_text = f"OPERATOR: {operator}  " if operator and operator.strip() else ""
        right_text = f"{op_text}TIMESTAMP: {timestamp_str}"

        y_pos = h - banner_h + (banner_h - font_size) // 2
        draw.text((8, y_pos), left_text, fill=(15, 20, 25), font=font)

        try:
            rw = font.getbbox(right_text)[2] if font else len(right_text) * 6
        except Exception:
            rw = len(right_text) * 6

        x_right = max(w - rw - 8, 8)
        draw.text((x_right, y_pos), right_text, fill=(15, 20, 25), font=font)

        return banner_img

    @staticmethod
    def export_csv_report(session: Any, photos: List[Any], csv_path: Path) -> Path:
        """Exports or regenerates the standardized geological CSV report (PRD Section 16 & Industry standard).
        Columns match the legacy Coreshed Excel report:
        HoleID, CoreIntervalFrom, CoreIntervalTo, TrayID, Path, Comments, Date, Name, Site, MD5,
        Timestamp, TrayRows, TrayLength, TrayWidth, TrayCrop
        """
        import csv
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "HoleID", "CoreIntervalFrom", "CoreIntervalTo", "TrayID",
                "Path", "Comments", "Date", "Name", "Site", "MD5",
                "Timestamp", "TrayRows", "TrayLength", "TrayWidth", "TrayCrop"
            ])
            for p in photos:
                comments = ""
                crop_str = "0.0025 0.3006 0.9645 0.6335"
                tray_rows = 3
                tray_len = 700
                tray_wid = 300
                ts = getattr(p, "captured_at", "") or getattr(session, "date", "")

                if getattr(p, "jpg_path", None):
                    meta_path = Path(p.jpg_path).with_suffix(".json")
                    if meta_path.exists():
                        try:
                            meta = json.loads(meta_path.read_text(encoding="utf-8"))
                            comments = meta.get("comments", "")
                            tray_rows = meta.get("tray_rows", 3)
                            tray_len = meta.get("tray_length", 700)
                            tray_wid = meta.get("tray_width", 300)
                            ts = meta.get("timestamp", ts)
                            tc = meta.get("tray_crop", {})
                            if isinstance(tc, dict) and "output_width" in tc:
                                ow = tc.get("output_width", 1) or 1
                                oh = tc.get("output_height", 1) or 1
                                nx1 = max(0.0, min(1.0, tc.get("x", 0) / ow))
                                ny1 = max(0.0, min(1.0, tc.get("y", 0) / oh))
                                nx2 = max(0.0, min(1.0, (tc.get("x", 0) + tc.get("width", ow)) / ow))
                                ny2 = max(0.0, min(1.0, (tc.get("y", 0) + tc.get("height", oh)) / oh))
                                crop_str = f"{nx1:.4f} {ny1:.4f} {nx2:.4f} {ny2:.4f}"
                        except Exception:
                            pass

                writer.writerow([
                    getattr(p, "hole_id", "TSD168"),
                    f"{getattr(p, 'interval_from', 0.0):g}",
                    f"{getattr(p, 'interval_to', 0.0):g}",
                    getattr(p, "tray_number", "1"),
                    getattr(p, "jpg_path", "") or "",
                    comments,
                    getattr(session, "date", ""),
                    getattr(session, "operator", ""),
                    getattr(session, "site", ""),
                    getattr(p, "md5_jpg", "") or "",
                    ts,
                    tray_rows,
                    tray_len,
                    tray_wid,
                    crop_str
                ])
        return csv_path

