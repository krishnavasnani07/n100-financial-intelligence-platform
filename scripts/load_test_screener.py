import time
import requests
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = "/api/v1/screener"
PARAMS = {"min_roe": "15"}
CONCURRENCY = 10

def make_request(req_id):
    url = f"{BASE_URL}{ENDPOINT}"
    start = time.perf_counter()
    status_code = None
    success = False
    try:
        res = requests.get(url, params=PARAMS, timeout=5)
        status_code = res.status_code
        success = (status_code == 200)
    except Exception as e:
        status_code = f"Error: {str(e)}"
        success = False
    duration = time.perf_counter() - start
    return {
        "id": req_id,
        "status_code": status_code,
        "duration": duration,
        "success": success
    }

def run_load_test():
    # Warm up first
    print("Running baseline request...")
    try:
        res = requests.get(f"{BASE_URL}{ENDPOINT}", params=PARAMS, timeout=5)
        print(f"Baseline: HTTP {res.status_code} | {len(res.json())} companies found | Time: {res.elapsed.total_seconds():.3f}s")
    except Exception as e:
        print(f"ERROR: Cannot connect to FastAPI server at {BASE_URL}. Is it running?")
        print(e)
        return False

    print(f"\nLaunching {CONCURRENCY} concurrent requests...")
    batch_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [executor.submit(make_request, i) for i in range(1, CONCURRENCY + 1)]
        results = [f.result() for f in futures]
    batch_duration = time.perf_counter() - batch_start

    print("\n--- Detailed Results ---")
    success_count = 0
    durations = []
    for r in results:
        durations.append(r["duration"])
        if r["success"]:
            success_count += 1
        print(f"Req {r['id']}: Status={r['status_code']}, Time={r['duration']:.3f}s, Success={r['success']}")

    min_t = min(durations)
    max_t = max(durations)
    avg_t = sum(durations) / len(durations)

    print("\n--- Summary ---")
    print(f"Concurrent requests: {CONCURRENCY}")
    print(f"Successful requests: {success_count}")
    print(f"Failed requests: {CONCURRENCY - success_count}")
    print(f"Total batch execution time: {batch_duration:.3f}s")
    print(f"Average response time: {avg_t:.3f}s")
    print(f"Minimum response time: {min_t:.3f}s")
    print(f"Maximum response time: {max_t:.3f}s")

    # Assertions
    assert success_count == CONCURRENCY, f"Expected {CONCURRENCY} successful requests, got {success_count}"
    assert batch_duration < 10.0, f"Batch execution took too long: {batch_duration:.3f}s (target < 10s)"
    print("\nResult: PASS")
    return True

if __name__ == "__main__":
    run_load_test()
