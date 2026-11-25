"""
TogoID - Python library for biological database ID conversion and annotation

This package provides:
- TogoIDConverter: Convert IDs between biological databases
- AnnotationsConverter: Get annotations and labels for IDs
- LabelConverter: Convert labels to IDs using external APIs
"""

from .converter import TogoIDConverter
from .annotations import AnnotationsConverter
from .label_converter import LabelConverter

try:
    from importlib.metadata import PackageNotFoundError, version as _pkg_version

    __version__ = _pkg_version("togoid")
except PackageNotFoundError:  # running from a source tree without installation
    __version__ = "unknown"
__all__ = ["TogoIDConverter", "AnnotationsConverter", "LabelConverter"]
