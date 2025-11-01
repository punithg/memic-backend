# Enriched JSON Format Specification

## Overview

This document defines the complete structure of the "enriched JSON" output from the document parsing module. This JSON represents a **digital twin** of each document, breaking it down into structured sections with spatial coordinates and metadata.

---

## Complete Structure

```json
{
  "sections": [
    {
      "content": "string",
      "type": "paragraph" | "table",
      "viewport": [x1, y1, x2, y2, x3, y3, x4, y4],
      "offset": 0,
      "page_number": 1,
      "role": "title" | "sectionHeading" | "pageHeader" | "pageFooter" | null,
      "row_count": 5,       // Only for tables
      "column_count": 3     // Only for tables
    }
  ],
  "page_info": {
    "1": {
      "width": 8.5,
      "height": 11.0,
      "unit": "inch",
      "angle": 0
    }
  },
  "headers": {
    "document_type": "string",
    "summary": "string",
    "tags": ["string"],
    "date_of_authoring": "YYYY-MM-DD" | null,
    "source": "string" | null,
    "reliability": "high" | "medium" | "low"
  },
  "metadata": {
    "document_id": "uuid-string",
    "file_name": "string",
    "parser": "PDFParser" | "ExcelParser" | "PowerPointParser",
    "parsing_service": "azure_form_recognizer",
    "created_at": "ISO-8601 timestamp",
    "file_size": 123456,
    "total_pages": 10,
    "total_sections": 45,
    "total_tables": 5,
    "file_type": "pdf" | "excel" | "powerpoint"
  }
}
```

---

## Field Definitions

### Root Level

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sections` | Array | Yes | List of document content blocks (paragraphs and tables) |
| `page_info` | Object | Yes | Page dimensions indexed by page number |
| `headers` | Object | No | LLM-enriched metadata (empty if `ENABLE_LLM_ENRICHMENT=false`) |
| `metadata` | Object | Yes | File and parsing metadata |

---

### `sections[]` - Content Blocks

Each section represents a discrete piece of content from the document.

#### Common Fields (All Sections)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | String | Yes | Text content or HTML table |
| `type` | String | Yes | `"paragraph"` or `"table"` |
| `viewport` | Array[8] | Yes | 8-point polygon: `[x1, y1, x2, y2, x3, y3, x4, y4]` |
| `offset` | Integer | Yes | Character position in original document |
| `page_number` | Integer | Yes | Page where this section appears (1-indexed) |

#### Paragraph-Specific Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | String | No | Semantic role: `"title"`, `"sectionHeading"`, `"pageHeader"`, `"pageFooter"`, or `null` |

#### Table-Specific Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `row_count` | Integer | Yes | Number of rows in table |
| `column_count` | Integer | Yes | Number of columns in table |

#### Viewport Coordinates

The `viewport` field uses an **8-point polygon** format (not bounding box):

```
[x1, y1, x2, y2, x3, y3, x4, y4]
 └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘
   │      │      │      │
  Top    Top   Bottom Bottom
  Left   Right  Right  Left
