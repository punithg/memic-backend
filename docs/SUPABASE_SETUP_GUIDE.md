# Supabase Setup & Testing Guide

This guide will help you set up Supabase and test the complete RAG system end-to-end.

## Why Supabase?

- Free tier with generous limits
- Simple setup (5 minutes)
- Built-in storage (S3-compatible)
- No credit card required
- Great for development and testing

## Step 1: Create Supabase Project

### 1.1 Sign Up
1. Go to https://supabase.com
2. Click "Start your project"
3. Sign up with GitHub (recommended) or email

### 1.2 Create New Project
1. Click "New Project"
2. Choose organization (or create one)
3. Fill in:
   - **Project name**: `memic-dev` (or anything you like)
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to you
4. Click "Create new project"
5. Wait 1-2 minutes for provisioning

### 1.3 Get Credentials
Once your project is ready:

1. Go to **Settings** (gear icon in sidebar) → **API**
2. Copy these values:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **anon public** key (long JWT token)

That's it! You're ready.

## Step 2: Install Dependencies

```bash
cd /Users/punithg/HaruLabs/memic-backend
source venv/bin/activate
pip install -r requirements.txt
```

This will install the new `supabase` package along with existing dependencies.

## Step 3: Configure Environment

Create a `.env` file in the project root:

```bash
# Application
APP_ENV=dev
DEBUG=True

# Database (already working)
DATABASE_URL=postgresql+psycopg://punithg@localhost:5432/memic_dev

# JWT & Security (generate random strings)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this
ENCRYPTION_KEY=another-secret-key-for-encryption

# Supabase Storage (PASTE YOUR VALUES HERE)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-anon-public-key-here
SUPABASE_BUCKET_NAME=memic-documents

# Redis & Celery (defaults work for local)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Optional (for Phase 2)
OPENAI_API_KEY=
PINECONE_API_KEY=
```

## Step 4: Install Redis

Redis is needed for Celery (background tasks).

### macOS
```bash
brew install redis
brew services start redis
```

### Ubuntu/Debian
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### Verify Redis
```bash
redis-cli ping
# Should return: PONG
```

## Step 5: Start Services

You need **3 terminal windows**:

### Terminal 1: Celery Worker
```bash
cd /Users/punithg/HaruLabs/memic-backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info --pool=solo
```

Note: Use `--pool=solo` on macOS to avoid forking issues.

### Terminal 2: FastAPI Server
```bash
cd /Users/punithg/HaruLabs/memic-backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 3: Test Commands (later)
Use this for API testing.

## Step 6: Test End-to-End

### Option A: Using Postman (Recommended)

1. **Open Postman**
2. **Import Collection**: `memic-backend.postman_collection.json`
3. **Run in sequence**:

```
1. Health Check → Verify API is running
2. Signup → Creates user
3. Login → Gets access token (auto-saved)
4. Create Organization → Creates org (auto-saves org_id)
5. Create Project → Creates project (auto-saves project_id)
6. Upload File → Uploads a test PDF/file (auto-saves file_id)
7. Get File Status → Watch it process through stages
8. List Files → See all uploaded files
```

### Option B: Using cURL

#### 1. Health Check
```bash
curl http://localhost:8000/api/v1/health
```

#### 2. Signup
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@memic.ai",
    "password": "Test123456",
    "name": "Test User"
  }'
```

#### 3. Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@memic.ai",
    "password": "Test123456"
  }'
```
Save the `access_token` from response.

#### 4. Create Organization
```bash
TOKEN="your_access_token_here"

curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test Organization"
  }'
```
Save the `id` as `ORG_ID`.

#### 5. Create Project
```bash
ORG_ID="your_org_id_here"

curl -X POST http://localhost:8000/api/v1/organizations/$ORG_ID/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test Project"
  }'
```
Save the `id` as `PROJECT_ID`.

#### 6. Upload File
```bash
PROJECT_ID="your_project_id_here"

curl -X POST http://localhost:8000/api/v1/projects/$PROJECT_ID/files \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/test.pdf"
```
Save the `id` as `FILE_ID`.

#### 7. Check File Status
```bash
FILE_ID="your_file_id_here"

curl -X GET "http://localhost:8000/api/v1/projects/$PROJECT_ID/files/$FILE_ID/status" \
  -H "Authorization: Bearer $TOKEN"
