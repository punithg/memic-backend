# Test Data for Memic RAG Pipeline

This directory contains test files for validating the RAG pipeline functionality.

## Directory Structure

```
test_data/
├── README.md              # This file
├── text/                  # Text files (.txt, .md)
├── office/                # Office documents (.docx, .doc, .xls, .xlsx, .ppt, .pptx)
├── pdf/                   # PDF documents
├── images/                # Images (.png, .jpg, .jpeg)
├── audio/                 # Audio files (.mp3, .wav, .m4a, etc.)
└── email/                 # Email files (.eml, .msg)
```

## Test Files

### Text Files
- `test_document.txt` - Comprehensive test document with headings, lists, and content

### Purpose

These test files are used to verify:
1. File upload to Azure Blob Storage
2. File conversion to PDF (where applicable)
3. Document parsing and content extraction
4. Semantic chunking
5. Vector embedding generation
6. End-to-end RAG pipeline functionality

## Testing Instructions

### Using the API

1. Start services:
```bash
# Terminal 1: Start Celery Worker
celery -A app.celery_app worker --loglevel=info -Q files,conversion,parsing,chunking,embedding

# Terminal 2: Start FastAPI Server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Upload test file:
```bash
curl -X POST http://localhost:8000/api/v1/projects/{PROJECT_ID}/files \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -F "file=@test_data/text/test_document.txt"
```

3. Monitor progress:
```bash
curl http://localhost:8000/api/v1/projects/{PROJECT_ID}/files/{FILE_ID}/status \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```

### Expected File Processing States

1. UPLOADING → UPLOADED
2. CONVERSION_STARTED → CONVERSION_COMPLETE (if file needs conversion)
3. PARSING_STARTED → PARSING_COMPLETE
4. CHUNKING_STARTED → CHUNKING_COMPLETE
5. EMBEDDING_STARTED → EMBEDDING_COMPLETE
6. READY

## Supported File Formats

### Formats Requiring Conversion (to PDF via LibreOffice)
- Word: .doc, .docx
- Excel (old): .xls
- PowerPoint (old): .ppt
- Images: .jpg, .jpeg, .png

### Formats Processed Directly (No Conversion)
- PDF: .pdf
- JSON: .json
- Excel (modern): .xlsx
- PowerPoint (modern): .pptx
- Audio: .mp3, .wav, .m4a, .flac, .ogg, .aac
- Email: .eml, .msg

## Adding New Test Files

When adding new test files:
1. Place in appropriate subdirectory by format
2. Use descriptive filenames (e.g., `test_invoice_large.pdf`)
3. Document the file purpose and test case in this README
4. Keep file sizes reasonable (< 10MB when possible)
5. Ensure files contain representative content for testing

## Verification Checklist

After uploading a test file, verify:
- [ ] File appears in Azure Blob Storage (raw/)
- [ ] Conversion creates PDF if needed (converted/)
- [ ] Parsing extracts content properly (enriched/)
- [ ] Chunks are created in database
- [ ] Vector embeddings are generated
- [ ] File status reaches READY
- [ ] No errors in Celery worker logs
