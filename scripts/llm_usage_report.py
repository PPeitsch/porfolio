"""Sums the chat's usage log by day (app/common/llm_usage.py).

    python scripts/llm_usage_report.py [folder] [--days 14]

The folder defaults to instance/llm_usage. "Top visitor" is the most calls from
a single visitor that day: the first number to look at for abuse.
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder", nargs="?", default="instance/llm_usage")
    parser.add_argument("--days", type=int, default=14)
    args = parser.parse_args()

    files = sorted(Path(args.folder).glob("llm_usage_*.jsonl"))[-args.days :]
    if not files:
        print(f"No usage log in {args.folder}.")
        return
    print(
        f"{'Day':<12}{'Calls':>7}{'Errors':>8}{'Visitors':>10}{'Top visitor':>13}"
        f"{'Tokens in':>11}{'Tokens out':>12}{'USD':>10}"
    )
    total = 0.0
    for path in files:
        day: dict = defaultdict(int)
        visitors: Counter = Counter()
        cost = 0.0
        for raw in path.read_text(encoding="utf-8").splitlines():
            try:
                line = json.loads(raw)
            except ValueError:
                continue
            day["calls"] += 1
            day["errors"] += bool(line.get("error"))
            day["in"] += line.get("input_tokens") or 0
            day["out"] += line.get("output_tokens") or 0
            cost += line.get("cost") or 0.0
            if line.get("visitor"):
                visitors[line["visitor"]] += 1
        total += cost
        top = visitors.most_common(1)[0][1] if visitors else 0
        date = path.stem[len("llm_usage_") :]
        print(
            f"{date:<12}{day['calls']:>7}{day['errors']:>8}{len(visitors):>10}"
            f"{top:>13}{day['in']:>11,}{day['out']:>12,}{cost:>10.4f}"
        )
    print(f"{'Total':<71}{total:>10.4f}")


if __name__ == "__main__":
    main()
