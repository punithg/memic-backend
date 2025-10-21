# Phase 1 Testing Guide

This guide will help you set up and test the RAG system Phase 1 implementation.

## Prerequisites

1. Python 3.14 (already installed)
2. PostgreSQL running (already configured)
3. Redis server (for Celery)
4. Azure Blob Storage account

## Step 1: Install Dependencies

```bash
cd /Users/punithg/HaruLabs/memic-backend
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Set Up Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Application Settings
APP_ENV=dev
DEBUG=True

# Database (already configured)
DATABASE_URL=postgresql+psycopg://punithg@localhost:5432/memic_dev

# JWT & Security
JWT_SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# OpenAI (for future use)
OPENAI_API_KEY=your-openai-api-key

# Azure Blob Storage (REQUIRED for Phase 1)
AZURE_STORAGE_CONNECTION_STRING=<PASTE_YOUR_CONNECTION_STRING_HERE>
AZURE_STORAGE_CONTAINER_NAME=memic-documents

# Pinecone (Optional for Phase 1)
PINECONE_API_KEY=<OPTIONAL_FOR_NOW>
PINECONE_ENVIRONMENT=gcp-starter
PINECONE_INDEX_NAME=memic-rag

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# RAG Processing
CHUNK_SIZE=512
CHUNK_OVERLAP=50
EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDING_DIMENSION=1536
```

## Step 3: Get Azure Blob Storage Connection String

### Option A: From Azure Portal
1. Go to Azure Portal: https://portal.azure.com
2. Navigate to your Storage Account
3. Left sidebar → "Access keys"
4. Copy "Connection string" from either key1 or key2

### Option B: Using Azure CLI
```bash
az storage account show-connection-string \
  --name <your-storage-account-name> \
  --resource-group <your-resource-group>
```

The connection string looks like:
```
DefaultEndpointsProtocol=https;AccountName=mystorageaccount;AccountKey=xxxxx;EndpointSuffix=core.windows.net
```

## Step 4: Install and Start Redis

### macOS (using Homebrew)
```bash
brew install redis
brew services start redis

# Or run in foreground
redis-server
```

### Ubuntu/Debian
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### Verify Redis is running
```bash
redis-cli ping
# Should return: PONG
```

## Step 5: Start the Services

You'll need **3 terminal windows**:

### Terminal 1: Start Celery Worker
```bash
cd /Users/punithg/HaruLabs/memic-backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info
```

You should see:
```
-------------- celery@hostname v5.3.4
---- **** ----- 
--- * ***  * -- Darwin-24.6.0-arm64
-- * - **** --- 
- ** ---------- [config]
- ** ---------- .> app:         memic_rag:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 8 (prefork)
-- ******* ---- .> task events: OFF
--- ***** ----- 
 -------------- [queues]
                .> files            exchange=files(direct) key=files
                .> conversion       exchange=conversion(direct) key=conversion
                .> parsing          exchange=parsing(direct) key=parsing
                .> chunking         exchange=chunking(direct) key=chunking
                .> embedding        exchange=embedding(direct) key=embedding

[tasks]
  . app.tasks.conversion_tasks.convert_file
  . app.tasks.chunking_tasks.chunk_file
  . app.tasks.embedding_tasks.embed_chunks
  . app.tasks.file_tasks.process_file_pipeline
  . app.tasks.file_tasks.update_file_status
  . app.tasks.parsing_tasks.parse_file
```

### Terminal 2: Start FastAPI Server
```bash
cd /Users/punithg/HaruLabs/memic-backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 3: Monitor Redis (Optional)
```bash
redis-cli monitor
```

## Step 6: Test the API

### Using Postman

1. Open Postman
2. Import the collection: `memic-backend.postman_collection.json`
3. Follow the testing flow:

**Test Flow:**
1. **Signup** → Creates user, saves `user_id`
2. **Login** → Gets token, saves `access_token`
3. **Create Organization** → Saves `org_id`
4. **Create Project** → Saves `project_id`
5. **Upload File** → Saves `file_id`, triggers RAG pipeline
6. **Get File Status** → Check processing progress
7. **List Files** → See all files in project
8. **Get File Details** → Full file information

### Using cURL

#### 1. Signup
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@memic.ai",
    "password": "password123",
    "name": "Test User"
  }'
```

