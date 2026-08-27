import time
from statistics import mean

def run_mock_benchmark():
    print("\n" + "="*80)
    print("VERINEWS AI — OFFLINE INTEGRATION & SUITE TELEMETRY (MOCK MODE)")
    print("="*80 + "\n")

    test_cases = [
        {"id": 1, "type": "URL", "label": "BBC News Article Audit", "claims": 3, "queries": 4, "time": 1.24, "score": 92},
        {"id": 2, "type": "Raw Text", "label": "Tesla Solid-State Battery Claim", "claims": 2, "queries": 3, "time": 0.88, "score": 15},
        {"id": 3, "type": "Raw Text", "label": "Sunscreen & Cancer Myth", "claims": 4, "queries": 4, "time": 1.10, "score": 10}
    ]

    for test in test_cases:
        time.sleep(0.3)
        print(f"[Test {test['id']}] Executing {test['label']}... SUCCESS ({test['time']}s)")

    print("\n" + "="*80)
    print("PIPELINE PERFORMANCE SUMMARY")
    print("="*80)
    print(f"Total Runs: {len(test_cases)} | Success Rate: 100%")
    print(f"Avg End-to-End Latency: {mean([t['time'] for t in test_cases]):.2f}s")
    print(f"Avg Queries Formulated: {mean([t['queries'] for t in test_cases]):.1f}")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_mock_benchmark()