# Document Parsing Module

## Overview

The parsing module converts documents (PDF, Excel, PowerPoint) into enriched JSON "digital twins" with structured sections, viewport coordinates, and optional LLM-enriched metadata.

This module is designed to be:
- **Self-contained**: Can be extracted as a separate deployable microservice
- **Configurable**: All AI/ML services controlled via feature flags
- **Cost-aware**: B2B-friendly with granular cost control

## Architecture

```
app/tasks/parsing/
├── __init__.py                 # Module exports
├── config.py                   # Configuration with feature flags
├── base_parser.py              # Abstract base class
├── pdf_parser.py               # PDF parsing implementation
├── excel_parser.py             # Excel parsing implementation
├── ppt_parser.py               # PowerPoint parsing implementation
└── utils/
    ├── afr_client.py           # Azure Form Recognizer wrapper
    ├── llm_enrichment.py       # Optional LLM metadata extraction
    └── storage_helper.py       # Azure Blob Storage helpers
```

## Supported File Types

- **PDF** (.pdf)
- **Excel** (.xlsx, .xls)
- **PowerPoint** (.pptx, .ppt)

## Enriched JSON Output Format

```json
{
  "sections": [
    {
      "content": "text content or <table>HTML</table>",
      "type": "paragraph" | "table",
      "viewport": [x1, y1, x2, y2, x3, y3, x4, y4],
      "offset": 0,
      "page_number": 1,
      "role": "title" | "sectionHeading" | null
    }
  ],
  "page_info": {
    "1": {
      "width": 8.5,
      "height": 11,
      "unit": "inch"
    }
  },
  "headers": {
    "document_type": "technical_specification",
    "summary": "Brief document summary",
    "tags": ["tag1", "tag2", "tag3"],
    "date_of_authoring": "2024-10-31",
    "source": "internal",
    "reliability": "high"
  },
  "metadata": {
    "document_id": "uuid",
    "file_name": "example.pdf",
    "parser": "PDFParser",
    "parsing_service": "azure_form_recognizer",
    "created_at": "2024-10-31T12:00:00Z",
    "file_size": 123456,
    "total_pages": 10,
    "total_sections": 45
  }
}
```

### Key Terminology

- **sections**: Array of document content blocks (paragraphs and tables)
- **viewport**: 8-point polygon coordinates `[x1, y1, x2, y2, x3, y3, x4, y4]` defining element position
- **headers**: LLM-enriched metadata (optional, controlled by `ENABLE_LLM_ENRICHMENT`)
- **page_info**: Page dimensions for accurate coordinate mapping

## Configuration

All configuration is managed through environment variables in `.env` files.

### Required Configuration

```bash
# Azure Form Recognizer
AZURE_AFR_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_AFR_API_KEY=your_api_key_here
```

### Optional Features (Cost Control)

```bash
# Parsing Service Selection (default: azure_form_recognizer)
PARSING_SERVICE=azure_form_recognizer

# LLM Enrichment (~$0.002 per document)
ENABLE_LLM_ENRICHMENT=false

# Advanced Table Extraction (additional AFR costs)
ENABLE_ADVANCED_TABLE_EXTRACTION=false

# Section Hierarchy Extraction (additional processing)
ENABLE_SECTION_HIERARCHY=false

# OpenAI Configuration (if LLM enrichment enabled)
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini
```

### Performance Tuning

```bash
# Azure Form Recognizer Timeouts
AFR_POLLING_TIMEOUT=120
AFR_RETRY_ATTEMPTS=3
AFR_RETRY_DELAY=2
```

## Cost Analysis

### Azure Form Recognizer Costs

- **prebuilt-layout model**: ~$1.50 per 1000 pages
- Charged per page analyzed
- Free tier: 500 pages/month

### LLM Enrichment Costs (Optional)

- **gpt-4o-mini**: ~$0.002 per document (recommended)
- **gpt-4o**: ~$0.02 per document (premium)
- Only incurred if `ENABLE_LLM_ENRICHMENT=true`

### Cost Optimization Tips

1. **Disable LLM enrichment for high-volume processing**
   ```bash
   ENABLE_LLM_ENRICHMENT=false
   ```

2. **Use converted files when possible**
   - Parsing PDF is more cost-effective than parsing DOCX
   - The conversion step already creates PDFs

3. **Monitor usage in Azure Portal**
   - Set up cost alerts
   - Track parsing volume

## Usage

### Celery Task

The parsing is automatically triggered after file conversion:

```python
from app.tasks.parsing_tasks import parse_file_task

# Trigger parsing
result = parse_file_task.delay(
    file_id="uuid",
    org_id="org-uuid",
    project_id="project-uuid"
)
```

### Direct Parser Usage

For testing or standalone use:

```python
from app.tasks.parsing import PDFParser

# Parse PDF
parser = PDFParser(
    file_content=pdf_bytes,
    filename="document.pdf",
    document_id="uuid"
)

enriched_json = await parser.parse()
```