```

**Why 8 points instead of 4?**
- Handles rotated text and elements
- Matches Azure Form Recognizer output format
- More accurate for skewed documents

**Coordinate System:**
- Origin: Top-left corner of page
- Units: Inches (specified in `page_info`)
- X increases rightward
- Y increases downward

---

### `page_info` - Page Dimensions

Indexed by page number (string keys: `"1"`, `"2"`, etc.)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `width` | Float | Yes | Page width in specified unit |
| `height` | Float | Yes | Page height in specified unit |
| `unit` | String | Yes | Measurement unit (usually `"inch"`) |
| `angle` | Float | No | Page rotation angle in degrees (0 if not rotated) |

---

### `headers` - LLM-Enriched Metadata

**Only populated if `ENABLE_LLM_ENRICHMENT=true`**. Otherwise, this is an empty object `{}`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `document_type` | String | Yes | Category (e.g., "technical_specification", "invoice", "contract") |
| `summary` | String | Yes | 1-2 sentence document summary |
| `tags` | Array[String] | Yes | 3-5 relevant tags for categorization |
| `date_of_authoring` | String | No | Date in YYYY-MM-DD format (if extractable) |
| `source` | String | No | Source/origin if identifiable |
| `reliability` | String | Yes | Confidence: `"high"`, `"medium"`, or `"low"` |

---

### `metadata` - File and Parsing Metadata

#### Common Fields (All File Types)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `document_id` | String | Yes | UUID of the file record |
| `file_name` | String | Yes | Original filename |
| `parser` | String | Yes | Parser class used: `"PDFParser"`, `"ExcelParser"`, `"PowerPointParser"` |
| `parsing_service` | String | Yes | Service used (currently `"azure_form_recognizer"`) |
| `created_at` | String | Yes | ISO-8601 timestamp of parsing |
| `file_size` | Integer | Yes | File size in bytes |

#### File-Type Specific Fields

| Field | Type | File Types | Description |
|-------|------|------------|-------------|
| `total_pages` | Integer | PDF, PowerPoint | Number of pages/slides |
| `total_sections` | Integer | All | Total number of sections extracted |
| `total_tables` | Integer | Excel | Number of tables (for Excel files) |
| `total_slides` | Integer | PowerPoint | Alias for `total_pages` in PowerPoint |
| `file_type` | String | Excel, PowerPoint | `"excel"` or `"powerpoint"` |

---

## Real-World Examples

### Example 1: PDF Document

```json
{
  "sections": [
    {
      "content": "Technical Specification Document",
      "type": "paragraph",
      "viewport": [1.0, 1.0, 7.5, 1.0, 7.5, 1.5, 1.0, 1.5],
      "offset": 0,
      "page_number": 1,
      "role": "title"
    },
    {
      "content": "Introduction",
      "type": "paragraph",
      "viewport": [1.0, 2.0, 3.0, 2.0, 3.0, 2.3, 1.0, 2.3],
      "offset": 35,
      "page_number": 1,
      "role": "sectionHeading"
    },
    {
      "content": "This document outlines the technical requirements for the Memic backend system. The system is designed to handle document processing, parsing, and embedding generation for RAG applications.",
      "type": "paragraph",
      "viewport": [1.0, 2.5, 7.5, 2.5, 7.5, 3.2, 1.0, 3.2],
      "offset": 48,
      "page_number": 1,
      "role": null
    },
    {
      "content": "<table>\n  <tr><th>Component</th><th>Technology</th><th>Purpose</th></tr>\n  <tr><td>API</td><td>FastAPI</td><td>REST endpoints</td></tr>\n  <tr><td>Database</td><td>PostgreSQL</td><td>Data storage</td></tr>\n  <tr><td>Queue</td><td>Celery</td><td>Async tasks</td></tr>\n</table>",
      "type": "table",
      "viewport": [1.0, 4.0, 7.5, 4.0, 7.5, 6.0, 1.0, 6.0],
      "offset": 250,
      "page_number": 1,
      "row_count": 4,
      "column_count": 3
    }
  ],
  "page_info": {
    "1": {
      "width": 8.5,
      "height": 11.0,
      "unit": "inch",
      "angle": 0
    },
    "2": {
      "width": 8.5,
      "height": 11.0,
      "unit": "inch",
      "angle": 0
    }
  },
  "headers": {
    "document_type": "technical_specification",
    "summary": "Technical specification document outlining the architecture and requirements for the Memic backend system, including API design, database schema, and task queue implementation.",
    "tags": ["technical", "backend", "architecture", "specification", "API"],
    "date_of_authoring": "2024-10-31",
    "source": "internal",
    "reliability": "high"
  },
  "metadata": {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "file_name": "technical_spec.pdf",
    "parser": "PDFParser",
    "parsing_service": "azure_form_recognizer",
    "created_at": "2024-10-31T14:30:00.123456Z",
    "file_size": 245678,
    "total_pages": 2,
    "total_sections": 15
  }
}
```

### Example 2: Excel Document

```json
{
  "sections": [
    {
      "content": "Q4 Sales Report",
      "type": "paragraph",
      "viewport": [0.5, 0.5, 4.0, 0.5, 4.0, 0.8, 0.5, 0.8],
      "offset": 0,
      "page_number": 1,
      "role": "title"
    },
    {
      "content": "<table>\n  <tr><th>Region</th><th>Product</th><th>Revenue</th><th>Units</th></tr>\n  <tr><td>North America</td><td>Product A</td><td>$125,000</td><td>500</td></tr>\n  <tr><td>North America</td><td>Product B</td><td>$89,000</td><td>350</td></tr>\n  <tr><td>Europe</td><td>Product A</td><td>$98,000</td><td>420</td></tr>\n  <tr><td>Asia</td><td>Product C</td><td>$156,000</td><td>680</td></tr>\n</table>",
      "type": "table",
      "viewport": [0.5, 1.0, 8.0, 1.0, 8.0, 4.5, 0.5, 4.5],
      "offset": 17,
      "page_number": 1,
      "row_count": 5,
      "column_count": 4
    }
  ],
  "page_info": {
    "1": {
      "width": 11.0,
      "height": 8.5,
      "unit": "inch",
      "angle": 0
    }
  },
  "headers": {
    "document_type": "sales_report",
    "summary": "Q4 sales report showing revenue and unit sales by region and product, with data for North America, Europe, and Asia.",
    "tags": ["sales", "revenue", "Q4", "report", "regional"],
    "date_of_authoring": null,
    "source": "internal",
    "reliability": "high"
  },
  "metadata": {
    "document_id": "660e8400-e29b-41d4-a716-446655440001",
    "file_name": "Q4_sales.xlsx",
    "parser": "ExcelParser",
    "parsing_service": "azure_form_recognizer",
    "created_at": "2024-10-31T14:35:00.789012Z",
    "file_size": 45123,
    "total_tables": 1,
    "file_type": "excel"
  }
}
```

### Example 3: PowerPoint Presentation

```json
{
  "sections": [
    {
      "content": "Memic Platform Overview",
      "type": "paragraph",
      "viewport": [2.0, 3.0, 8.0, 3.0, 8.0, 4.0, 2.0, 4.0],
      "offset": 0,
      "page_number": 1,
      "role": "title"
    },
    {
      "content": "Q4 2024",
      "type": "paragraph",
      "viewport": [4.0, 4.5, 6.0, 4.5, 6.0, 5.0, 4.0, 5.0],
      "offset": 24,
      "page_number": 1,
      "role": null
    },
    {
      "content": "Key Features",
      "type": "paragraph",
      "viewport": [1.5, 2.0, 4.0, 2.0, 4.0, 2.5, 1.5, 2.5],
      "offset": 35,
      "page_number": 2,
      "role": "sectionHeading"
    },
    {
      "content": "Document processing pipeline with automatic conversion, parsing, and embedding generation for enterprise RAG applications.",
      "type": "paragraph",
      "viewport": [1.5, 3.0, 8.5, 3.0, 8.5, 4.2, 1.5, 4.2],
      "offset": 48,
      "page_number": 2,
      "role": null
    }
  ],
  "page_info": {
    "1": {
      "width": 10.0,
      "height": 7.5,
      "unit": "inch",
      "angle": 0
    },
    "2": {
      "width": 10.0,
      "height": 7.5,
      "unit": "inch",
      "angle": 0
    },
    "3": {
      "width": 10.0,
      "height": 7.5,
      "unit": "inch",
      "angle": 0
    }
  },
  "headers": {
    "document_type": "presentation",
    "summary": "Platform overview presentation for Memic, highlighting key features of the document processing pipeline including conversion, parsing, and embedding generation capabilities.",
    "tags": ["presentation", "platform", "overview", "features", "enterprise"],
    "date_of_authoring": "2024-10-31",
    "source": "internal",
    "reliability": "high"
  },
  "metadata": {
    "document_id": "770e8400-e29b-41d4-a716-446655440002",
    "file_name": "platform_overview.pptx",
    "parser": "PowerPointParser",
    "parsing_service": "azure_form_recognizer",
    "created_at": "2024-10-31T14:40:00.456789Z",
    "file_size": 1234567,
    "total_slides": 3,
    "total_sections": 12,
    "file_type": "powerpoint"
  }
}
```

### Example 4: When LLM Enrichment is Disabled

```json
{
  "sections": [...],
  "page_info": {...},
  "headers": {},
  "metadata": {
    "document_id": "880e8400-e29b-41d4-a716-446655440003",
    "file_name": "document.pdf",
    "parser": "PDFParser",
    "parsing_service": "azure_form_recognizer",
    "created_at": "2024-10-31T14:45:00.123456Z",
    "file_size": 123456,
    "total_pages": 5,
    "total_sections": 20
  }
}
```

---

## Design Decisions & Rationale

### 1. Why "viewport" instead of "bounding_box"?

**Rationale:**
- More semantic: "viewport" implies the viewing area/region
- Avoids confusion with traditional rectangular bounding boxes
- Better describes the 8-point polygon nature

### 2. Why 8-point polygon instead of 4-point rectangle?

**Rationale:**
- Handles rotated or skewed text accurately
- Matches Azure Form Recognizer's native output
- Future-proof for complex document layouts
- More precise spatial information

### 3. Why separate `sections` array instead of page-based hierarchy?

**Current format:**
```json
{
  "sections": [
    {"content": "...", "page_number": 1},
    {"content": "...", "page_number": 1},
    {"content": "...", "page_number": 2}
  ]
}
```

**Alternative (page-based):**
```json
{
  "pages": {
    "1": {"sections": [...]},
    "2": {"sections": [...]}
  }
}
```

**Rationale for flat array:**
- Easier to iterate through all content linearly
- Simpler chunking logic (just slice the array)
- Page info still available via `page_number` field
- More flexible for cross-page elements

**⚠️ DECISION POINT: Do you prefer flat array or page-based hierarchy?**

### 4. Why store tables as HTML instead of JSON?

**Current format:**
```json
{
  "content": "<table><tr><td>Cell 1</td></tr></table>",
  "type": "table"
}
```

**Alternative (structured):**
```json
{
  "content": {
    "rows": [
      {"cells": [{"content": "Cell 1", "row_span": 1}]}
    ]
  },
  "type": "table"
}
```

**Rationale for HTML:**
- Preserves formatting (merged cells, headers)
- Easy to render in UI
- Standard format understood by LLMs
- Compact representation

**⚠️ DECISION POINT: Keep HTML or switch to structured JSON for tables?**

### 5. Why nullable `role` field instead of always present?

**Rationale:**
- Not all paragraphs have semantic roles
- Azure Form Recognizer only provides roles for specific elements
- `null` clearly indicates "no special role" vs missing data

---

## Questions for Final Format Decision

Please review and decide:

### 1. **Structure: Flat vs Hierarchical**

**Option A (Current): Flat sections array**
```json
{
  "sections": [
    {"content": "...", "page_number": 1},
    {"content": "...", "page_number": 2}
  ]
}
```

**Option B: Page-based hierarchy**
```json
{
  "pages": {
    "1": {"sections": [...]},
    "2": {"sections": [...]}
  }
}
```

**Your preference:** A or B?

### 2. **Tables: HTML vs Structured JSON**

**Option A (Current): HTML string**
```json
{
  "content": "<table>...</table>",
  "type": "table"
}
```

**Option B: Structured JSON**
```json
{
  "content": {
    "rows": [
      {"cells": [{"text": "...", "row_span": 1, "col_span": 1}]}
    ]
  },
  "type": "table"
}
```

**Your preference:** A or B?

### 3. **Viewport Coordinates: Keep 8-point polygon?**

Current: `[x1, y1, x2, y2, x3, y3, x4, y4]`

Alternative: `{"top_left": [x, y], "top_right": [x, y], ...}`

**Your preference:** Keep array or switch to object?

### 4. **Metadata: Any additional fields needed?**

Current metadata fields:
- `document_id`, `file_name`, `parser`, `parsing_service`
- `created_at`, `file_size`, `total_pages`, etc.

Do you need:
- `language`: Detected document language?
- `confidence_score`: Overall parsing confidence?
- `processing_time`: Time taken to parse?
- `version`: Schema version for future compatibility?

### 5. **Headers: Any additional LLM-extracted fields?**

Current headers:
- `document_type`, `summary`, `tags`, `date_of_authoring`, `source`, `reliability`

Do you need:
- `key_entities`: Named entities (people, organizations)?
- `sentiment`: Document sentiment analysis?
- `classification`: Multi-level classification?
- `relationships`: References to other documents?

---

## Storage Location

The enriched JSON is stored in Azure Blob Storage at:

```
{org_id}/{project_id}/{file_id}/enriched/enriched.json
```

The path is also saved in the database:
- `File.enriched_file_path`
- `File.document_metadata` (stores the `headers` object for quick querying)

---

## Schema Version

**Current Version:** `1.0`

Future versions will increment as the schema evolves. Consider adding a `schema_version` field to `metadata` for forward compatibility.

---

Please review this specification and let me know:
1. Which options you prefer for the decision points
2. Any additional fields needed
3. Any changes to terminology or structure
4. Whether we should add a schema version field

Once you approve, I'll update the implementation to match the final format!
