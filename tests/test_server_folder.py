"""Unit tests for Target Server Folder integration in CaptureView and SettingsView."""

import os
from pathlib import Path
import pytest
import customtkinter as ctk

from config.config_manager import get_config
from core.app_context import get_app_context
from database.models import PhotoModel, SessionModel
from storage.manager import StorageManager
from ui.capture import CaptureView
from ui.settings import SettingsView


def test_capture_view_server_folder_components(tmp_path):
    root = ctk.CTk()
    root.withdraw()
    try:
        config = get_config()
        config.set("transfer", "server_folder", str(tmp_path / "ServerRepo"))

        view = CaptureView(root, navigate_fn=lambda r: None)
        assert hasattr(view, "entry_server_folder")
        assert hasattr(view, "btn_browse_server_folder")
        assert hasattr(view, "btn_sync_server")

        # Check that starting view populates entry_server_folder from config
        view.start_view()
        assert view.entry_server_folder.get() == str(tmp_path / "ServerRepo")

        # Test changing entry saves to config
        new_server_path = str(tmp_path / "NewServerRepo")
        view.entry_server_folder.delete(0, "end")
        view.entry_server_folder.insert(0, new_server_path)
        view._on_server_folder_changed()
        assert config.get("transfer", "server_folder") == new_server_path

        view.stop_view()
    finally:
        root.destroy()


def test_sync_session_to_server_folder(tmp_path):
    root = ctk.CTk()
    root.withdraw()
    try:
        ctx = get_app_context()
        ctx.storage_manager = StorageManager(base_dir=tmp_path / "LocalData")
        sess = ctx.create_session("GOSOWONG", "Danes", "20261010")

        # Create dummy JPG and CSV in session directory
        sp = ctx.session_paths
        test_jpg = sp.jpg_dir / "TSD168_01.jpg"
        test_jpg.write_text("dummy image content", encoding="utf-8")

        test_csv = sp.session_dir / "TSD168.csv"
        test_csv.write_text("dummy,csv,data", encoding="utf-8")

        server_target = tmp_path / "RemoteServer"
        view = CaptureView(root, navigate_fn=lambda r: None)
        view.entry_server_folder.delete(0, "end")
        view.entry_server_folder.insert(0, str(server_target))

        # Perform sync
        view._on_sync_server_folder()

        dest_sess_dir = server_target / f"{sess.site}_{sess.date}"
        assert dest_sess_dir.exists()
        assert (dest_sess_dir / "jpg" / "TSD168_01.jpg").exists()
        assert (dest_sess_dir / "TSD168.csv").exists()
        assert "Synced" in view.lbl_capture_feedback.cget("text")

        view.stop_view()
    finally:
        root.destroy()


def test_settings_view_server_folder_integration(tmp_path):
    root = ctk.CTk()
    root.withdraw()
    try:
        config = get_config()
        config.set("transfer", "server_folder", str(tmp_path / "ServerFolderFromSettings"))

        view = SettingsView(root, navigate_fn=lambda r: None)
        assert hasattr(view, "entry_settings_server_folder")
        assert hasattr(view, "entry_settings_local_folder")
        assert hasattr(view, "entry_settings_server_url")

        view.refresh()
        assert view.entry_settings_server_folder.get() == str(tmp_path / "ServerFolderFromSettings")

        # Test updating settings
        new_path = str(tmp_path / "UpdatedSettingsServer")
        view.entry_settings_server_folder.delete(0, "end")
        view.entry_settings_server_folder.insert(0, new_path)
        view._on_settings_save_server()

        assert config.get("transfer", "server_folder") == new_path
        assert "saved successfully" in view.lbl_settings_server_status.cget("text")
    finally:
        root.destroy()