```

Run this multiple times to watch the status change!

## Step 7: What to Expect

### File Processing Flow (Phase 1 Simulation)

1. **Upload** → File saved to Supabase Storage
2. **Status: UPLOADING → UPLOADED**
3. **Celery pipeline triggers automatically**
4. **Processing stages** (each ~2 seconds):
   ```
   CONVERSION_STARTED → CONVERSION_COMPLETE
   PARSING_STARTED → PARSING_COMPLETE  
   CHUNKING_STARTED → CHUNKING_COMPLETE (creates 3 dummy chunks)
   EMBEDDING_STARTED → EMBEDDING_COMPLETE
   READY ✓
   ```

### Verify in Supabase Dashboard

1. Go to your Supabase project
2. Click **Storage** in sidebar
3. You should see `memic-documents` bucket
4. Browse folders: `org_id/project_id/file_id/raw/your-file.pdf`

### Check Database

```bash
psql -U punithg -d memic_dev
```

```sql
-- See all files
SELECT id, name, status, total_chunks 
FROM files 
ORDER BY created_at DESC;

-- See chunks for a file
SELECT chunk_index, chunk_text, token_count 
FROM file_chunks 
WHERE file_id = 'YOUR_FILE_ID';

-- See full processing timeline
SELECT 
  name,
  status,
  parsing_completed_at - parsing_started_at as parse_time,
  chunking_completed_at - chunking_started_at as chunk_time,
  embedding_completed_at - embedding_started_at as embed_time
FROM files 
WHERE id = 'YOUR_FILE_ID';
```

## Step 8: Monitor Logs

### Celery Worker Logs
Watch for:
```
[INFO] [STUB] Starting conversion for file...
[INFO] [STUB] Conversion simulation complete
[INFO] [STUB] Starting parsing for file...
[INFO] [STUB] File <id> is now READY for retrieval
```

### FastAPI Logs
Watch for:
```
INFO: POST /api/v1/projects/.../files 201 Created
INFO: Using Supabase Storage
INFO: Uploaded file to Supabase: org_id/project_id/...
INFO: Triggering RAG pipeline for file...
```

## Troubleshooting

### Redis Connection Error
```
Error 61: Connection refused
```
**Fix**: Start Redis
```bash
redis-server
```

### Supabase Connection Error
```
ValueError: Supabase URL and Key not configured
```
**Fix**: Check your `.env` file has:
- `SUPABASE_URL=https://....supabase.co`
- `SUPABASE_KEY=eyJ...` (long JWT token)

### Bucket Permission Error
```
Error: Bucket not found or insufficient permissions
```
**Fix**: 
1. Go to Supabase Dashboard → Storage
2. Bucket `memic-documents` should auto-create
3. If not, create it manually with "Private" access

### File Upload 500 Error
Check:
1. Supabase credentials are correct
2. Celery worker is running
3. Redis is running
4. Check Celery worker logs for errors

## Success Checklist

✅ Supabase project created  
✅ Credentials in `.env` file  
✅ Dependencies installed (`pip install -r requirements.txt`)  
✅ Redis running  
✅ Celery worker running (Terminal 1)  
✅ FastAPI server running (Terminal 2)  
✅ Health endpoint returns 200  
✅ User signup/login works  
✅ Organization & Project created  
✅ File uploads successfully  
✅ File appears in Supabase Storage  
✅ File status progresses: UPLOADED → ... → READY  
✅ 3 chunks created in database  
✅ API endpoints all working  

## Next Steps

Once everything works:
1. ✅ **Phase 1 Complete** - Infrastructure is solid!
2. 🚀 **Phase 2** - Replace dummy tasks with real RAG logic:
   - Port file conversion from `rag-file-conversion/`
   - Port parsing from `rag-parsing/`
   - Port chunking from `rag-chunking/`
   - Port embedding from `rag-embedding/`

## API Documentation

Visit these URLs while server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Cost & Limits

Supabase Free Tier includes:
- ✅ 500 MB database storage
- ✅ 1 GB file storage
- ✅ 50 MB file upload limit
- ✅ 2 GB bandwidth
- ✅ Unlimited API requests

Perfect for development and testing!

## Questions?

Common questions:

**Q: Do I need a credit card?**  
A: No! Supabase free tier doesn't require one.

**Q: Can I use this in production?**  
A: For MVP/small scale, yes. For production scale, upgrade to Pro ($25/month).

**Q: What if I want to switch to Azure later?**  
A: Easy! Just set Azure credentials in `.env`. The abstraction layer handles it automatically.

**Q: Files not showing in Supabase?**  
A: Check bucket permissions. Make sure you're looking at the right project.

Happy testing! 🚀

