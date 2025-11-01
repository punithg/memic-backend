#!/usr/bin/env python
"""
Comprehensive Pipeline Test - Tests conversion and parsing with Celery workers

Tests multiple file types to verify:
1. Files that need conversion (DOC, DOCX, PPT, XLS, images)
2. Files that skip conversion (PDF, XLSX, PPTX)
3. Celery workers process tasks correctly
4. Complete pipeline: upload → conversion → parsing → enriched JSON
"""
import httpx
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

BASE_URL = "http://localhost:8000"
EMAIL = "punith@memic.ai"
PASSWORD = "12345678"

# Test files configuration
TEST_FILES = [
    # Files that SKIP conversion
    {
        "path": "test_data/pdf/sample2.pdf",
        "name": "PDF (skip conversion)",
        "mime_type": "application/pdf",
        "should_convert": False,
        "expected_parser": "PDFParser"
    },
    {
        "path": "test_data/office/file_example_XLSX_5000.xlsx",
        "name": "Excel XLSX (skip conversion)",
        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "should_convert": False,
        "expected_parser": "ExcelParser"
    },

    # Files that NEED conversion
    {
        "path": "test_data/office/sample.docx",
        "name": "Word DOCX (convert to PDF)",
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "should_convert": True,
        "expected_parser": "PDFParser"  # After conversion to PDF
    },
    {
        "path": "test_data/office/file_example_PPT_1MB.ppt",
        "name": "PowerPoint PPT (convert to PDF)",
        "mime_type": "application/vnd.ms-powerpoint",
        "should_convert": True,
        "expected_parser": "PDFParser"  # After conversion to PDF
    },
    {
        "path": "test_data/images/file_example_JPG_2500kB.jpg",
        "name": "JPG Image (convert to PDF)",
        "mime_type": "image/jpeg",
        "should_convert": True,
        "expected_parser": "PDFParser"  # After conversion to PDF
    },
]


