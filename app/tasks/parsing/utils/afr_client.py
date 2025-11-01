"""
Azure Form Recognizer client wrapper.

This module provides a clean interface to Azure Form Recognizer with
retry logic, error handling, and cost tracking.
"""

import asyncio
import logging
from typing import Any, Optional

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

from .. import config

logger = logging.getLogger(__name__)


class AzureFormRecognizerClient:
    """
    Wrapper for Azure Form Recognizer with retry logic and error handling.

    Cost per 1000 pages (as of 2024):
    - Read model: ~$1.50
    - Layout model: ~$10.00
    - Prebuilt models: Varies by type

    We use the 'prebuilt-layout' model for comprehensive extraction.
    """

    def __init__(self):
        """Initialize Azure Form Recognizer client."""
        if not config.AZURE_AFR_ENDPOINT or not config.AZURE_AFR_API_KEY:
            raise ValueError(
                "Azure Form Recognizer credentials not configured. "
                "Please set AZURE_AFR_ENDPOINT and AZURE_AFR_API_KEY"
            )

        self.endpoint = config.AZURE_AFR_ENDPOINT
        self.client = DocumentAnalysisClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(config.AZURE_AFR_API_KEY),
        )

        logger.info(f"Azure Form Recognizer client initialized: {self.endpoint}")

    async def analyze_document(
        self,
        file_content: bytes,
        model_id: str = "prebuilt-layout",
    ) -> Any:
        """
        Analyze document using Azure Form Recognizer.

        Args:
            file_content: Document bytes
            model_id: AFR model to use (default: prebuilt-layout)

        Returns:
            Analyzed document result

        Raises:
            RuntimeError: If analysis fails after retries
        """
        for attempt in range(config.AFR_RETRY_ATTEMPTS):
            try:
                logger.info(
                    f"Starting AFR analysis with model '{model_id}' "
                    f"(attempt {attempt + 1}/{config.AFR_RETRY_ATTEMPTS})"
                )

                # Begin analysis (async operation)
                poller = self.client.begin_analyze_document(
                    model_id=model_id,
                    document=file_content,
                )

                # Wait for completion with timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(poller.result),
                    timeout=config.AFR_POLLING_TIMEOUT,
                )

                logger.info("AFR analysis completed successfully")
                return result

            except asyncio.TimeoutError:
                logger.error(
                    f"AFR analysis timeout after {config.AFR_POLLING_TIMEOUT}s "
                    f"(attempt {attempt + 1})"
                )
                if attempt < config.AFR_RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(config.AFR_RETRY_DELAY * (attempt + 1))
                    continue
                raise RuntimeError("AFR analysis timed out after all retries")

            except HttpResponseError as e:
                logger.error(f"AFR HTTP error: {e.status_code} - {e.message}")
                if e.status_code == 429:  # Rate limit
                    if attempt < config.AFR_RETRY_ATTEMPTS - 1:
                        wait_time = config.AFR_RETRY_DELAY * (2 ** attempt)
                        logger.info(f"Rate limited, waiting {wait_time}s before retry")
                        await asyncio.sleep(wait_time)
                        continue
                raise RuntimeError(f"AFR HTTP error: {e.message}")

            except Exception as e:
                logger.error(f"AFR analysis failed: {str(e)}")
                if attempt < config.AFR_RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(config.AFR_RETRY_DELAY)
                    continue
                raise RuntimeError(f"AFR analysis failed: {str(e)}")

        raise RuntimeError("AFR analysis failed after all retry attempts")

    def extract_sections_from_result(
        self, result: Any, include_tables: bool = True
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Extract sections and page info from AFR result.

        Args:
            result: AFR analysis result
            include_tables: Whether to include table extraction

        Returns:
            tuple: (sections list, page_info dict)
        """
        sections = []
        page_info = {}

        # Extract page dimensions
        for page in result.pages:
            page_info[str(page.page_number)] = {
                "width": page.width,
                "height": page.height,
                "unit": page.unit,
                "angle": page.angle if hasattr(page, "angle") else 0,
            }

        # Extract paragraphs
        if hasattr(result, "paragraphs"):
            for para in result.paragraphs:
                section = self._create_section_from_paragraph(para)
                sections.append(section)

        # Extract tables (if enabled)
        if include_tables and hasattr(result, "tables"):
            for table in result.tables:
                section = self._create_section_from_table(table)
                sections.append(section)

        # Sort by page number and offset
        sections.sort(key=lambda x: (x.get("page_number", 0), x.get("offset", 0)))

        logger.info(
            f"Extracted {len(sections)} sections from {len(page_info)} pages"
        )

        return sections, page_info

    def _create_section_from_paragraph(self, paragraph: Any) -> dict[str, Any]:
        """
        Create section dict from AFR paragraph.

        Args:
            paragraph: AFR paragraph object

        Returns:
            dict: Section with content, viewport, and metadata
        """
        # Extract bounding box if available
        viewport = []
        if hasattr(paragraph, "bounding_regions") and paragraph.bounding_regions:
            region = paragraph.bounding_regions[0]
            if hasattr(region, "polygon"):
                # Convert polygon to flat list [x1, y1, x2, y2, ...]
                viewport = [coord for point in region.polygon for coord in (point.x, point.y)]

        # Determine page number
        page_number = 1
        if hasattr(paragraph, "bounding_regions") and paragraph.bounding_regions:
            page_number = paragraph.bounding_regions[0].page_number

        return {
            "content": paragraph.content,
            "type": "paragraph",
            "viewport": viewport,
            "offset": paragraph.spans[0].offset if paragraph.spans else 0,
            "page_number": page_number,
            "role": getattr(paragraph, "role", None),  # Heading levels (title, sectionHeading, etc.)
        }

    def _create_section_from_table(self, table: Any) -> dict[str, Any]:
        """
        Create section dict from AFR table.

        Args:
            table: AFR table object

        Returns:
            dict: Section with HTML table content and metadata
        """
        # Extract bounding box if available
        viewport = []
        if hasattr(table, "bounding_regions") and table.bounding_regions:
            region = table.bounding_regions[0]
            if hasattr(region, "polygon"):
                viewport = [coord for point in region.polygon for coord in (point.x, point.y)]

        # Determine page number
        page_number = 1
        if hasattr(table, "bounding_regions") and table.bounding_regions:
            page_number = table.bounding_regions[0].page_number

        # Convert table to HTML
        html_content = self._table_to_html(table)

        return {
            "content": html_content,
            "type": "table",
            "viewport": viewport,
            "offset": table.spans[0].offset if table.spans else 0,
            "page_number": page_number,
            "row_count": table.row_count,
            "column_count": table.column_count,
        }

    def _table_to_html(self, table: Any) -> str:
        """
        Convert AFR table to HTML format.

        Args:
            table: AFR table object

        Returns:
            str: HTML table string
        """
        html_rows = [[] for _ in range(table.row_count)]

        for cell in table.cells:
            row_idx = cell.row_index
            tag = "th" if cell.kind == "columnHeader" else "td"

            cell_html = f"<{tag}>{cell.content}</{tag}>"

            # Handle colspan and rowspan
            if cell.column_span and cell.column_span > 1:
                cell_html = f"<{tag} colspan='{cell.column_span}'>{cell.content}</{tag}>"
            if cell.row_span and cell.row_span > 1:
                cell_html = f"<{tag} rowspan='{cell.row_span}'>{cell.content}</{tag}>"

            html_rows[row_idx].append(cell_html)

        # Build HTML
        rows_html = "\n".join(
            f"  <tr>{''.join(cells)}</tr>" for cells in html_rows if cells
        )

        return f"<table>\n{rows_html}\n</table>"
