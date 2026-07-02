"""Entry point for the IT / Ticket Auto-Resolution Agent.

Usage:
    python main.py            # process all new tickets
    python main.py --reset    # reset all tickets to 'New' (repeatable demos)
    python main.py --reset-run  # reset, then process (handy for the demo)

The pipeline automatically uses the LLM + Ollama embeddings when the endpoint is
reachable, and transparently falls back to an offline keyword classifier and
TF-IDF retrieval when it is not.
"""
from __future__ import annotations

import argparse
import json

from src.config import path
from src.orchestrator import Orchestrator


def reset_tickets() -> int:
    """Reset every ticket in the mock store back to status 'New'."""
    tickets_file = path("data", "tickets.json")
    tickets = json.loads(tickets_file.read_text(encoding="utf-8"))
    for t in tickets:
        t["status"] = "New"
        t["assigned_to"] = None
        t.pop("resolution_comment", None)
    tickets_file.write_text(
        json.dumps(tickets, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return len(tickets)


def print_summary(results: list[dict]) -> None:
    print("\n" + "=" * 78)
    print("RESOLUTION SUMMARY")
    print("=" * 78)
    print(f"{'Ticket':<12}{'Category':<22}{'Conf':<7}{'Outcome':<14}{'Status':<12}")
    print("-" * 78)
    auto = 0
    for r in results:
        c = r["classification"]
        e = r["execution"]
        if e["outcome"] == "auto_resolved":
            auto += 1
        print(
            f"{r['ticket_id']:<12}"
            f"{c['category'][:20]:<22}"
            f"{c['confidence']:<7.2f}"
            f"{e['outcome']:<14}"
            f"{e['new_status']:<12}"
        )
    print("-" * 78)
    print(f"Total: {len(results)}  |  Auto-resolved: {auto}  |  Escalated: {len(results) - auto}")
    print("=" * 78)


def main() -> None:
    parser = argparse.ArgumentParser(description="IT / Ticket Auto-Resolution Agent")
    parser.add_argument("--reset", action="store_true", help="Reset tickets to 'New' and exit")
    parser.add_argument("--reset-run", action="store_true", help="Reset tickets, then process")
    args = parser.parse_args()

    if args.reset:
        n = reset_tickets()
        print(f"Reset {n} tickets to 'New'.")
        return

    if args.reset_run:
        n = reset_tickets()
        print(f"Reset {n} tickets to 'New'.\n")

    results = Orchestrator().run()
    print_summary(results)


if __name__ == "__main__":
    main()
