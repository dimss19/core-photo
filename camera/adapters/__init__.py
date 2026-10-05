"""Camera adapters package."""
from .webcam import WebcamAdapter
from .hot_folder import HotFolderAdapter
from .direct_usb import DirectUsbAdapter

__all__ = ["WebcamAdapter", "HotFolderAdapter", "DirectUsbAdapter"]
