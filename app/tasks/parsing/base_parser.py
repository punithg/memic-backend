"""
Base parser class with shared utilities.

All parsers inherit from this base class to ensure consistent behavior
and output format across different document types.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from . import config

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Abstract base class for all document parsers."""

    def __init__(self, file_content: bytes, filename: str, document_id: str):
        """
        Initialize the parser.

        Args:
            file_content: Raw bytes of the document
            filename: Original filename
            document_id: Unique document identifier (UUID)
        """
        self.file_content = file_content
        self.filename = filename
        self.document_id = document_id
        self.parser_name = self.__class__.__name__

        # Log enabled features
        enabled_features = config.get_enabled_features()
        if enabled_features:
            logger.info(f"Parser initialized with features: {', '.join(enabled_features)}")
        else:
            logger.info("Parser initialized with no optional features")

    @abstractmethod
    async def parse(self) -> dict[str, Any]:
        """
        Parse the document and return enriched JSON.

        Returns:
            dict: Enriched JSON containing sections, enriched_metadata, and metadata

        Raises:
            ValueError: If document format is invalid
            RuntimeError: If parsing service fails
        """
        pass

    def _create_base_metadata(self) -> dict[str, Any]:
        """
        Create base metadata common to all parsers.

        Returns:
            dict: Base metadata structure
        """
        return {
            "document_id": self.document_id,
            "file_name": self.filename,
            "parser": self.parser_name,
            "parsing_service": config.PARSING_SERVICE,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_size": len(self.file_content),
        }

    def _create_enriched_json_structure(
        self,
        sections: list[dict[str, Any]],
        page_info: Optional[dict[str, Any]] = None,
        enriched_metadata: Optional[dict[str, Any]] = None,
        additional_metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create standardized enriched JSON structure.

        This ensures all parsers return data in the same format.

        Args:
            sections: List of document sections with content and viewport
            page_info: Page dimensions and metadata
            enriched_metadata: LLM-extracted semantic metadata (document type, summary, tags)
            additional_metadata: Parser-specific metadata

        Returns:
            dict: Standardized enriched JSON structure
        """
        base_metadata = self._create_base_metadata()

        if additional_metadata:
            base_metadata.update(additional_metadata)

        return {
            "sections": sections,
            "page_info": page_info or {},
            "enriched_metadata": enriched_metadata or {},
            "metadata": base_metadata,
        }

    async def _enrich_with_llm(self, text_content: str) -> dict[str, Any]:
        """
        Optionally enrich document with LLM-generated metadata.

        Only runs if ENABLE_LLM_ENRICHMENT is True.

        Args:
            text_content: Full text content of the document

        Returns:
            dict: Enriched metadata dict (empty if LLM enrichment disabled)
        """
        if not config.ENABLE_LLM_ENRICHMENT:
            logger.debug("LLM enrichment disabled, skipping metadata extraction")
            return {}

        try:
            from .utils.llm_enrichment import LLMEnrichment

            enrichment = LLMEnrichment()
            enriched_metadata = await enrichment.extract_metadata(text_content, self.filename)
            logger.info(f"LLM enrichment successful for {self.filename}")
            return enriched_metadata

        except Exception as e:
            logger.warning(f"LLM enrichment failed: {str(e)}, continuing without enrichment")
            return {}

    def _convert_bounding_box_to_viewport(
        self, bounding_box: list[float]
    ) -> list[float]:
        """
        Convert bounding box coordinates to viewport format.

        Azure Form Recognizer returns 8-point polygon: [x1, y1, x2, y2, x3, y3, x4, y4]
        We keep the same format but rename to 'viewport' for better semantics.

        Args:
            bounding_box: 8-point polygon coordinates

        Returns:
            list: Viewport coordinates (same format, better naming)
        """
        if not bounding_box or len(bounding_box) != 8:
            logger.warning(f"Invalid bounding box format: {bounding_box}")
            return []

        return bounding_box

    def _extract_text_from_sections(self, sections: list[dict[str, Any]]) -> str:
        """
        Extract plain text from all sections for LLM enrichment.

        Args:
            sections: List of section dicts with 'content' field

        Returns:
            str: Combined text content
        """
        text_parts = []

        for section in sections:
            content = section.get("content", "")
            section_type = section.get("type", "")

            # Skip tables for LLM enrichment (too verbose)
            if section_type == "table":
                continue

            if content:
                text_parts.append(content)

        return "\n\n".join(text_parts)
