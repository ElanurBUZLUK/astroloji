"""CLI helper to run the retrieval/groundedness benchmark suite."""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from statistics import mean
from typing import Iterable

from app.evaluation.benchmark_runner import (
    BenchmarkResult,
    load_benchmark_cases,
    run_benchmark_cases,
)


def _summarise(results: Iterable[BenchmarkResult]) -> dict[str, float]:
    """Aggregate metric averages for a benchmark run."""
    buckets: dict[str, list[float]] = {}
    for result in results:
        for key, value in result.metrics.items():
            if value is None:
                continue
            buckets.setdefault(key, []).append(float(value))
    return {key: mean(values) for key, values in buckets.items() if values}


async def _run(path: Path) -> None:
    cases = load_benchmark_cases(path)
    results = await run_benchmark_cases(cases)

    print(f"Loaded {len(cases)} benchmark cases from {path}.")
    for result in results:
        metrics_str = ", ".join(
            f"{metric}={value:.3f}" for metric, value in sorted(result.metrics.items()) if value is not None
        )
        print(f" - {result.case_id}: {metrics_str or 'no metrics recorded'}")

    summary = _summarise(results)
    if summary:
        print("\nAverages across cases:")
        for metric, value in sorted(summary.items()):
            print(f" * {metric}: {value:.3f}")
    else:
        print("\nNo metrics recorded.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RAG retrieval/groundedness benchmark suite")
    parser.add_argument(
        "benchmark_path",
        nargs="?",
        default=Path(__file__).parent / "datasets" / "rag_groundedness_benchmark.json",
        help="Path to the benchmark dataset JSON file",
    )
    args = parser.parse_args()

    path = Path(args.benchmark_path)
    if not path.exists():
        raise SystemExit(f"Benchmark file not found: {path}")

    asyncio.run(_run(path))


if __name__ == "__main__":
    main()
