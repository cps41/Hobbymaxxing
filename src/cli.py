import argparse
from datetime import datetime

from graph import build_graph


def main() -> None:
    parser = argparse.ArgumentParser(prog="hobbymaxxing")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Get a hobby recommendation")
    run_parser.add_argument("--horizon", choices=["today", "week"], default="today")
    run_parser.add_argument("--feeling", default=None)

    args = parser.parse_args()

    if args.command == "run":
        graph = build_graph()
        result = graph.invoke(
            {
                "run_timestamp": datetime.now().isoformat(),
                "horizon": args.horizon,
                "user_feeling_input": args.feeling,
            }
        )
        rec = result["final_recommendation"]
        print(f"Suggestion: {rec['hobby']}")
        print(f"Reasoning: {rec['reasoning']}")
        if rec.get("alternatives"):
            print(f"Alternatives: {', '.join(rec['alternatives'])}")
        if result.get("skip_reasons"):
            for domain, reason in result["skip_reasons"].items():
                print(f"Skipped {domain}: {reason}")


if __name__ == "__main__":
    main()
