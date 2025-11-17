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

__version__ = "1.0.0"
__all__ = ["TogoIDConverter", "AnnotationsConverter", "LabelConverter"]
