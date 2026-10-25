"""Command-line interface (CLI) for running tool description optimization."""

import argparse
from pathlib import Path
import sys

from backend.app.core.constants import MAX_OPTIMIZATION_ROUNDS
from backend.app.core.exceptions import AppBaseException
from backend.app.core.logging import logger
from backend.app.services.optimizer_service import optimizer_service

def parse_args():
    """Parses command-line arguments for description optimization runs."""
    parser = argparse.ArgumentParser(
        description="Iteratively optimize tool descriptions using tuning mistakes with strict guardrails."
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=MAX_OPTIMIZATION_ROUNDS,
        help=f"Maximum optimization rounds to execute (default: {MAX_OPTIMIZATION_ROUNDS}).",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of evaluation passes per query during candidate testing (default: 1).",
    )
    parser.add_argument(
        "--no-cache",
        "--force-refresh",
        dest="force_refresh",
        action="store_true",
        help="Bypass disk cache during candidate evaluation.",
    )
    parser.add_argument(
        "--baseline-file",
        type=str,
        default=None,
        help="Path to existing baseline evaluation artifact (default: results/evaluation_tuning_latest.json).",
    )
    return parser.parse_args()

def main():
    """Main execution function for optimization CLI."""
    args = parse_args()
    logger.info(
        "Starting description optimization: max_rounds=%d, runs=%d, force_refresh=%s",
        args.max_rounds,
        args.runs,
        args.force_refresh,
    )

    try:
        optimizer_service.run_optimization_loop(
            max_rounds=args.max_rounds,
            runs_per_query=args.runs,
            force_refresh=args.force_refresh,
            baseline_file=args.baseline_file,
        )
    except AppBaseException as exc:
        print(f"\n[ERROR] Optimization failed: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] Unexpected error during optimization: {exc}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
