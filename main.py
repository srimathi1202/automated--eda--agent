"""
main.py
-------
CLI entry point for the Automated EDA Agent.

Usage examples:
  python main.py --input data/sample/sales_data.csv
  python main.py --input data/sample/sales_data.csv --email you@gmail.com --verbose
  python main.py --input data/sample/sales_data.csv --output outputs/my_report.html
"""

import argparse
import json
import sys
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(
        description="🤖 Automated EDA Agent — Explores any dataset and generates a dashboard"
    )
    p.add_argument("--input",  "-i", required=True, help="Path to input CSV or Excel file")
    p.add_argument("--output", "-o", default="",    help="Output path for the HTML dashboard")
    p.add_argument("--email",  "-e", default="",    help="Recipient email address for the report")
    p.add_argument("--email-method", choices=["smtp", "sendgrid"], default="smtp")
    p.add_argument("--verbose","-v", action="store_true", help="Enable verbose logging")
    return p.parse_args()


def main():
    args = parse_args()

    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"\n❌ File not found: {input_path}")
        sys.exit(1)

    # Build output path
    output_path = args.output or f"outputs/eda_{input_path.stem}.html"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Import here so config loads first
    from agents.orchestrator import OrchestratorAgent

    context = {
        "input_path":      str(input_path),
        "output_path":     output_path,
        "email_recipient": args.email,
        "email_method":    args.email_method,
        "verbose":         args.verbose,
    }

    orchestrator = OrchestratorAgent(verbose=args.verbose)
    result = orchestrator.run(context)

    # ── Final output ───────────────────────────────────────────────────
    print("\n" + "="*60)
    if result.get("success"):
        print("  ✅  PIPELINE COMPLETE")
        print(f"  ⏱  Duration   : {result.get('duration_sec')}s")
        print(f"  📊  Dashboard : {result.get('dashboard_path')}")
        if result.get("email_sent"):
            print(f"  📧  Email     : Sent to {args.email}")
        elif args.email:
            print("  📧  Email     : ⚠️  Failed (check .env credentials)")
        print("\n  📋  Summary:")
        for k, v in result.get("summary", {}).items():
            print(f"      {k:<12}: {v}")
    else:
        print("  ❌  PIPELINE FAILED")
        print(f"  Error: {result.get('error')}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
