import time
import logging
from typing import List, Dict, Any
from statistics import mean
from dotenv import load_dotenv

load_dotenv()

from agent.planner import ResearchPlanner
from agent.context_manager import HybridContextEngine
from agent.verifier import VeriNewsVerifier
from agent.url_extractor import is_url, extract_article_from_url

# Configure minimal logging for clean CLI output
logging.basicConfig(level=logging.ERROR)


class PipelineBenchmarker:
    """Automated benchmarking suite for VeriNews AI pipeline telemetry and accuracy checks."""

    def __init__(self):
        self.planner = ResearchPlanner()
        self.context_engine = HybridContextEngine()
        self.verifier = VeriNewsVerifier()

    def run_single_test(self, test_id: int, input_text: str) -> Dict[str, Any]:
        print(f"\n{'='*70}")
        print(f"RUNNING BENCHMARK TEST {test_id}: {input_text[:60]}...")
        print(f"{'='*70}")

        metrics = {
            "test_id": test_id,
            "input_type": "URL" if is_url(input_text) else "Raw Text",
            "extract_time_sec": 0.0,
            "plan_time_sec": 0.0,
            "search_time_sec": 0.0,
            "context_time_sec": 0.0,
            "verify_time_sec": 0.0,
            "total_time_sec": 0.0,
            "queries_generated": 0,
            "truth_score": 0,
            "tier_1_sources": 0,
            "tier_2_sources": 0,
            "tier_3_sources": 0,
            "atomic_claims_count": 0,
            "status": "SUCCESS"
        }

        start_total = time.perf_counter()

        try:
            target_text = input_text
            # Phase 1: URL Extraction (if applicable)
            if is_url(input_text):
                t0 = time.perf_counter()
                meta = extract_article_from_url(input_text)
                metrics["extract_time_sec"] = round(time.perf_counter() - t0, 3)
                
                if not meta["success"]:
                    metrics["status"] = "EXTRACTION_FAILED"
                    return metrics
                
                target_text = f"TITLE: {meta['title']}\n\nBODY:\n{meta['content']}"
                print(f"[Phase 1] Scraped Article Title: {meta['title'][:50]}... ({metrics['extract_time_sec']}s)")

            # Phase 2: Planning & Sub-Query Formulation
            t0 = time.perf_counter()
            plan = self.planner.create_plan(target_text)
            metrics["plan_time_sec"] = round(time.perf_counter() - t0, 3)
            metrics["queries_generated"] = len(plan.sub_queries)
            print(f"[Phase 2] Generated {len(plan.sub_queries)} Sub-Queries ({metrics['plan_time_sec']}s)")

            # Phase 3: Multi-Engine Search Execution
            t0 = time.perf_counter()
            raw_results = self.planner.execute_plan(plan)
            metrics["search_time_sec"] = round(time.perf_counter() - t0, 3)
            print(f"[Phase 3] Executed SerpApi Search Calls ({metrics['search_time_sec']}s)")

            # Phase 4: Hybrid Context Preparation
            t0 = time.perf_counter()
            evidence = self.context_engine.prepare_evidence(raw_results)
            metrics["context_time_sec"] = round(time.perf_counter() - t0, 3)
            print(f"[Phase 4] Context Formatted (Total Word Count: {evidence.get('word_count', 0)}) ({metrics['context_time_sec']}s)")

            # Phase 5: Verification & Synthesis
            t0 = time.perf_counter()
            headline = input_text if not is_url(input_text) else meta["title"]
            report = self.verifier.verify_news(headline, evidence)
            metrics["verify_time_sec"] = round(time.perf_counter() - t0, 3)
            print(f"[Phase 5] Verification Complete ({metrics['verify_time_sec']}s)")

            # Record Output Metrics
            metrics["truth_score"] = report.overall_truth_score
            metrics["tier_1_sources"] = report.source_spectrum.tier_1_count
            metrics["tier_2_sources"] = report.source_spectrum.tier_2_count
            metrics["tier_3_sources"] = report.source_spectrum.tier_3_count
            metrics["atomic_claims_count"] = len(report.atomic_claims)

        except Exception as e:
            metrics["status"] = f"FAILED: {str(e)}"
            print(f"Error during benchmark run: {e}")

        metrics["total_time_sec"] = round(time.perf_counter() - start_total, 3)
        return metrics


