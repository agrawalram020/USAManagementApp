import sys
import argparse
sys.stdout.reconfigure(encoding="utf-8")

from config import MISTRAL_API_KEY
from agents.orchestrator import run_revenue_analysis
from generate_report import generate_report


def main():
    parser = argparse.ArgumentParser(description="USA Revenue Agent — analysis pipeline")
    parser.add_argument(
        "--period",
        choices=["1y", "6m", "1m"],
        default="1y",
        help="Data window: 1y=last 12 months, 6m=last 6 months, 1m=last month (default: 1y)",
    )
    args = parser.parse_args()

    if not MISTRAL_API_KEY:
        print("Error: MISTRAL_API_KEY not set. Copy .env.example to .env and add your key.")
        sys.exit(1)

    run_revenue_analysis(period=args.period)
    print("\n[Generating HTML report...]", flush=True)
    generate_report()


if __name__ == "__main__":
    main()
