"""
Parsing module for document processing.

This module provides self-contained parsing functionality for converting
documents (PDF, Excel, PowerPoint) into enriched JSON "digital twins".

The module is designed to be:
- Self-contained: Can be extracted as a separate deployable unit
- Configurable: All AI/ML services controlled via feature flags
- Cost-aware: B2B-friendly with granular cost control
"""

from .pdf_parser import PDFParser
from .excel_parser import ExcelParser
from .ppt_parser import PowerPointParser

__all__ = ["PDFParser", "ExcelParser", "PowerPointParser"]
