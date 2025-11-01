#!/usr/bin/env python
"""
Check Celery Workers Status

Verifies:
1. Celery workers are running
2. Workers are registered and active
3. Workers are listening to correct queues
4. Redis connection is working
"""
import subprocess
import sys
from celery import Celery
from app.config import settings

def check_celery_processes():
    """Check if Celery worker processes are running"""
    print("\n" + "="*80)
    print("  CHECKING CELERY PROCESSES")
    print("="*80)

    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True
    )

    celery_processes = [
        line for line in result.stdout.split('\n')
        if 'celery' in line.lower() and 'worker' in line and 'grep' not in line
    ]

    if celery_processes:
        print(f"\n✓ Found {len(celery_processes)} Celery worker process(es)")
        for i, process in enumerate(celery_processes[:3], 1):  # Show first 3
            # Extract relevant parts
            parts = process.split()
            if len(parts) > 10:
                pid = parts[1]
                print(f"  Process {i}: PID {pid}")
        if len(celery_processes) > 3:
            print(f"  ... and {len(celery_processes) - 3} more")
    else:
        print("\n✗ No Celery worker processes found!")
        print("\nTo start Celery workers:")
        print("  celery -A app.celery_app worker --loglevel=info -Q files,conversion,parsing,chunking,embedding,celery")
        return False

    return True


def check_celery_inspect():
    """Check Celery workers using inspect"""
    print("\n" + "="*80)
    print("  INSPECTING CELERY WORKERS")
    print("="*80)

    try:
        # Create Celery app instance
        celery_app = Celery(
            'memic',
            broker=settings.celery_broker_url,
            backend=settings.celery_result_backend
        )

        # Get inspector
        inspect = celery_app.control.inspect()

        # Check active workers
        print("\n1. Checking active workers...")
        active_workers = inspect.active()

        if not active_workers:
            print("✗ No active workers found!")
            print("\nPossible issues:")
            print("  - Celery workers not started")
            print("  - Redis connection issue")
            print("  - Worker crashed")
            return False

        print(f"✓ Found {len(active_workers)} active worker(s):")
        for worker_name in active_workers.keys():
            print(f"  - {worker_name}")

        # Check registered tasks
        print("\n2. Checking registered tasks...")
        registered = inspect.registered()

        if registered:
            for worker_name, tasks in registered.items():
                print(f"\n  Worker: {worker_name}")
                relevant_tasks = [
                    t for t in tasks
                    if 'conversion' in t or 'parsing' in t or 'file' in t
                ]
                if relevant_tasks:
                    print(f"  Registered tasks ({len(relevant_tasks)} relevant):")
                    for task in relevant_tasks[:5]:
                        print(f"    - {task}")
                    if len(relevant_tasks) > 5:
                        print(f"    ... and {len(relevant_tasks) - 5} more")
        else:
            print("⚠ No registered tasks found")

        # Check stats
        print("\n3. Checking worker statistics...")
        stats = inspect.stats()

        if stats:
            for worker_name, worker_stats in stats.items():
                print(f"\n  Worker: {worker_name}")
                print(f"    Total tasks: {worker_stats.get('total', {})}")
                print(f"    Pool: {worker_stats.get('pool', {}).get('implementation', 'unknown')}")

        # Check queues
        print("\n4. Checking active queues...")
        active_queues = inspect.active_queues()

        expected_queues = ['files', 'conversion', 'parsing', 'chunking', 'embedding', 'celery']

        if active_queues:
            for worker_name, queues in active_queues.items():
                queue_names = [q['name'] for q in queues]
                print(f"\n  Worker: {worker_name}")
                print(f"  Listening to queues: {', '.join(queue_names)}")

                # Check if all expected queues are covered
                missing_queues = set(expected_queues) - set(queue_names)
                if missing_queues:
                    print(f"  ⚠ Missing queues: {', '.join(missing_queues)}")
                else:
                    print(f"  ✓ All expected queues covered")
        else:
            print("✗ No active queues found")

        return True

    except Exception as e:
        print(f"\n✗ Failed to inspect Celery workers: {e}")
        print("\nPossible issues:")
        print("  - Redis not running")
        print("  - Incorrect Redis URL in configuration")
        print("  - Network connectivity issue")
        return False


def check_redis_connection():
    """Check Redis connection"""
    print("\n" + "="*80)
    print("  CHECKING REDIS CONNECTION")
    print("="*80)

    try:
        import redis
        from urllib.parse import urlparse

        # Parse Redis URL
        parsed = urlparse(settings.celery_broker_url)
        redis_host = parsed.hostname or 'localhost'
        redis_port = parsed.port or 6379
        redis_db = int(parsed.path.strip('/') or 0)

        print(f"\nConnecting to Redis:")
        print(f"  Host: {redis_host}")
        print(f"  Port: {redis_port}")
        print(f"  DB: {redis_db}")

        # Try to connect
        r = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        r.ping()

        print("\n✓ Redis connection successful")

        # Get some stats
        info = r.info()
        print(f"\nRedis Info:")
        print(f"  Version: {info.get('redis_version', 'unknown')}")
        print(f"  Connected clients: {info.get('connected_clients', 0)}")
        print(f"  Used memory: {info.get('used_memory_human', 'unknown')}")

        return True

    except Exception as e:
        print(f"\n✗ Redis connection failed: {e}")
        print("\nTo start Redis:")
        print("  redis-server")
        return False


def main():
    print("\n" + "="*80)
    print("  CELERY WORKERS HEALTH CHECK")
    print("="*80)

    checks = {
        "Redis Connection": check_redis_connection(),
        "Celery Processes": check_celery_processes(),
        "Celery Workers": check_celery_inspect()
    }

    print("\n" + "="*80)
    print("  HEALTH CHECK SUMMARY")
    print("="*80)

    all_passed = True
    for check_name, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {check_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "="*80)

    if all_passed:
        print("  ✓ ALL CHECKS PASSED - READY TO TEST PIPELINE")
        print("="*80)
        print("\nYou can now run:")
        print("  python test_pipeline_comprehensive.py")
        return 0
    else:
        print("  ✗ SOME CHECKS FAILED - FIX ISSUES BEFORE TESTING")
        print("="*80)
        print("\nPlease fix the issues above before running pipeline tests.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
