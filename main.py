"""Entry point for the IT / Ticket Auto-Resolution Agent.

Usage:
    python main.py            # process all new tickets
    python main.py --reset    # reset all tickets to 'New' (repeatable demos)
    python main.py --reset-run  # reset, then process (handy for the demo)
    python main.py --add-ticket # add a new 'New' ticket interactively (live demo)

The pipeline automatically uses the LLM + Ollama embeddings when the endpoint is
reachable, and transparently falls back to an offline keyword classifier and
TF-IDF retrieval when it is not.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

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


def _next_ticket_id(tickets: list[dict]) -> str:
    """Return the next INC id based on the highest existing numeric suffix."""
    max_num = 0
    for t in tickets:
        tid = str(t.get("id", ""))
        digits = "".join(ch for ch in tid if ch.isdigit())
        if digits:
            max_num = max(max_num, int(digits))
    if max_num == 0:
        max_num = 12000
    return f"INC{max_num + 1:07d}"


def add_ticket(
    short_description: str | None = None,
    description: str | None = None,
    priority: str | None = None,
) -> dict:
    """Add a new ticket with status 'New' to the mock store.

    If any field is missing it is collected interactively so this can be used
    live during a demo (``python main.py --add-ticket``).
    """
    if short_description is None:
        short_description = input("Short description: ").strip()
    if description is None:
        description = input("Description (details): ").strip() or short_description
    if priority is None:
        priority = input("Priority [Low/Medium/High] (default Medium): ").strip() or "Medium"

    tickets_file = path("data", "tickets.json")
    tickets = json.loads(tickets_file.read_text(encoding="utf-8"))

    ticket = {
        "id": _next_ticket_id(tickets),
        "short_description": short_description,
        "description": description,
        "category": None,
        "priority": priority,
        "status": "New",
        "assigned_to": None,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    tickets.append(ticket)
    tickets_file.write_text(
        json.dumps(tickets, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Created ticket {ticket['id']} ({ticket['priority']}) with status 'New'.")
    return ticket


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
    parser.add_argument(
        "--add-ticket",
        action="store_true",
        help="Add a new ticket to the queue (interactive unless fields are given)",
    )
    parser.add_argument("--short", help="Short description for --add-ticket")
    parser.add_argument("--desc", help="Full description for --add-ticket")
    parser.add_argument("--priority", help="Priority for --add-ticket (Low/Medium/High)")
    parser.add_argument(
        "--run",
        action="store_true",
        help="With --add-ticket, process the queue immediately after adding",
    )
    args = parser.parse_args()

    if args.reset:
        n = reset_tickets()
        print(f"Reset {n} tickets to 'New'.")
        return

    if args.add_ticket:
        add_ticket(args.short, args.desc, args.priority)
        if not args.run:
            print("Run 'python main.py' to process the queue.")
            return
        print()

    if args.reset_run:
        n = reset_tickets()
        print(f"Reset {n} tickets to 'New'.\n")

    results = Orchestrator().run()
    print_summary(results)


if __name__ == "__main__":
    main()
