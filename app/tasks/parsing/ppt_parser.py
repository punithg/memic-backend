"""
PowerPoint document parser.

Extracts slides, text, and layout from PowerPoint presentations
using Azure Form Recognizer.
"""

import logging
from typing import Any

from .base_parser import BaseParser
from .utils.afr_client import AzureFormRecognizerClient

logger = logging.getLogger(__name__)


class PowerPointParser(BaseParser):
    """
    Parser for PowerPoint documents (.pptx, .ppt).

    Uses Azure Form Recognizer to extract:
    - Slide content (text and tables)
    - Slide layouts
    - Viewport coordinates for elements
    """

    def __init__(self, file_content: bytes, filename: str, document_id: str):
        """
        Initialize PowerPoint parser.

        Args:
            file_content: PowerPoint file bytes
            filename: Original filename
            document_id: Unique document identifier
        """
        super().__init__(file_content, filename, document_id)
        self.afr_client = AzureFormRecognizerClient()

    async def parse(self) -> dict[str, Any]:
        """
        Parse PowerPoint document into enriched JSON.

        Returns:
            dict: Enriched JSON with sections (slides), enriched_metadata, metadata

        Raises:
            RuntimeError: If parsing fails
        """
        try:
            logger.info(f"Starting PowerPoint parsing for: {self.filename}")

            # Step 1: Analyze document with Azure Form Recognizer
            afr_result = await self.afr_client.analyze_document(
                file_content=self.file_content,
                model_id="prebuilt-layout",
            )

            # Step 2: Extract sections and page info (pages = slides)
            sections, page_info = self.afr_client.extract_sections_from_result(
                result=afr_result,
                include_tables=True,
            )

            logger.info(
                f"Extracted {len(sections)} sections from "
                f"{len(page_info)} slides"
            )

            # Step 3: Optional LLM enrichment
            enriched_metadata = {}
            if sections:
                text_content = self._extract_text_from_sections(sections)
                enriched_metadata = await self._enrich_with_llm(text_content)

            # Step 4: Create enriched JSON structure
            enriched_json = self._create_enriched_json_structure(
                sections=sections,
                page_info=page_info,
                enriched_metadata=enriched_metadata,
                additional_metadata={
                    "total_slides": len(page_info),
                    "total_sections": len(sections),
                    "file_type": "powerpoint",
                },
            )

            logger.info(
                f"PowerPoint parsing completed successfully for: {self.filename}"
            )
            return enriched_json

        except Exception as e:
            logger.error(f"PowerPoint parsing failed for {self.filename}: {str(e)}")
            raise RuntimeError(f"PowerPoint parsing failed: {str(e)}")
