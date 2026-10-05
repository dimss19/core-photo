"""Camera adapters package."""
from .webcam import WebcamAdapter
from .hot_folder import HotFolderAdapter

__all__ = ["WebcamAdapter", "HotFolderAdapter"]
