# Image Extraction Analysis - Missing Feature Investigation

**Date:** November 1, 2025
**Status:** ⚠️ **IMAGE EXTRACTION FEATURE MISSING IN NEW PIPELINE**

---

## Executive Summary

The **old RAG pipeline** (`rag-parsing/`) had a **comprehensive image extraction feature** that:
1. Extracted images/charts/diagrams from documents using Azure Form Recognizer's "figures" data
2. Used OpenAI Vision API (GPT-4 Vision) to extract content from images
3. Integrated image-extracted text back into the enriched JSON

The **new RAG pipeline** (`app/tasks/parsing/`) is **missing this entire feature** due to using an older Azure SDK that doesn't support figure extraction.

---

## Key Findings

### 1. SDK Version Discrepancy

| Component | Old Implementation | New Implementation | Impact |
|-----------|-------------------|-------------------|--------|
| **Azure SDK** | `azure-ai-documentintelligence` | `azure-ai-formrecognizer==3.3.3` | ❌ Missing features |
| **Client Class** | `DocumentIntelligenceClient` | `DocumentAnalysisClient` | Different API |
| **Figures Support** | ✅ Yes - extracts figures/images | ❌ No - no figure extraction | **Critical** |
| **Markdown Output** | ✅ Yes - dual extraction (JSON + Markdown) | ❌ No - JSON only | Missing feature |

### 2. Image Extraction Workflow (Old Implementation)

The old implementation had a sophisticated image extraction pipeline:

```
1. Azure Form Recognizer Extraction
   ↓
   - Extracts 'figures' (images, charts, diagrams) with bounding boxes
   - Returns both JSON and Markdown formats

2. Figure Detection & Cropping
   ↓
   - Identifies figures from AFR result
   - Crops images from PDF using PyMuPDF (fitz)
   - Saves cropped images to /tmp/

3. OpenAI Vision Processing
   ↓
   - Encodes images to base64
   - Calls GPT-4 Vision API for each image
   - Prompt: "Extract all the details only for the charts and infographs
     present in the image, don't miss out on any details for charts or
     infographs present. Provide the output in json format"

4. Integration into Enriched JSON
   ↓
   - Combines vision-extracted content with paragraphs/tables
   - Maintains bounding box metadata
   - Adds to sections with type="figure"
```

### 3. Code Evidence

#### Old Implementation Files with Image Extraction:

1. **`rag-parsing/src/parsers/pdf/notebook.py`**
   - `ImageContentExtraction` class (lines 958-1033)
   - `_crop_and_save_images_from_figures()` method
   - `_encode_image()` - Base64 encoding
   - `_make_openai_call()` - GPT-4 Vision API call
   - `_process_single_image()` - Full image processing pipeline

2. **`rag-parsing/src/parsers/ppt/premium_extraction.py`**
   - Image extraction for PowerPoint presentations
   - `_crop_and_save_images_from_figures()` (lines 276-310)
   - OpenAI Vision integration (lines 324-379)
   - INFOGRAPHICS_EXTRACTION_PROMPT constant

3. **`rag-parsing/src/parsers/email/extraction.py`**
   - Email attachment image extraction
   - Similar pattern to PDF/PPT extraction

#### New Implementation - Missing Features:

1. **`app/tasks/parsing/pdf_parser.py`**
   - ❌ No image extraction code
   - ❌ No figure processing
   - ❌ No vision API integration

2. **`app/tasks/parsing/utils/afr_client.py`**
   - ❌ Uses `DocumentAnalysisClient` (older SDK)
   - ❌ No figure extraction from result
   - ❌ JSON-only extraction (no markdown)

### 4. Azure Form Recognizer Result Comparison

#### Old SDK (`azure-ai-documentintelligence`):
```python
result = await document_intelligence_client.begin_analyze_document(
    model_id="prebuilt-layout",
    body=document,
    content_type="application/octet-stream",
    output_content_format=DocumentContentFormat.MARKDOWN  # Optional
)

# Result includes:
# - result.figures  ← Image/chart/diagram detection
# - result.paragraphs
# - result.tables
# - result.pages
```

#### New SDK (`azure-ai-formrecognizer==3.3.3`):
```python
result = client.begin_analyze_document(
    model_id="prebuilt-layout",
    document=file_content
)

# Result includes:
# - result.paragraphs
# - result.tables
# - result.pages
# - result.key_value_pairs
# ❌ NO result.figures  ← Missing!
```

**Test Results:**
- Ran inspection on `sample2.pdf` (3.7MB)
- Old SDK would extract `figures` if present
- New SDK has **no figures attribute** - confirmed via `dir(result)` and `result.to_dict()`

---

## Missing Features Breakdown

### 1. ✅ Implemented in Old Pipeline | ❌ Missing in New Pipeline

