# LibreOffice Setup for File Conversion

## Issue

LibreOffice is installed but not in PATH:
```bash
# LibreOffice exists here:
/Applications/LibreOffice.app/Contents/MacOS/soffice

# But 'which soffice' fails because it's not in PATH
```

## Clean Solution: Add to PATH

### Option 1: Add to ~/.zshrc (Permanent)

```bash
# Add this line to ~/.zshrc
echo 'export PATH="/Applications/LibreOffice.app/Contents/MacOS:$PATH"' >> ~/.zshrc

# Reload shell
source ~/.zshrc

# Verify
which soffice
# Should output: /Applications/LibreOffice.app/Contents/MacOS/soffice
```

### Option 2: Add to current session (Temporary)

```bash
# For current terminal session only
export PATH="/Applications/LibreOffice.app/Contents/MacOS:$PATH"

# Verify
which soffice
```

### Option 3: Symlink to /usr/local/bin

```bash
# Create symlink (requires sudo)
sudo ln -s /Applications/LibreOffice.app/Contents/MacOS/soffice /usr/local/bin/soffice

# Verify
which soffice
# Should output: /usr/local/bin/soffice
```

## After Setup

Once soffice is in PATH, restart Celery workers:

```bash
# Kill existing workers
pkill -f "celery.*worker"

# Restart (they will pick up new PATH)
celery -A app.celery_app worker --loglevel=info -Q files,conversion,parsing,chunking,embedding,celery
```

## Verify

```bash
# Test conversion directly
soffice --headless --convert-to pdf test_data/office/sample.docx --outdir /tmp

# Should create /tmp/sample.pdf
ls -lh /tmp/sample.pdf
```

## Why This is Better Than Hardcoding

❌ **Hardcoding path in code:**
- Not portable (breaks on Linux, different macOS versions)
- Violates separation of concerns (app shouldn't know OS-specific paths)
- Difficult to override for different environments

✅ **PATH configuration:**
- Standard Unix approach
- Works across different systems
- Easy to override per environment
- Clean code - just use "soffice" command
