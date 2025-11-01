# Headers vs Metadata: Design Decision

## The Problem

Currently, the enriched JSON has two separate top-level objects that both seem to contain "information about the document":

```json
{
  "sections": [...],
  "page_info": {...},
  "headers": {
    "document_type": "technical_specification",
    "summary": "...",
    "tags": [...],
    "date_of_authoring": "2024-10-31",
    "source": "internal",
    "reliability": "high"
  },
  "metadata": {
    "document_id": "uuid",
    "file_name": "doc.pdf",
    "parser": "PDFParser",
    "parsing_service": "azure_form_recognizer",
    "created_at": "2024-11-01T14:30:25Z",
    "file_size": 1245678,
    "total_pages": 5,
    "total_sections": 42
  }
}
```

**Question: Why do we need both `headers` and `metadata`? What's the distinction?**

---

## Current Design Rationale

### `headers` - WHAT THE DOCUMENT IS ABOUT
**Source:** Extracted from document content using AI/LLM (OpenAI)
**Purpose:** Semantic understanding of the document's content and meaning
**Cost:** ~$0.002 per document (if enabled)
**Toggleable:** Yes (`ENABLE_LLM_ENRICHMENT=false` makes this empty `{}`)

**Use Cases:**
- Search: "Find all invoices from last quarter"
- Classification: Route documents to appropriate workflows
- Tagging: Organize documents by topic
- Summary: Quick overview without reading full document
- Date extraction: "Documents authored in January 2024"

**Example:**
```json
{
  "document_type": "invoice",
  "summary": "Invoice for cloud services totaling $1,500 for October 2024",
  "tags": ["billing", "cloud", "Azure", "monthly"],
  "date_of_authoring": "2024-10-31",
  "source": "external_vendor",
  "reliability": "high"
}
```

### `metadata` - WHAT THE FILE IS (TECHNICAL INFO)
**Source:** Known from the file itself and parsing process (deterministic)
**Purpose:** Technical information about the file and how it was processed
**Cost:** $0 (no AI involved)
**Toggleable:** No (always present)

**Use Cases:**
- File management: Track which files have been processed
- Debugging: Which parser was used? When was it parsed?
- Storage: Link back to original file
- Audit: Processing timestamps and file sizes
- Performance: Track document complexity (pages, sections)

