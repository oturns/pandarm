import contextlib
from importlib.metadata import PackageNotFoundError, version

from .network import Network

try:
    __version__ = version("pandarm")
except PackageNotFoundError:
    try:
        from ._version import __version__  # type: ignore[no-redef]
    except ImportError:
        __version__ = "0.0.0+unknown"

__all__ = [
    "Network",
]