class PipelineTest:
    def __init__(self):
        self.client = httpx.Client(timeout=60.0)
        self.token = None
        self.org_id = None
        self.project_id = None
        self.results = []

    def authenticate(self):
        """Authenticate and get token"""
        print("\n" + "="*80)
        print("  AUTHENTICATION")
        print("="*80)

        response = self.client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": EMAIL, "password": PASSWORD}
        )

        if response.status_code != 200:
            raise Exception(f"Auth failed: {response.status_code}")

        self.token = response.json()["access_token"]
        print("✓ Authenticated successfully")

    def get_organization_and_project(self):
        """Get organization and project IDs"""
        print("\n" + "="*80)
        print("  ORGANIZATION & PROJECT SETUP")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        # Get organization
        response = self.client.get(f"{BASE_URL}/api/v1/organizations/", headers=headers)
        self.org_id = str(response.json()[0]["id"])
        print(f"✓ Organization ID: {self.org_id[:8]}...")

        # Get project
        response = self.client.get(
            f"{BASE_URL}/api/v1/organizations/{self.org_id}/projects/",
            headers=headers
        )
        self.project_id = str(response.json()[0]["id"])
        print(f"✓ Project ID: {self.project_id[:8]}...")

    def test_file(self, test_config: Dict) -> Dict:
        """Test a single file through the pipeline"""
        file_path = Path(test_config["path"])

        if not file_path.exists():
            return {
                "name": test_config["name"],
                "status": "SKIPPED",
                "reason": f"File not found: {file_path}"
            }

        print("\n" + "="*80)
        print(f"  TESTING: {test_config['name']}")
        print("="*80)
        print(f"  File: {file_path}")
        print(f"  Size: {file_path.stat().st_size:,} bytes")
        print(f"  Should convert: {test_config['should_convert']}")
        print(f"  Expected parser: {test_config['expected_parser']}")

        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Org-ID": self.org_id
        }

        # Step 1: Initialize upload
        print("\n1. Initializing upload...")
        response = self.client.post(
            f"{BASE_URL}/api/v1/projects/{self.project_id}/files/init",
            json={
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "mime_type": test_config["mime_type"]
            },
            headers=headers
        )

        if response.status_code not in [200, 201]:
            return {
                "name": test_config["name"],
                "status": "FAILED",
                "reason": f"Init failed: {response.status_code}",
                "details": response.text
            }

        data = response.json()
        file_id = data["file_id"]
        presigned_url = data["upload_url"]
        print(f"✓ Initialized: {file_id[:8]}...")

        # Step 2: Upload to blob
        print("2. Uploading to Azure Blob Storage...")
        with open(file_path, 'rb') as f:
            upload_response = self.client.put(
                presigned_url,
                content=f.read(),
                headers={
                    "x-ms-blob-type": "BlockBlob",
                    "Content-Type": test_config["mime_type"]
                }
            )

        if upload_response.status_code not in [200, 201]:
            return {
                "name": test_config["name"],
                "status": "FAILED",
                "reason": f"Upload failed: {upload_response.status_code}"
            }

        print("✓ Uploaded to blob storage")

        # Step 3: Confirm and trigger pipeline
        print("3. Triggering pipeline...")
        self.client.post(
            f"{BASE_URL}/api/v1/projects/{self.project_id}/files/{file_id}/confirm",
            headers=headers
        )
        print("✓ Pipeline triggered")

        # Step 4: Monitor pipeline
        print("\n4. Monitoring pipeline progress...")
        print("   Expected flow:")
        if test_config["should_convert"]:
            print("   uploaded → conversion_started → conversion_complete → parsing_started → parsing_complete")
        else:
            print("   uploaded → conversion_complete (skipped) → parsing_started → parsing_complete")
        print()

        result = self.monitor_pipeline(file_id, test_config, headers)

        return result

    def monitor_pipeline(self, file_id: str, test_config: Dict, headers: Dict) -> Dict:
        """Monitor pipeline progress and verify each stage"""
        start_time = time.time()
        last_status = None
        statuses_seen = []

        timeout = 180  # 3 minutes

        while time.time() - start_time < timeout:
            response = self.client.get(
                f"{BASE_URL}/api/v1/projects/{self.project_id}/files/{file_id}",
                headers=headers
            )

            if response.status_code != 200:
                return {
                    "name": test_config["name"],
                    "status": "FAILED",
                    "reason": f"Status check failed: {response.status_code}"
                }

            data = response.json()
            status = data.get("status")

            if status != last_status:
                elapsed = time.time() - start_time
                print(f"   [{elapsed:5.1f}s] {status}")
                statuses_seen.append(status)
                last_status = status

            # Check for completion
            if status in ["completed", "parsing_complete", "parsing_completed", "chunking_started"]:
                elapsed = time.time() - start_time

                # Verify conversion happened as expected
                is_converted = data.get("is_converted", False)
                enriched_path = data.get("enriched_file_path")

                print(f"\n✓ Pipeline completed in {elapsed:.1f}s")
                print(f"\n  Final State:")
                print(f"    Status: {status}")
                print(f"    Converted: {is_converted}")
                print(f"    Enriched JSON: {enriched_path}")

                # Verify conversion expectations
                conversion_ok = True
                conversion_msg = ""

                if test_config["should_convert"] and not is_converted:
                    conversion_ok = False
                    conversion_msg = "Expected conversion but file was not converted"
                elif not test_config["should_convert"] and is_converted:
                    conversion_ok = False
                    conversion_msg = "Expected no conversion but file was converted"

                if not conversion_ok:
                    return {
                        "name": test_config["name"],
                        "status": "FAILED",
                        "reason": conversion_msg,
                        "time": elapsed,
                        "statuses": statuses_seen,
                        "is_converted": is_converted,
                        "enriched_path": enriched_path
                    }

                # Verify enriched JSON was created
                if not enriched_path:
                    return {
                        "name": test_config["name"],
                        "status": "FAILED",
                        "reason": "No enriched JSON path",
                        "time": elapsed,
                        "statuses": statuses_seen
                    }

                return {
                    "name": test_config["name"],
                    "status": "SUCCESS",
                    "time": elapsed,
                    "statuses": statuses_seen,
                    "is_converted": is_converted,
                    "enriched_path": enriched_path,
                    "file_id": file_id
                }

            # Check for failures
            if status in ["failed", "parsing_failed", "conversion_failed"]:
                error = data.get("error_message", "Unknown error")
                return {
                    "name": test_config["name"],
                    "status": "FAILED",
                    "reason": f"Pipeline failed: {error}",
                    "failed_at": status,
                    "statuses": statuses_seen
                }

            time.sleep(2)

        # Timeout
        return {
            "name": test_config["name"],
            "status": "TIMEOUT",
            "reason": f"Pipeline did not complete in {timeout}s",
            "last_status": last_status,
            "statuses": statuses_seen
        }

    def verify_enriched_json(self, result: Dict) -> Dict:
        """Download and verify enriched JSON"""
        if result["status"] != "SUCCESS":
            return result

        print(f"\n5. Verifying enriched JSON for {result['name']}...")

        try:
            from app.core.storage import get_storage_client
            import asyncio

            storage_client = get_storage_client()

            async def download():
                return await storage_client.download_file(result["enriched_path"])

            enriched_content = asyncio.run(download())
            enriched_json = json.loads(enriched_content.decode('utf-8'))

            # Verify structure
            sections = enriched_json.get("sections", [])
            metadata = enriched_json.get("metadata", {})

            print(f"✓ Enriched JSON downloaded ({len(enriched_content)} bytes)")
            print(f"  Sections: {len(sections)}")
            print(f"  Parser: {metadata.get('parser', 'unknown')}")

            # Verify parser
            expected_parser = result.get("expected_parser")
            actual_parser = metadata.get("parser")

            if expected_parser and actual_parser != expected_parser:
                result["status"] = "FAILED"
                result["reason"] = f"Expected parser {expected_parser}, got {actual_parser}"
            else:
                result["sections_count"] = len(sections)
                result["parser"] = actual_parser

        except Exception as e:
            result["status"] = "FAILED"
            result["reason"] = f"Failed to verify enriched JSON: {str(e)}"

        return result

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("  TEST SUMMARY")
        print("="*80)

        success_count = sum(1 for r in self.results if r["status"] == "SUCCESS")
        failed_count = sum(1 for r in self.results if r["status"] == "FAILED")
        skipped_count = sum(1 for r in self.results if r["status"] == "SKIPPED")
        timeout_count = sum(1 for r in self.results if r["status"] == "TIMEOUT")

        print(f"\nTotal Tests: {len(self.results)}")
        print(f"  ✓ Success: {success_count}")
        print(f"  ✗ Failed: {failed_count}")
        print(f"  ⊘ Skipped: {skipped_count}")
        print(f"  ⧗ Timeout: {timeout_count}")

        print("\nDetailed Results:")
        print("-" * 80)

        for result in self.results:
            status_icon = {
                "SUCCESS": "✓",
                "FAILED": "✗",
                "SKIPPED": "⊘",
                "TIMEOUT": "⧗"
            }.get(result["status"], "?")

            print(f"\n{status_icon} {result['name']}")
            print(f"  Status: {result['status']}")

            if result["status"] == "SUCCESS":
                print(f"  Time: {result.get('time', 0):.1f}s")
                print(f"  Converted: {result.get('is_converted', 'N/A')}")
                print(f"  Parser: {result.get('parser', 'N/A')}")
                print(f"  Sections: {result.get('sections_count', 'N/A')}")
            elif result["status"] == "FAILED":
                print(f"  Reason: {result.get('reason', 'Unknown')}")
                if "failed_at" in result:
                    print(f"  Failed at: {result['failed_at']}")
            elif result["status"] == "TIMEOUT":
                print(f"  Reason: {result.get('reason', 'Unknown')}")
                print(f"  Last status: {result.get('last_status', 'Unknown')}")
            elif result["status"] == "SKIPPED":
                print(f"  Reason: {result.get('reason', 'Unknown')}")

        print("\n" + "="*80)
        if failed_count == 0 and timeout_count == 0 and success_count > 0:
            print("  ✓ ALL TESTS PASSED!")
        else:
            print("  ⚠ SOME TESTS FAILED OR TIMED OUT")
        print("="*80)

        # Save detailed results
        output_file = Path("test_results/pipeline_test_results.json")
        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✓ Detailed results saved to: {output_file}")

    def run(self):
        """Run all tests"""
        print("\n" + "="*80)
        print("  COMPREHENSIVE PIPELINE TEST")
        print("  Testing conversion and parsing with Celery workers")
        print("="*80)

        try:
            # Setup
            self.authenticate()
            self.get_organization_and_project()

            # Test each file
            for test_config in TEST_FILES:
                result = self.test_file(test_config)

                # Add expected parser to result for verification
                result["expected_parser"] = test_config.get("expected_parser")

                # Verify enriched JSON if successful
                if result["status"] == "SUCCESS":
                    result = self.verify_enriched_json(result)

                self.results.append(result)

                # Brief pause between tests
                time.sleep(2)

            # Print summary
            self.print_summary()

        except Exception as e:
            print(f"\n✗ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.client.close()


def main():
    test = PipelineTest()
    test.run()


if __name__ == "__main__":
    main()