**Example:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "invoice_oct_2024.pdf",
  "parser": "PDFParser",
  "parsing_service": "azure_form_recognizer",
  "created_at": "2024-11-01T14:30:25.123456Z",
  "file_size": 1245678,
  "total_pages": 5,
  "total_sections": 42
}
```

---

## Side-by-Side Comparison

| Aspect | `headers` | `metadata` |
|--------|-----------|------------|
| **What it describes** | Document content/meaning | File properties/processing |
| **Data source** | AI extraction from content | File system + parsing engine |
| **Can change?** | Yes (reprocess with different prompt) | Mostly no (file properties are fixed) |
| **Costs money?** | Yes (if LLM enabled) | No |
| **Optional?** | Yes (feature flag) | No (always present) |
| **User-facing?** | Yes (shown in UI for search/filtering) | Mostly internal (shown in file details) |
| **Example field** | `document_type: "contract"` | `parser: "PDFParser"` |

---

## Alternative Design Options

### Option 1: Keep Separate (Current Design)
```json
{
  "headers": {
    "document_type": "invoice",
    "summary": "...",
    "tags": [...]
  },
  "metadata": {
    "document_id": "uuid",
    "file_name": "invoice.pdf",
    "parser": "PDFParser"
  }
}
```

**Pros:**
- Clear separation of concerns
- Easy to disable LLM enrichment (just empty headers)
- Matches common data engineering pattern (content vs metadata)

**Cons:**
- Two places to look for "information about the document"
- Name "headers" is confusing (borrowed from rag-parsing reference)

---

### Option 2: Merge into Single `metadata` Object
```json
{
  "metadata": {
    "document_id": "uuid",
    "file_name": "invoice.pdf",
    "parser": "PDFParser",
    "document_type": "invoice",
    "summary": "...",
    "tags": [...]
  }
}
```

**Pros:**
- Single place for all document information
- Simpler structure

**Cons:**
- Mixes AI-extracted (costly) with deterministic (free) data
- Harder to see what's optional vs always present
- Can't easily skip LLM fields (they'd be null instead of absent)

---

### Option 3: Rename for Clarity
```json
{
  "content_metadata": {  // or "semantic_info", "extracted_info"
    "document_type": "invoice",
    "summary": "...",
    "tags": [...]
  },
  "file_metadata": {  // or "technical_metadata", "processing_info"
    "document_id": "uuid",
    "file_name": "invoice.pdf",
    "parser": "PDFParser"
  }
}
```

**Pros:**
- Names are more self-explanatory
- Still maintains separation of concerns
- Clear what each contains

**Cons:**
- Longer names
- Still two objects

---

### Option 4: Nested Structure
```json
{
  "metadata": {
    "file": {
      "document_id": "uuid",
      "file_name": "invoice.pdf",
      "parser": "PDFParser"
    },
    "content": {
      "document_type": "invoice",
      "summary": "...",
      "tags": [...]
    }
  }
}
```

**Pros:**
- Single top-level key
- Clear hierarchy

**Cons:**
- Deeper nesting
- More verbose access: `metadata.content.document_type`

---

### Option 5: Separate Top-Level Keys (Most Explicit)
```json
{
  "sections": [...],
  "page_info": {...},
  "extracted_metadata": {  // LLM-extracted semantic info
    "document_type": "invoice",
    "summary": "...",
    "tags": [...]
  },
  "processing_metadata": {  // Technical processing info
    "document_id": "uuid",
    "file_name": "invoice.pdf",
    "parser": "PDFParser"
  }
}
```

**Pros:**
- Crystal clear naming
- Easy to understand at a glance

**Cons:**
- Verbose
- Four top-level keys

---

## Recommendation & Questions for You

### Current Terminology Issues

The name **"headers"** is borrowed from the rag-parsing reference implementation, but it's confusing because:
1. It doesn't mean HTTP headers
2. It doesn't mean document headers (like title, author in a Word doc)
3. It actually means "LLM-extracted semantic metadata about content"

### Questions for Final Decision

**1. Do you want to keep the separation between AI-extracted and deterministic data?**
   - ✅ **YES** → Helps with cost visibility, makes it clear what's optional
   - ❌ **NO** → Merge everything into one `metadata` object

**2. If keeping separation, what should we call them?**
   - Option A: `headers` + `metadata` (current, borrowed from rag-parsing)
   - Option B: `content_metadata` + `file_metadata`
   - Option C: `extracted_metadata` + `processing_metadata`
   - Option D: `semantic_info` + `technical_info`
   - Option E: `enrichment` + `metadata`
   - Option F: Your suggestion?

**3. Should we add more fields to either object?**

**Potential additions to `headers` (AI-extracted):**
- `language`: Detected document language ("en", "es", "fr")
- `key_entities`: Named entities (people, orgs, places)
- `sentiment`: Document tone ("positive", "neutral", "negative")
- `confidence_scores`: Per-field confidence from LLM
- `keywords`: Most important terms (vs tags which are categories)

**Potential additions to `metadata` (deterministic):**
- `schema_version`: For future compatibility ("1.0")
- `processing_time_ms`: How long parsing took
- `conversion_applied`: Was file converted? (true/false)
- `original_format`: Original file extension if converted
- `afr_model_version`: Azure Form Recognizer model used
- `errors`: List of non-fatal errors during parsing
- `warnings`: Processing warnings

**4. Database storage strategy:**

Currently:
- Full enriched JSON → Azure Blob Storage
- `headers` object → Copied to `File.document_metadata` (JSONB column)

Should we also store in database:
- Selected fields from `metadata` for fast querying?
- Keep only `headers` in DB as planned?
- Store both in separate DB columns?

---

## Real-World Usage Examples

### Use Case 1: Search by Document Type
```python
# With separate headers
files = db.query(File).filter(
    File.document_metadata['document_type'] == 'invoice'
).all()
```

### Use Case 2: Filter by Parser Used
```python
# Need to fetch from blob storage or add to DB
enriched_json = download_from_blob(file.enriched_file_path)
if enriched_json['metadata']['parser'] == 'PDFParser':
    # ...
```

### Use Case 3: Display in UI
```jsx
// Document card in UI
<Card>
  <Title>{headers.document_type}</Title>
  <Summary>{headers.summary}</Summary>
  <Tags>{headers.tags}</Tags>

  <Details>
    <Filename>{metadata.file_name}</Filename>
    <Pages>{metadata.total_pages}</Pages>
    <ParsedAt>{metadata.created_at}</ParsedAt>
  </Details>
</Card>
```

---

## My Recommendation

Based on B2B requirements and cost transparency:

**Keep separation but rename for clarity:**

```json
{
  "sections": [...],
  "page_info": {...},

  "enrichment": {
    "document_type": "invoice",
    "summary": "...",
    "tags": [...],
    "date_of_authoring": "2024-10-31",
    "source": "internal",
    "reliability": "high"
  },

  "metadata": {
    "document_id": "uuid",
    "file_name": "invoice.pdf",
    "parser": "PDFParser",
    "parsing_service": "azure_form_recognizer",
    "created_at": "2024-11-01T14:30:25Z",
    "file_size": 1245678,
    "total_pages": 5,
    "total_sections": 42,
    "schema_version": "1.0"
  }
}
```

**Why "enrichment"?**
- Clearly indicates "value-added" data (costs money)
- Commonly used in data engineering
- Self-explanatory: data that enriches the raw content
- When empty (`{}`), obviously means "no enrichment applied"

**Why keep "metadata"?**
- Standard term for file/processing info
- Everyone understands what metadata means
- Clear it's deterministic technical data

---

## Your Decision Needed

Please choose:

1. **Structure:** Keep separate or merge?
2. **Naming (if separate):**
   - Option A: `headers` + `metadata` ← current
   - Option B: `enrichment` + `metadata` ← my recommendation
   - Option C: `content_metadata` + `file_metadata`
   - Option D: `extracted_metadata` + `processing_metadata`
   - Option E: Your choice?

3. **Additional fields:** Which ones from the lists above?

4. **Database storage:** What to store in `File.document_metadata`?
   - Just enrichment?
   - Just metadata?
   - Both?
   - Selected fields only?

Let me know your preferences and I'll update the implementation!
