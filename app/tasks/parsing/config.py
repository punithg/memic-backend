"""
Configuration for parsing module.

This module manages all configuration for document parsing with feature flags
for cost control in a B2B environment.
"""

import os
from typing import Literal

# Parsing Service Selection
# Cost: Azure Form Recognizer ~$1.50 per 1000 pages
# Future: Support for LlamaParse, AWS Textract, etc.
PARSING_SERVICE: Literal["azure_form_recognizer"] = os.getenv(
    "PARSING_SERVICE", "azure_form_recognizer"
)

# Feature Flags for Cost Control
# Each flag controls a feature that incurs additional costs

# LLM Enrichment: Uses OpenAI to extract metadata (document type, summary, tags)
# Cost: ~$0.002 per document with gpt-4o-mini
# When disabled: Returns empty headers dict
ENABLE_LLM_ENRICHMENT: bool = os.getenv("ENABLE_LLM_ENRICHMENT", "false").lower() == "true"

# Advanced Table Extraction: Uses premium AFR features for complex tables
# Cost: May incur additional AFR costs
# When disabled: Uses standard table extraction
ENABLE_ADVANCED_TABLE_EXTRACTION: bool = (
    os.getenv("ENABLE_ADVANCED_TABLE_EXTRACTION", "false").lower() == "true"
)

# Section Hierarchy Extraction: Extracts document structure (headings, levels)
# Cost: Additional processing time and AFR API calls
# When disabled: Returns flat section list
ENABLE_SECTION_HIERARCHY: bool = (
    os.getenv("ENABLE_SECTION_HIERARCHY", "false").lower() == "true"
)

# Azure Form Recognizer Configuration
AZURE_AFR_ENDPOINT: str = os.getenv("AZURE_AFR_ENDPOINT", "")
AZURE_AFR_API_KEY: str = os.getenv("AZURE_AFR_API_KEY", "")

# LLM Configuration (for enrichment)
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Cost-effective choice

# Parsing Timeouts (in seconds)
AFR_POLLING_TIMEOUT: int = int(os.getenv("AFR_POLLING_TIMEOUT", "120"))
AFR_RETRY_ATTEMPTS: int = int(os.getenv("AFR_RETRY_ATTEMPTS", "3"))
AFR_RETRY_DELAY: int = int(os.getenv("AFR_RETRY_DELAY", "2"))


def validate_config() -> dict[str, bool]:
    """
    Validate configuration and return status of required services.

    Returns:
        dict: Status of each service configuration
    """
    validation_status = {
        "azure_form_recognizer": bool(AZURE_AFR_ENDPOINT and AZURE_AFR_API_KEY),
        "llm_enrichment": bool(OPENAI_API_KEY) if ENABLE_LLM_ENRICHMENT else True,
    }

    return validation_status


def get_enabled_features() -> list[str]:
    """
    Get list of enabled features for logging/monitoring.

    Returns:
        list: Names of enabled features
    """
    features = []

    if ENABLE_LLM_ENRICHMENT:
        features.append("llm_enrichment")
    if ENABLE_ADVANCED_TABLE_EXTRACTION:
        features.append("advanced_table_extraction")
    if ENABLE_SECTION_HIERARCHY:
        features.append("section_hierarchy")

    return features
