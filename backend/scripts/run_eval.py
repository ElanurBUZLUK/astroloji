"""CLI to run evaluation test suite."""
import argparse
import asyncio

from app.evaluation.test_suite import TestSuite
from app.pipelines.rag_pipeline import RAGAnswerPipeline


async def run(test_ids, list_only: bool) -> None:
    suite = TestSuite()
    if list_only:
        for case in suite.test_cases:
            print(f"{case.id}: {case.name} [{case.category}] - {case.description}")
        return

    pipeline = RAGAnswerPipeline()
    selected = [case for case in suite.test_cases if not test_ids or case.id in test_ids]
    for case in selected:
        result = await suite.run_test_case(case, pipeline)
        print(f"[{result.status.value.upper()}] {case.id} score={result.score:.2f} time={result.execution_time:.2f}s")
        if result.error_message:
            print(f"    error: {result.error_message}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run evaluation test suite.")
    parser.add_argument("test_ids", nargs="*", help="Optional test case IDs to run")
    parser.add_argument("--list", action="store_true", help="List available tests")
    args = parser.parse_args()
    asyncio.run(run(args.test_ids, args.list))


if __name__ == "__main__":
    main()
