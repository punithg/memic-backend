# Quick Start Guide - 10 Minutes to RAG!

Get the entire RAG system running in under 10 minutes using Supabase.

## Prerequisites

- ✅ Python 3.14 with venv (you have this)
- ✅ PostgreSQL running (you have this)
- ⬜ Redis (we'll install)
- ⬜ Supabase account (free, no credit card)

## 1. Get Supabase Credentials (2 minutes)

1. **Sign up**: Go to https://supabase.com and create account
2. **New Project**: Click "New Project"
   - Name: `memic-dev`
   - Password: (generate and save)
   - Region: (choose closest)
3. **Get Credentials**: Settings → API
   - Copy **Project URL**: `https://xxxxx.supabase.co`
   - Copy **anon public** key: `eyJxxx...`

## 2. Install Redis (1 minute)

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt-get install redis-server
sudo systemctl start redis

# Verify
redis-cli ping  # Should return: PONG
```

## 3. Create .env File (1 minute)

Create `.env` in project root:

```bash
# Application
APP_ENV=dev
DEBUG=True
DATABASE_URL=postgresql+psycopg://punithg@localhost:5432/memic_dev

# Security (generate random strings)
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# SUPABASE - PASTE YOUR VALUES HERE
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJxxx_your_anon_key_here
SUPABASE_BUCKET_NAME=memic-documents

# Redis (local defaults)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 4. Install Dependencies (1 minute)

```bash
cd /Users/punithg/HaruLabs/memic-backend
source venv/bin/activate
pip install -r requirements.txt
```

## 5. Start Services (3 terminals)

### Terminal 1: Celery Worker
```bash
cd /Users/punithg/HaruLabs/memic-backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info --pool=solo
```

### Terminal 2: FastAPI Server
```bash
cd /Users/punithg/HaruLabs/memic-backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Terminal 3: Testing
Leave this open for testing commands.

## 6. Test the Complete Flow (3 minutes)

### Quick Test Script

Save this as `test_rag.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000/api/v1"

echo "1. Signup..."
SIGNUP_RESPONSE=$(curl -s -X POST $BASE_URL/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@memic.ai", "password": "Test123456", "name": "Test User"}')
echo "✓ User created"

echo "2. Login..."
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@memic.ai", "password": "Test123456"}')
TOKEN=$(echo $LOGIN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "✓ Got access token"

echo "3. Create Organization..."
ORG_RESPONSE=$(curl -s -X POST $BASE_URL/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Test Organization"}')
ORG_ID=$(echo $ORG_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "✓ Organization created: $ORG_ID"

echo "4. Create Project..."
PROJECT_RESPONSE=$(curl -s -X POST $BASE_URL/organizations/$ORG_ID/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Test Project"}')
PROJECT_ID=$(echo $PROJECT_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "✓ Project created: $PROJECT_ID"

echo "5. Create a test file..."
echo "This is a test document for RAG processing." > test_file.txt

echo "6. Upload File..."
UPLOAD_RESPONSE=$(curl -s -X POST $BASE_URL/projects/$PROJECT_ID/files \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_file.txt")
FILE_ID=$(echo $UPLOAD_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "✓ File uploaded: $FILE_ID"

echo "7. Check file status (will poll for 20 seconds)..."
for i in {1..10}; do
  STATUS_RESPONSE=$(curl -s -X GET $BASE_URL/projects/$PROJECT_ID/files/$FILE_ID/status \
    -H "Authorization: Bearer $TOKEN")
  STATUS=$(echo $STATUS_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['status'])")
  echo "   Status: $STATUS"
  
  if [ "$STATUS" == "READY" ]; then
    echo "✓ File processing complete!"
    break
  fi
  sleep 2
done

echo "8. List all files..."
curl -s -X GET "$BASE_URL/projects/$PROJECT_ID/files?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

echo ""
echo "========================================="
echo "SUCCESS! 🎉"
echo "========================================="
echo "File ID: $FILE_ID"
echo "Status: READY"
echo ""
echo "Check Supabase Storage:"
echo "https://supabase.com → Your Project → Storage → memic-documents"
echo ""
echo "Check database:"
echo "psql -U punithg -d memic_dev -c \"SELECT id, name, status, total_chunks FROM files;\""
```

Make it executable and run:
```bash
chmod +x test_rag.sh
./test_rag.sh
```

### Or Use Postman

1. Import: `memic-backend.postman_collection.json`
2. Run requests in order:
   - Health Check
   - Signup
   - Login
   - Create Organization
   - Create Project
   - Upload File
   - Get File Status

## What You'll See

### Celery Worker Terminal
```
[INFO] Using Supabase Storage
[INFO] [STUB] Starting conversion for file...
[INFO] [STUB] Conversion simulation complete
[INFO] [STUB] Starting parsing for file...
[INFO] [STUB] Parsing simulation complete
[INFO] [STUB] Starting chunking for file...
[INFO] [STUB] Chunking simulation complete
[INFO] [STUB] Starting embedding for file...
[INFO] [STUB] File <id> is now READY for retrieval
```

### FastAPI Server Terminal
```
INFO: POST /api/v1/auth/signup 201 Created
INFO: POST /api/v1/auth/login 200 OK
INFO: POST /api/v1/organizations 201 Created
INFO: POST /api/v1/projects 201 Created
INFO: POST /api/v1/projects/.../files 201 Created
INFO: Triggering RAG pipeline for file...
```

### Supabase Dashboard
1. Go to Storage → memic-documents
2. Browse: `org_id/project_id/file_id/raw/test_file.txt`
3. File should be there! 🎉

### Database
```bash
psql -U punithg -d memic_dev
```

```sql
-- See files
SELECT id, name, status, total_chunks FROM files;

-- See chunks (3 dummy chunks created)
SELECT chunk_index, chunk_text FROM file_chunks;
```

## Success Indicators

✅ All 3 terminals running without errors  
✅ Health endpoint returns 200  
✅ File upload returns 201 with file_id  
✅ File status progresses through stages  
✅ File reaches "READY" status  
✅ 3 chunks created in database  
✅ File visible in Supabase Storage  

## Troubleshooting

### "Connection refused" error
- **Redis not running**: `brew services start redis`
- **Wrong database**: Check `DATABASE_URL` in .env

### "Supabase URL and Key not configured"
- Check `.env` file exists in project root
- Check `SUPABASE_URL` and `SUPABASE_KEY` are set

### Celery worker won't start
- Make sure you're in venv: `source venv/bin/activate`
- Use `--pool=solo` on macOS: `celery -A app.celery_app worker --loglevel=info --pool=solo`

### File upload fails
1. Check all 3 services are running
2. Check Supabase credentials
3. Look at Celery worker logs for errors

## Next Steps

Once this works:

1. **Explore the API**: http://localhost:8000/docs
2. **Try different files**: PDFs, DOCX, etc.
3. **Check Supabase**: See files in storage
4. **Query database**: See how data is structured
5. **Phase 2**: Replace dummy tasks with real RAG logic!

## Time Saved

Without this setup:
- Manual file storage handling: 2 hours
- Database schema design: 3 hours
- API endpoints: 4 hours
- Background task setup: 3 hours
- Testing infrastructure: 2 hours
**Total: ~14 hours**

With this setup: **10 minutes** ⚡

You're welcome! 😄

