"""
LLM enrichment for document metadata extraction.

This module uses OpenAI to extract structured metadata from documents:
- document_type: Category of document
- summary: Brief document summary
- tags: Relevant tags
- date_of_authoring: Extracted date if available

Cost: ~$0.002 per document with gpt-4o-mini (as of 2024)
"""

import logging
from typing import Any, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from .. import config

logger = logging.getLogger(__name__)


class EnrichedMetadata(BaseModel):
    """Structured enriched metadata extracted by LLM."""

    document_type: str = Field(
        description="Category of document (e.g., invoice, contract, report, email)"
    )
    summary: str = Field(
        description="Brief 1-2 sentence summary of document content"
    )
    tags: list[str] = Field(
        description="Relevant tags for categorization (3-5 tags)"
    )
    date_of_authoring: Optional[str] = Field(
        default=None,
        description="Date document was authored (YYYY-MM-DD format) if extractable",
    )
    source: Optional[str] = Field(
        default=None,
        description="Source/origin of document if identifiable"
    )
    reliability: str = Field(
        default="medium",
        description="Confidence level of extraction (high/medium/low)"
    )


class LLMEnrichment:
    """
    LLM-based document enrichment.

    Only instantiate if ENABLE_LLM_ENRICHMENT is True.
    """

    def __init__(self):
        """Initialize OpenAI client."""
        if not config.OPENAI_API_KEY:
            raise ValueError(
                "OpenAI API key not configured. "
                "Please set OPENAI_API_KEY or disable ENABLE_LLM_ENRICHMENT"
            )

        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL

        logger.info(f"LLM enrichment initialized with model: {self.model}")

    async def extract_metadata(
        self, text_content: str, filename: str, max_chars: int = 8000
    ) -> dict[str, Any]:
        """
        Extract enriched metadata using LLM.

        Args:
            text_content: Full text content of document
            filename: Original filename (provides context)
            max_chars: Maximum characters to send to LLM (cost control)

        Returns:
            dict: Extracted enriched metadata

        Raises:
            RuntimeError: If LLM extraction fails
        """
        try:
            # Truncate content for cost control
            truncated_content = text_content[:max_chars]
            if len(text_content) > max_chars:
                logger.info(
                    f"Truncated content from {len(text_content)} to {max_chars} chars"
                )

            # Create prompt
            prompt = self._create_extraction_prompt(filename, truncated_content)

            # Call OpenAI with structured output
            logger.info(f"Requesting LLM metadata extraction with {self.model}")

            response = await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a document analysis expert. Extract structured "
                            "metadata from documents accurately and concisely."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format=EnrichedMetadata,
                temperature=0.3,  # Lower temperature for more consistent extraction
            )

            # Parse response
            enriched_metadata = response.choices[0].message.parsed
            enriched_metadata_dict = enriched_metadata.model_dump()

            logger.info(
                f"LLM extraction successful: {enriched_metadata_dict.get('document_type')} document"
            )

            return enriched_metadata_dict

        except Exception as e:
            logger.error(f"LLM metadata extraction failed: {str(e)}")
            raise RuntimeError(f"LLM enrichment failed: {str(e)}")

    def _create_extraction_prompt(self, filename: str, content: str) -> str:
        """
        Create prompt for LLM metadata extraction.

        Args:
            filename: Original filename
            content: Document content

        Returns:
            str: Formatted prompt
        """
        return f"""Extract metadata from this document.

Filename: {filename}

Document Content:
{content}

Please analyze the document and extract:
1. Document type (be specific, e.g., "technical specification" not just "document")
2. Brief summary of the main content and purpose
3. 3-5 relevant tags for categorization
4. Date of authoring if mentioned in the content
5. Source/origin if identifiable
6. Your confidence level in the extraction (high/medium/low)

Focus on accuracy and brevity."""