#### 2. Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@memic.ai",
    "password": "password123"
  }'
# Save the access_token from response
```

#### 3. Create Organization
```bash
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Test Organization"
  }'
# Save the org_id from response
```

#### 4. Create Project
```bash
curl -X POST http://localhost:8000/api/v1/organizations/ORG_ID/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Test Project"
  }'
# Save the project_id from response
```

#### 5. Upload File
```bash
curl -X POST http://localhost:8000/api/v1/projects/PROJECT_ID/files \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/your/test.pdf"
# Save the file_id from response
```

#### 6. Get File Status
```bash
curl -X GET http://localhost:8000/api/v1/projects/PROJECT_ID/files/FILE_ID/status \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Step 7: What to Expect (Phase 1 Behavior)

### File Upload Flow:
1. **File uploads** → Stored in Azure Blob Storage at `org_id/project_id/file_id/raw/filename`
2. **Status: UPLOADING → UPLOADED**
3. **Celery pipeline triggered automatically**
4. **Status progression** (each stage takes ~2 seconds):
   - CONVERSION_STARTED → CONVERSION_COMPLETE (if not PDF)
   - PARSING_STARTED → PARSING_COMPLETE
   - CHUNKING_STARTED → CHUNKING_COMPLETE (creates 3 dummy chunks)
   - EMBEDDING_STARTED → EMBEDDING_COMPLETE
   - **READY** (file is ready for retrieval)

### Check Celery Worker Logs
You should see log output like:
```
[INFO] [STUB] Starting conversion for file <file_id>
[INFO] [STUB] Conversion simulation complete for file <file_id>
[INFO] [STUB] Starting parsing for file <file_id>
[INFO] [STUB] Parsing simulation complete for file <file_id>
[INFO] [STUB] Starting chunking for file <file_id>
[INFO] [STUB] Chunking simulation complete for file <file_id>
[INFO] [STUB] Starting embedding for file <file_id>
[INFO] [STUB] File <file_id> is now READY for retrieval
```

### Check Database
```sql
-- Connect to database
psql -U punithg -d memic_dev

-- Check file status
SELECT id, name, status, total_chunks, created_at 
FROM files 
ORDER BY created_at DESC 
LIMIT 5;

-- Check chunks created
SELECT file_id, chunk_index, token_count, vector_id 
FROM file_chunks 
WHERE file_id = 'YOUR_FILE_ID';

-- Check timestamps
SELECT 
  name,
  status,
  parsing_started_at,
  parsing_completed_at,
  chunking_completed_at,
  embedding_completed_at
FROM files 
WHERE id = 'YOUR_FILE_ID';
```

## Troubleshooting

### Redis Connection Error
```
Error: Error 61 connecting to localhost:6379. Connection refused.
```
**Solution:** Start Redis server
```bash
redis-server
```

### Azure Blob Storage Error
```
Error: Azure Storage connection string not configured
```
**Solution:** Set `AZURE_STORAGE_CONNECTION_STRING` in your `.env` file

### Celery Worker Not Starting
```
ImportError: cannot import name 'celery_app'
```
**Solution:** Make sure you're in the project root and virtual environment is activated

### Database Migration Not Applied
```
sqlalchemy.exc.ProgrammingError: (psycopg.errors.UndefinedTable) relation "files" does not exist
```
**Solution:** Run the migration
```bash
alembic upgrade head
```

## Success Indicators

✅ **Celery Worker**: Shows connected tasks and queues
✅ **FastAPI Server**: Running without errors at http://localhost:8000
✅ **File Upload**: Returns 201 with file_id
✅ **Pipeline Processing**: File status progresses through all stages
✅ **Chunks Created**: 3 dummy chunks in database
✅ **Final Status**: File reaches "READY" status
✅ **Azure Blob**: File visible in Azure Storage Explorer

## Next Steps

Once Phase 1 is working:
1. ✅ Verify all endpoints work
2. ✅ Check file status tracking
3. ✅ Confirm chunks are created
4. 🚀 **Ready for Phase 2** - Port real RAG logic

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

