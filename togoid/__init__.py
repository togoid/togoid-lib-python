"""
TogoID - Python library for biological database ID conversion and annotation

This package provides:
- TogoIDConverter: Convert IDs between biological databases
- AnnotationsConverter: Get annotations and labels for IDs
"""

from .converter import TogoIDConverter
from .annotations import AnnotationsConverter

__version__ = "1.0.0"
__all__ = ["TogoIDConverter", "AnnotationsConverter"]
