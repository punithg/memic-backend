"""
Excel document parser.

Extracts sheets, tables, and cell data from Excel documents
using Azure Form Recognizer.
"""

import logging
from typing import Any

from .base_parser import BaseParser
from .utils.afr_client import AzureFormRecognizerClient

logger = logging.getLogger(__name__)


class ExcelParser(BaseParser):
    """
    Parser for Excel documents (.xlsx, .xls).

    Uses Azure Form Recognizer to extract:
    - Sheet names and data
    - Tables with cell values
    - Formulas and formatting metadata
    """

    def __init__(self, file_content: bytes, filename: str, document_id: str):
        """
        Initialize Excel parser.

        Args:
            file_content: Excel file bytes
            filename: Original filename
            document_id: Unique document identifier
        """
        super().__init__(file_content, filename, document_id)
        self.afr_client = AzureFormRecognizerClient()

    async def parse(self) -> dict[str, Any]:
        """
        Parse Excel document into enriched JSON.

        Returns:
            dict: Enriched JSON with sections, enriched_metadata, metadata

        Raises:
            RuntimeError: If parsing fails
        """
        try:
            logger.info(f"Starting Excel parsing for: {self.filename}")

            # Step 1: Analyze document with Azure Form Recognizer
            afr_result = await self.afr_client.analyze_document(
                file_content=self.file_content,
                model_id="prebuilt-layout",
            )

            # Step 2: Extract tables (Excel sheets become tables)
            sections, page_info = self.afr_client.extract_sections_from_result(
                result=afr_result,
                include_tables=True,
            )

            # Excel documents are often single-page in AFR's view
            logger.info(
                f"Extracted {len([s for s in sections if s['type'] == 'table'])} "
                f"tables from Excel"
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
                    "total_tables": len(
                        [s for s in sections if s["type"] == "table"]
                    ),
                    "file_type": "excel",
                },
            )

            logger.info(f"Excel parsing completed successfully for: {self.filename}")
            return enriched_json

        except Exception as e:
            logger.error(f"Excel parsing failed for {self.filename}: {str(e)}")
            raise RuntimeError(f"Excel parsing failed: {str(e)}")
