"""Command line helpers for evaluation tasks."""
from __future__ import annotations

import argparse
import asyncio
import json

from .test_suite import TestSuite
from app.pipelines.rag_pipeline import RAGAnswerPipeline
from app.evaluation.dashboard import snapshot


async def run_tests(test_ids: list[str]) -> list[dict]:
    suite = TestSuite()
    pipeline = RAGAnswerPipeline()
    selected = [case for case in suite.test_cases if not test_ids or case.id in test_ids]
    results = []
    for case in selected:
        result = await suite.run_test_case(case, pipeline)
        results.append(result)
    return [
        {
            "id": r.test_case_id,
            "status": r.status.value,
            "score": r.score,
            "execution_time": r.execution_time,
            "metrics": [m.model_dump() for m in r.metrics],
            "error": r.error_message,
        }
        for r in results
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluation CLI")
    parser.add_argument("command", choices=["run", "snapshot"], help="Command to execute")
    parser.add_argument("ids", nargs="*", help="Test IDs when running eval")
    parser.add_argument("--window", type=int, default=60, help="Dashboard window in minutes")
    args = parser.parse_args()

    if args.command == "snapshot":
        data = snapshot(args.window)
        print(json.dumps(data, indent=2))
    else:
        results = asyncio.run(run_tests(args.ids))
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