| Feature | Old | New | Impact |
|---------|-----|-----|--------|
| **Figure/Image Detection** | ✅ | ❌ | High - Charts/diagrams not extracted |
| **Image Cropping** | ✅ | ❌ | High - Cannot isolate images |
| **OpenAI Vision Integration** | ✅ | ❌ | High - Image content not understood |
| **Base64 Encoding** | ✅ | ❌ | Medium - Required for Vision API |
| **Vision Output Integration** | ✅ | ❌ | High - Image content lost |
| **Markdown Extraction** | ✅ | ❌ | Medium - Alternative format unavailable |
| **Figure Metadata** | ✅ | ❌ | Medium - No bounding boxes for images |

### 2. Configuration for Vision API

#### Old Implementation had:
```python
# Config parameters (from rag-parsing/src/utils/config.py)
OPENAI_VISION_MODEL = "gpt-4o-2024-08-06"  # or "gpt-4-vision-preview"
OPENAI_VISION_TIMEOUT = 100
OPENAI_VISION_MAX_TOKENS = 3000
```

#### New Implementation has:
```python
# Config parameters (from app/config.py)
OPENAI_API_KEY = ...  # For LLM enrichment only
# ❌ No vision-specific configuration
# ❌ No vision model selection
# ❌ No vision timeout settings
```

### 3. Image Processing Dependencies

#### Old Implementation:
```python
# From rag-parsing/requirements.txt
PyMuPDF>=1.23.8  # fitz - for PDF image cropping
Pillow>=10.2.0   # PIL - for image processing
openai>=1.0.0    # Async OpenAI with vision support
```

#### New Implementation:
```python
# From requirements.txt
openai==1.54.4   # ✅ Has vision capability
# ❌ Missing PyMuPDF (fitz)
# ✅ Has Pillow (via transitive dependency)
```

---

## Document Types Affected

### Documents with Images/Charts/Diagrams:

| Document Type | Old Pipeline | New Pipeline | Impact |
|--------------|--------------|--------------|--------|
| **PDF with charts** | ✅ Extracts chart content | ❌ Charts ignored | High |
| **PDF with diagrams** | ✅ Extracts diagram text | ❌ Diagrams ignored | High |
| **PDF with images** | ✅ Extracts image content | ❌ Images ignored | Medium |
| **PowerPoint slides** | ✅ Extracts slide images | ❌ Likely missing | High |
| **Email attachments** | ✅ Extracts image content | ❌ Not implemented | Medium |
| **Infographics** | ✅ Full extraction | ❌ Completely missed | **Critical** |

### Documents Unaffected:

| Document Type | Status | Reason |
|--------------|--------|--------|
| Text-only PDFs | ✅ Works | No images to extract |
| Excel spreadsheets | ✅ Works | No image extraction needed |
| Pure text documents | ✅ Works | No visual content |

---

## Cost Implications

### Old Implementation Costs:

**Azure Form Recognizer:**
- Layout model: ~$10/1000 pages

**OpenAI Vision API:**
- GPT-4 Vision: ~$0.01-0.03 per image (depending on detail level)
- For a 50-page document with 20 charts: ~$0.20-0.60 per document

**Total estimated cost:** ~$0.50-1.00 per typical business document

### New Implementation Costs:

**Azure Form Recognizer:**
- Layout model: ~$10/1000 pages (same)

**OpenAI Vision API:**
- Not used: $0

**Total estimated cost:** ~$0.01 per document (10x cheaper but missing critical content)

**Trade-off:** Lower cost but **missing potentially critical information** from charts, diagrams, and infographics.

---

## Real-World Impact Examples

### Example 1: Financial Report with Charts
**Old Pipeline:**
- ✅ Extracts chart titles
- ✅ Extracts chart data labels
- ✅ Extracts chart legends
- ✅ Understands chart content via Vision API
- Result: Full searchable content including chart data

**New Pipeline:**
- ❌ Chart completely ignored
- ❌ No chart content in enriched JSON
- ❌ Cannot search chart data
- Result: **Missing critical financial data**

### Example 2: Technical Documentation with Diagrams
**Old Pipeline:**
- ✅ Extracts architecture diagrams
- ✅ Extracts component labels
- ✅ Extracts flow chart content
- Result: Diagrams converted to searchable text

**New Pipeline:**
- ❌ Diagrams ignored
- ❌ Architecture not captured
- ❌ Flow charts missing
- Result: **Incomplete technical documentation**

### Example 3: Presentation Decks
**Old Pipeline:**
- ✅ Extracts slide image content
- ✅ Captures embedded charts
- ✅ Processes infographics
- Result: Complete slide content

**New Pipeline:**
- ❌ Only text bullets extracted
- ❌ Visual content lost
- ❌ Infographics missing
- Result: **Incomplete presentation understanding**

---

## Technical Details

