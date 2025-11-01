#!/usr/bin/env python
"""
Quick parsing test - uploads a small PDF and monitors it
"""
import httpx
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
EMAIL = "punith@memic.ai"
PASSWORD = "12345678"

def main():
    print("\n" + "="*80)
    print("  QUICK PARSING TEST")
    print("="*80)

    client = httpx.Client(timeout=30.0)

    # Step 1: Auth
    print("\n1. Authenticating...")
    response = client.post(f"{BASE_URL}/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    if response.status_code != 200:
        print(f"✗ Auth failed: {response.status_code}")
        return
    token = response.json()["access_token"]
    print("✓ Authenticated")

    # Step 2: Get org and project
    print("\n2. Getting organization and project...")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"{BASE_URL}/api/v1/organizations/", headers=headers)
    org_id = str(response.json()[0]["id"])

    response = client.get(f"{BASE_URL}/api/v1/organizations/{org_id}/projects/", headers=headers)
    project_id = str(response.json()[0]["id"])

    print(f"✓ Org: {org_id[:8]}...")
    print(f"✓ Project: {project_id[:8]}...")

    # Step 3: Upload file
    print("\n3. Uploading PDF file...")
    file_path = Path("test_data/pdf/sample2.pdf")

    headers = {"Authorization": f"Bearer {token}", "X-Org-ID": org_id}

    # Initialize
    response = client.post(
        f"{BASE_URL}/api/v1/projects/{project_id}/files/init",
        json={"filename": file_path.name, "size": file_path.stat().st_size, "mime_type": "application/pdf"},
        headers=headers
    )
    data = response.json()
    file_id = data["file_id"]
    presigned_url = data["upload_url"]
    print(f"✓ Initialized: {file_id[:8]}...")

    # Upload to blob
    with open(file_path, 'rb') as f:
        client.put(presigned_url, content=f.read(), headers={"x-ms-blob-type": "BlockBlob", "Content-Type": "application/pdf"})
    print("✓ Uploaded to blob")

    # Confirm
    client.post(f"{BASE_URL}/api/v1/projects/{project_id}/files/{file_id}/confirm", headers=headers)
    print("✓ Pipeline triggered")

    # Step 4: Monitor
    print("\n4. Monitoring progress...")
    print("   Waiting for status transitions...")
    print("   Expected: uploaded → conversion_complete → parsing_started → parsing_complete")
    print()

    start = time.time()
    last_status = None

    while time.time() - start < 120:  # 2 min timeout
        response = client.get(f"{BASE_URL}/api/v1/projects/{project_id}/files/{file_id}", headers=headers)
        data = response.json()
        status = data.get("status")

        if status != last_status:
            elapsed = time.time() - start
            print(f"   [{elapsed:5.1f}s] {status}")
            last_status = status

        if status in ["completed", "parsing_complete", "parsing_completed"]:
            print(f"\n✓ SUCCESS! Parsing completed in {elapsed:.1f}s")
            print(f"\nFile details:")
            print(f"  Status: {status}")
            if data.get("enriched_file_path"):
                print(f"  Enriched JSON: {data['enriched_file_path']}")
            print("\n" + "="*80)
            print("  ✓ PARSING PIPELINE WORKING!")
            print("="*80)
            return True

        if status in ["failed", "parsing_failed", "conversion_failed"]:
            error = data.get("error_message", "Unknown error")
            print(f"\n✗ FAILED: {error}")
            print("\n" + "="*80)
            print("  ✗ TEST FAILED")
            print("="*80)
            return False

        time.sleep(2)

    print(f"\n✗ TIMEOUT: Still at status '{last_status}' after 120s")
    print("\nThis likely means:")
    print("  - Celery worker still has old code cached")
    print("  - Try: ./restart_celery.sh")
    print("\n" + "="*80)
    print("  ✗ TEST TIMED OUT")
    print("="*80)
    return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