def main():
    benchmarking_dataset = [
        "https://www.bbc.com/news/articles/cwyz9gjw9n9o",
        "Tesla announced immediate full production of solid-state battery electric vehicles in 2026.",
        "Sunscreen causes skin cancer and blocks all essential vitamin absorption."
    ]

    runner = PipelineBenchmarker()
    all_metrics: List[Dict[str, Any]] = []

    print("\nStarting VeriNews AI Automated Benchmark Suite...")
    print(f"Total Test Cases: {len(benchmarking_dataset)}")

    for idx, test_input in enumerate(benchmarking_dataset, start=1):
        res = runner.run_single_test(idx, test_input)
        all_metrics.append(res)
        if idx < len(benchmarking_dataset):
            print("\n[Pacing] Waiting 4 seconds before next test case...")
            time.sleep(4)

    # ------------------- AGGREGATE SUMMARY REPORT -------------------
    successful_runs = [m for m in all_metrics if m["status"] == "SUCCESS"]

    print("\n" + "="*80)
    print("VERINEWS AI — PIPELINE BENCHMARK TELEMETRY SUMMARY")
    print("="*80)

    print(f"\nExecution Overview:")
    print(f"  - Total Benchmark Runs:  {len(all_metrics)}")
    print(f"  - Successful Runs:       {len(successful_runs)}")
    print(f"  - Pipeline Success Rate: {(len(successful_runs)/len(all_metrics))*100:.1f}%")

    if successful_runs:
        avg_plan = mean([m["plan_time_sec"] for m in successful_runs])
        avg_search = mean([m["search_time_sec"] for m in successful_runs])
        avg_verify = mean([m["verify_time_sec"] for m in successful_runs])
        avg_total = mean([m["total_time_sec"] for m in successful_runs])
        avg_queries = mean([m["queries_generated"] for m in successful_runs])

        print(f"\nAverage Performance Latencies:")
        print(f"  - Research Planning Time:   {avg_plan:.3f} s")
        print(f"  - SerpApi Search Time:      {avg_search:.3f} s")
        print(f"  - Verification Engine Time: {avg_verify:.3f} s")
        print(f"  - End-to-End Latency:       {avg_total:.3f} s")

        print(f"\nData & Evidence Metrics:")
        print(f"  - Avg Sub-Queries / Run:    {avg_queries:.1f}")
        print(f"  - Total Tier 1 Sources:     {sum(m['tier_1_sources'] for m in successful_runs)}")
        print(f"  - Total Tier 2 Sources:     {sum(m['tier_2_sources'] for m in successful_runs)}")
        print(f"  - Total Tier 3 Sources:     {sum(m['tier_3_sources'] for m in successful_runs)}")
        print(f"  - Total Claims Analyzed:    {sum(m['atomic_claims_count'] for m in successful_runs)}")

    print("\nIndividual Test Case Breakdown:")
    print(f"{'ID':<4} | {'Type':<8} | {'Score':<6} | {'Claims':<6} | {'Queries':<7} | {'Total Time':<10} | {'Status'}")
    print("-" * 75)
    for m in all_metrics:
        print(
            f"{m['test_id']:<4} | {m['input_type']:<8} | {m['truth_score']:<6} | "
            f"{m['atomic_claims_count']:<6} | {m['queries_generated']:<7} | "
            f"{m['total_time_sec']:<10}s | {m['status']}"
        )
    print("="*80 + "\n")


if __name__ == "__main__":
    main()