## Pipeline Flow

```
Upload → Conversion → Parsing → Chunking → Embedding → Indexing
          ↓            ↓
     (if needed)   (enriched JSON)
```

1. **Upload**: User uploads file via API
2. **Conversion**: Convert to PDF if needed (DOC, DOCX, XLS, PPT)
3. **Parsing**: Extract content with viewport coordinates (THIS MODULE)
4. **Chunking**: Split into semantic chunks (future)
5. **Embedding**: Create vector embeddings (future)
6. **Indexing**: Store in vector database (future)

## Database Updates

After successful parsing, the `File` model is updated:

- `parsing_started_at`: Timestamp when parsing began
- `parsing_completed_at`: Timestamp when parsing finished
- `enriched_file_path`: Azure Blob path to enriched JSON
- `document_metadata`: LLM-enriched headers (if available)
- `status`: Updated to `PARSING_COMPLETE` or `PARSING_FAILED`

## Error Handling

The module implements comprehensive error handling:

1. **Configuration validation**: Checks required credentials on startup
2. **Retry logic**: Automatic retry for transient failures (rate limits, timeouts)
3. **Graceful degradation**: LLM enrichment failures don't block parsing
4. **Status tracking**: Database status updates at each stage

## Extending the Module

### Adding a New Parser

1. Create new parser file (e.g., `word_parser.py`)
2. Inherit from `BaseParser`
3. Implement the `parse()` method
4. Register in `__init__.py`
5. Update `get_parser_for_file()` in `parsing_tasks.py`

Example:

```python
from .base_parser import BaseParser

class WordParser(BaseParser):
    async def parse(self) -> dict[str, Any]:
        # Your parsing logic
        sections = []
        page_info = {}

        # Optional LLM enrichment
        text = self._extract_text_from_sections(sections)
        headers = await self._enrich_with_llm(text)

        return self._create_enriched_json_structure(
            sections=sections,
            page_info=page_info,
            headers=headers
        )
```

### Adding a New Parsing Service

1. Update `config.py` with new service option
2. Create client wrapper (e.g., `utils/textract_client.py`)
3. Update parsers to support both services
4. Add configuration examples to `.env.example`

## Testing

### Local Testing

```bash
# Set up environment
cp .env.example .env.dev
# Fill in AZURE_AFR_ENDPOINT and AZURE_AFR_API_KEY

# Install dependencies
pip install -r requirements.txt

# Start Celery worker
celery -A app.celery_app worker --loglevel=info

# Upload a test file through the API
# Monitor Celery logs for parsing progress
```

### Test Files

Store test files in `test_data/parsing/`:
- `test_data/parsing/pdf/sample.pdf`
- `test_data/parsing/excel/sample.xlsx`
- `test_data/parsing/ppt/sample.pptx`

## Monitoring

Key metrics to monitor:

1. **Parsing success rate**: `PARSING_COMPLETE` vs `PARSING_FAILED`
2. **Average parsing time**: `parsing_completed_at - parsing_started_at`
3. **Azure AFR usage**: Track API calls in Azure Portal
4. **LLM enrichment usage**: Track OpenAI API calls (if enabled)
5. **Cost per document**: Azure AFR + OpenAI costs

## Deployment

### As Part of Monolith

The module is currently integrated into the main application.

### As Separate Microservice (Future)

The module is designed to be extracted:

1. Copy `app/tasks/parsing/` directory
2. Add minimal FastAPI wrapper or standalone Celery worker
3. Configure separate database for parsing status
4. Update `parsing_tasks.py` to publish results via queue/webhook

## Troubleshooting

### "Azure Form Recognizer not configured"

**Solution**: Set `AZURE_AFR_ENDPOINT` and `AZURE_AFR_API_KEY` in `.env`

### "AFR analysis timeout"

**Solution**: Increase `AFR_POLLING_TIMEOUT` for large documents

### "LLM enrichment failed"

**Solution**: This is non-blocking. Check:
- `OPENAI_API_KEY` is set correctly
- OpenAI account has credits
- Or disable with `ENABLE_LLM_ENRICHMENT=false`

### Parsing takes too long

**Solutions**:
1. Increase `AFR_POLLING_TIMEOUT`
2. Check document size (very large PDFs may need longer timeout)
3. Disable optional features (`ENABLE_LLM_ENRICHMENT=false`)

## Future Enhancements

- [ ] Add AWS Textract as alternative parsing service
- [ ] Add LlamaParse integration for complex documents
- [ ] Implement document complexity scoring for smart routing
- [ ] Add section hierarchy extraction (heading levels)
- [ ] Add image extraction and OCR
- [ ] Add audio/email parsing
- [ ] Implement cost tracking and reporting
- [ ] Add batch parsing for high-volume processing

## References

- [Azure Form Recognizer Documentation](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Celery Documentation](https://docs.celeryq.dev/)