### How Figures Were Extracted (Old Implementation)

```python
# Step 1: Get figures from AFR result
figures = result.figures  # List of figure objects

# Step 2: Extract figure metadata
for figure in figures:
    bounding_regions = figure.bounding_regions  # Location on page
    page_number = bounding_regions[0].page_number
    polygon = bounding_regions[0].polygon  # Bounding box coordinates

# Step 3: Crop image from PDF
def _crop_and_save_images_from_figures(self, document, figures, output_folder, file_id, file_name, dpi=300):
    document_stream = BytesIO(document)
    document_reader = fitz.open(stream=document_stream)  # PyMuPDF

    for figure in figures:
        for region in figure.boundingRegions:
            page_number = region.pageNumber - 1
            polygon = region.polygon

            # Calculate bounding box
            x0 = min(polygon[0::2]) * 72
            y0 = min(polygon[1::2]) * 72
            x1 = max(polygon[0::2]) * 72
            y1 = max(polygon[1::2]) * 72

            # Crop and save
            page = document_reader.load_page(page_number)
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat, clip=fitz.Rect(x0, y0, x1, y1))
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            output_path = f"/tmp/{uuid.uuid4()}_page_{page_number + 1}.jpg"
            image.save(output_path, "JPEG")

# Step 4: Process with OpenAI Vision
async def _make_openai_call(self, base64_image):
    messages = [{
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Extract all the details only for the charts and infographs present in the image..."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high"
                }
            }
        ]
    }]

    response = await self.client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=messages,
        max_tokens=3000
    )
```

---

## Recommendations

### Option 1: Upgrade Azure SDK (Recommended)
**Action:** Upgrade from `azure-ai-formrecognizer==3.3.3` to `azure-ai-documentintelligence`

**Pros:**
- ✅ Enables figure extraction
- ✅ Access to latest features
- ✅ Markdown output format
- ✅ Future-proof

**Cons:**
- Requires code changes to new API
- Need to test compatibility
- Different client class

**Effort:** Medium (2-3 days)

### Option 2: Add Image Extraction Feature
**Action:** Port image extraction code from old implementation

**Components to add:**
1. Figure detection from AFR result
2. Image cropping using PyMuPDF
3. OpenAI Vision integration
4. Vision output integration into enriched JSON
5. Configuration for vision API

**Effort:** High (5-7 days)

### Option 3: Keep As-Is (Not Recommended)
**Action:** Accept that image/chart content won't be extracted

**Impact:**
- ❌ Charts/diagrams ignored
- ❌ Infographics lost
- ❌ Incomplete document understanding
- ❌ Lower RAG quality for visual-heavy documents

**Acceptable for:** Text-only documents only

---

## Migration Path (If Implementing)

### Phase 1: SDK Upgrade
1. Update `requirements.txt`: `azure-ai-documentintelligence`
2. Update `afr_client.py` to use `DocumentIntelligenceClient`
3. Test figure extraction with sample documents
4. Verify backward compatibility

### Phase 2: Figure Processing
1. Add PyMuPDF dependency
2. Implement figure cropping logic
3. Add image storage/temp file handling
4. Test with various document types

### Phase 3: Vision Integration
1. Add vision API configuration
2. Implement vision API calls
3. Add retry logic and error handling
4. Integrate vision output into enriched JSON

### Phase 4: Testing & Optimization
1. Test with image-heavy documents
2. Measure cost impact
3. Add feature flags for cost control
4. Performance optimization

**Estimated Total Effort:** 10-15 days

---

## Conclusion

### Current State:
- ✅ Text extraction: Working
- ✅ Table extraction: Working
- ❌ **Image/Chart extraction: MISSING**
- ❌ **Vision content: MISSING**

### Impact:
- **High Impact** for documents with charts, diagrams, infographics
- **Low Impact** for text-only documents

### Decision Required:
**Should image extraction be implemented in the new pipeline?**

**Factors to consider:**
1. **Content completeness** - Do users need chart/diagram content?
2. **Cost** - Vision API adds $0.20-0.60 per document
3. **Use case** - Are visual-heavy documents common?
4. **Timeline** - Can allocate 10-15 days for implementation?

---

## Test Results Summary

**Test File:** `sample2.pdf` (3.5 MB, 2 pages)

**Azure Form Recognizer 3.3.3 Output:**
- ✅ Pages: 2
- ✅ Paragraphs: 11
- ✅ Tables: 0
- ❌ **Figures: Not available** (attribute doesn't exist)

**Recommendation:** This specific PDF appears to be mostly text (cover page + confidentiality page), so image extraction may not be critical for this file. However, for typical business documents with charts and diagrams, the missing feature would be significant.

---

**Last Updated:** November 1, 2025
**Analyst:** Claude Code
**Status:** Investigation Complete - Awaiting Decision on Implementation
