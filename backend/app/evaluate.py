"""Command-line interface (CLI) for running tool-selection evaluations."""

import argparse
from pathlib import Path
import sys

# Ensure repository root is on sys.path
_repo_root = str(Path(__file__).resolve().parent.parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from backend.app.core.exceptions import AppBaseException
from backend.app.core.logging import logger
from backend.app.services.evaluator_service import evaluator_service

def parse_args():
    """Parses command-line arguments for evaluation runs."""
    parser = argparse.ArgumentParser(
        description="Run deterministic tool-selection evaluation on tuning or held-out dataset splits."
    )
    parser.add_argument(
        "--split",
        type=str,
        default="tuning",
        choices=["tuning", "held-out", "held_out"],
        help="Dataset split to evaluate ('tuning' [35 queries] or 'held-out' [15 queries]). Default: tuning.",
    )
    parser.add_argument(
        "--tools-file",
        type=str,
        default=None,
        help="Optional path to custom tools JSON file or optimization record. If omitted, loads canonical tools/tools.json.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of inference passes per query for majority voting. Default: 1.",
    )
    parser.add_argument(
        "--no-cache",
        "--force-refresh",
        dest="force_refresh",
        action="store_true",
        help="Bypass disk cache and force fresh inference calls against Ollama.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional custom file path to save evaluation results JSON.",
    )
    return parser.parse_args()

def main():
    """Main execution function for evaluator CLI."""
    args = parse_args()
    logger.info(
        "Starting evaluation: split=%s, tools_file=%s, runs_per_query=%d, force_refresh=%s",
        args.split,
        args.tools_file,
        args.runs,
        args.force_refresh,
    )

    try:
        tools = None
        if args.tools_file:
            from backend.app.services.tool_service import load_tools_from_file
            tools = load_tools_from_file(args.tools_file)

        split = args.split.replace("_", "-")
        result = evaluator_service.evaluate(
            split=split,
            runs_per_query=args.runs,
            force_refresh=args.force_refresh,
            tools=tools,
        )
    except AppBaseException as exc:
        print(f"\n[ERROR] Evaluation failed: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] Unexpected error during evaluation: {exc}", file=sys.stderr)
        sys.exit(1)

    # Output formatted terminal summary
    summary = evaluator_service.format_terminal_summary(result)
    print("\n" + summary + "\n")

    if args.output:
        import json
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
        print(f"Results additionally saved to: {args.output}")

    sys.exit(0)

if __name__ == "__main__":
    main()
