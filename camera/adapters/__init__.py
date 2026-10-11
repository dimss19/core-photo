"""Camera adapters package."""
from .webcam import WebcamAdapter
from .hot_folder import HotFolderAdapter
from .direct_usb import DirectUsbAdapter
from .wifi_dslr import WiFiDslrAdapter

__all__ = ["WebcamAdapter", "HotFolderAdapter", "DirectUsbAdapter", "WiFiDslrAdapter"]
