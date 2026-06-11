#!/usr/bin/env python3
"""Dependency-free CLI for the Growth OS."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / ".growth" / "growth.db"
GOALS_PATH = ROOT / "config" / "goals.json"
REVIEWS_PATH = ROOT / "reviews"


def monday(value: Optional[str] = None) -> date:
    day = date.fromisoformat(value) if value else date.today()
    return day - timedelta(days=day.weekday())


def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise SystemExit("Growth OS is not initialized. Run: python3 growth.py init")
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS areas (
            key TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            priority INTEGER NOT NULL,
            allocation INTEGER NOT NULL,
            outcome TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS commitments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week TEXT NOT NULL,
            area_key TEXT NOT NULL REFERENCES areas(key),
            title TEXT NOT NULL,
            target REAL NOT NULL DEFAULT 1,
            progress REAL NOT NULL DEFAULT 0,
            unit TEXT NOT NULL DEFAULT 'artifact',
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL,
            completed_at TEXT,
            note TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurred_on TEXT NOT NULL,
            week TEXT NOT NULL,
            area_key TEXT NOT NULL REFERENCES areas(key),
            kind TEXT NOT NULL,
            value REAL NOT NULL DEFAULT 1,
            note TEXT NOT NULL,
            commitment_id INTEGER REFERENCES commitments(id),
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_on TEXT NOT NULL,
            title TEXT NOT NULL,
            helps TEXT NOT NULL,
            decision TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT ''
        );
        """
    )
    connection.commit()


def command_init(_: argparse.Namespace) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    goals = json.loads(GOALS_PATH.read_text())
    connection = sqlite3.connect(DB_PATH)
    create_schema(connection)
    connection.executemany(
        """
        INSERT INTO areas(key, name, priority, allocation, outcome)
        VALUES(:key, :name, :priority, :allocation, :outcome)
        ON CONFLICT(key) DO UPDATE SET
            name=excluded.name,
            priority=excluded.priority,
            allocation=excluded.allocation,
            outcome=excluded.outcome
        """,
        goals["areas"],
    )
    connection.commit()
    print(f"Initialized Growth OS at {DB_PATH}")
    print("Next: python3 growth.py dashboard")


def validate_area(connection: sqlite3.Connection, area: str) -> None:
    if not connection.execute("SELECT 1 FROM areas WHERE key = ?", (area,)).fetchone():
        valid = ", ".join(row["key"] for row in connection.execute("SELECT key FROM areas"))
        raise SystemExit(f"Unknown area '{area}'. Valid areas: {valid}")


def command_add(args: argparse.Namespace) -> None:
    connection = connect()
    validate_area(connection, args.area)
    week = monday(args.week).isoformat()
    cursor = connection.execute(
        """
        INSERT INTO commitments(week, area_key, title, target, unit, created_at)
        VALUES(?, ?, ?, ?, ?, ?)
        """,
        (week, args.area, args.title, args.target, args.unit, datetime.now().isoformat()),
    )
    connection.commit()
    print(f"Added commitment #{cursor.lastrowid} for week {week}: {args.title}")


def command_list(args: argparse.Namespace) -> None:
    connection = connect()
    conditions: list[str] = []
    values: list[str] = []
    if not args.all:
        conditions.append("c.week = ?")
        values.append(monday(args.week).isoformat())
    if args.area:
        validate_area(connection, args.area)
        conditions.append("c.area_key = ?")
        values.append(args.area)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = connection.execute(
        f"""
        SELECT c.*, a.name AS area_name
        FROM commitments c JOIN areas a ON a.key = c.area_key
        {where}
        ORDER BY c.week DESC, a.priority, c.id
        """,
        values,
    ).fetchall()
    if not rows:
        print("No commitments found.")
        return
    for row in rows:
        marker = "x" if row["status"] == "done" else " "
        print(
            f"[{marker}] #{row['id']} {row['area_name']}: {row['title']} "
            f"({row['progress']:g}/{row['target']:g} {row['unit']})"
        )


def command_done(args: argparse.Namespace) -> None:
    connection = connect()
    row = connection.execute("SELECT * FROM commitments WHERE id = ?", (args.id,)).fetchone()
    if not row:
        raise SystemExit(f"Commitment #{args.id} does not exist.")
    progress = row["progress"] + args.value
    status = "done" if progress >= row["target"] else "open"
    completed_at = datetime.now().isoformat() if status == "done" else None
    connection.execute(
        """
        UPDATE commitments
        SET progress = ?, status = ?, completed_at = ?, note = ?
        WHERE id = ?
        """,
        (progress, status, completed_at, args.note or row["note"], args.id),
    )
    connection.execute(
        """
        INSERT INTO evidence(
            occurred_on, week, area_key, kind, value, note, commitment_id, created_at
        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            date.today().isoformat(),
            monday().isoformat(),
            row["area_key"],
            "commitment_progress",
            args.value,
            args.note or row["title"],
            args.id,
            datetime.now().isoformat(),
        ),
    )
    connection.commit()
    print(f"Commitment #{args.id}: {progress:g}/{row['target']:g} {row['unit']} ({status})")


def command_evidence(args: argparse.Namespace) -> None:
    connection = connect()
    validate_area(connection, args.area)
    occurred_on = date.fromisoformat(args.date) if args.date else date.today()
    cursor = connection.execute(
        """
        INSERT INTO evidence(occurred_on, week, area_key, kind, value, note, created_at)
        VALUES(?, ?, ?, ?, ?, ?, ?)
        """,
        (
            occurred_on.isoformat(),
            monday(occurred_on.isoformat()).isoformat(),
            args.area,
            args.kind,
            args.value,
            args.note,
            datetime.now().isoformat(),
        ),
    )
    connection.commit()
    print(f"Recorded evidence #{cursor.lastrowid}: {args.kind} - {args.note}")


def command_dashboard(args: argparse.Namespace) -> None:
    connection = connect()
    end = monday()
    start = end - timedelta(weeks=args.weeks - 1)
    areas = connection.execute("SELECT * FROM areas ORDER BY priority").fetchall()
    print(f"Growth OS | {start.isoformat()} through {(end + timedelta(days=6)).isoformat()}")
    print("=" * 72)
    for area in areas:
        commitments = connection.execute(
            """
            SELECT COUNT(*) AS planned,
                   SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS done
            FROM commitments
            WHERE area_key = ? AND week BETWEEN ? AND ?
            """,
            (area["key"], start.isoformat(), end.isoformat()),
        ).fetchone()
        evidence = connection.execute(
            """
            SELECT COUNT(*) AS entries, COALESCE(SUM(value), 0) AS total
            FROM evidence
            WHERE area_key = ? AND week BETWEEN ? AND ?
            """,
            (area["key"], start.isoformat(), end.isoformat()),
        ).fetchone()
        print(
            f"{area['name']:<20} allocation {area['allocation']:>2}% | "
            f"commitments {commitments['done'] or 0}/{commitments['planned']} | "
            f"evidence {evidence['entries']} entries"
        )
    print("\nCurrent week:")
    current = connection.execute(
        """
        SELECT c.*, a.name AS area_name
        FROM commitments c JOIN areas a ON a.key = c.area_key
        WHERE c.week = ? ORDER BY a.priority, c.id
        """,
        (end.isoformat(),),
    ).fetchall()
    if not current:
        print("  No commitments yet. Add 5-8 measurable weekly bets.")
    for row in current:
        marker = "done" if row["status"] == "done" else "open"
        print(f"  #{row['id']} [{marker}] {row['area_name']}: {row['title']}")


def command_idea(args: argparse.Namespace) -> None:
    connection = connect()
    helps = sorted(set(args.helps or []))
    decision = "eligible" if helps else "reject"
    connection.execute(
        "INSERT INTO ideas(created_on, title, helps, decision, note) VALUES(?, ?, ?, ?, ?)",
        (date.today().isoformat(), args.title, ",".join(helps), decision, args.note or ""),
    )
    connection.commit()
    if helps:
        print(f"ELIGIBLE: helps {', '.join(helps)}.")
        print("It still must beat the opportunity cost of an existing weekly commitment.")
    else:
        print("REJECT: it does not clearly improve health, job, Lens, quant, or network.")


def command_review(args: argparse.Namespace) -> None:
    connection = connect()
    week = monday(args.week)
    week_text = week.isoformat()
    areas = connection.execute("SELECT * FROM areas ORDER BY priority").fetchall()
    lines = [
        f"# Weekly Review: {week_text}",
        "",
        "## Generated Scoreboard",
        "",
        "| Area | Completed | Planned | Evidence Entries |",
        "|---|---:|---:|---:|",
    ]
    for area in areas:
        counts = connection.execute(
            """
            SELECT COUNT(*) AS planned,
                   SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS done
            FROM commitments WHERE week = ? AND area_key = ?
            """,
            (week_text, area["key"]),
        ).fetchone()
        evidence_count = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence WHERE week = ? AND area_key = ?",
            (week_text, area["key"]),
        ).fetchone()["count"]
        lines.append(
            f"| {area['name']} | {counts['done'] or 0} | {counts['planned']} | {evidence_count} |"
        )
    lines.extend(["", "## Evidence", ""])
    evidence_rows = connection.execute(
        """
        SELECT e.*, a.name AS area_name
        FROM evidence e JOIN areas a ON a.key = e.area_key
        WHERE e.week = ? ORDER BY a.priority, e.occurred_on, e.id
        """,
        (week_text,),
    ).fetchall()
    if evidence_rows:
        for row in evidence_rows:
            lines.append(f"- **{row['area_name']} / {row['kind']}:** {row['note']}")
    else:
        lines.append("- No evidence recorded.")
    lines.extend(
        [
            "",
            "## Reflection",
            "",
            "### What created real outcomes or external signals?",
            "",
            "- [Add outcome or signal]",
            "",
            "### What consumed time without changing an outcome?",
            "",
            "- [Add low-value activity]",
            "",
            "### Which repeated gaps need attention?",
            "",
            "- [Add repeated gap]",
            "",
            "### Stop, continue, start",
            "",
            "- **Stop:** [Add item]",
            "- **Continue:** [Add item]",
            "- **Start:** [Add item]",
            "",
            "## Next Week's 5-8 Bets",
            "",
            "- [Add measurable commitment]",
            "",
        ]
    )
    REVIEWS_PATH.mkdir(exist_ok=True)
    path = REVIEWS_PATH / f"{week_text}.md"
    path.write_text("\n".join(lines))
    print(f"Generated {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Persistent evidence-based Growth OS")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize or refresh the database")
    init_parser.set_defaults(func=command_init)

    add_parser = subparsers.add_parser("add", help="Add a weekly commitment")
    add_parser.add_argument("--area", required=True)
    add_parser.add_argument("--title", required=True)
    add_parser.add_argument("--target", type=float, default=1)
    add_parser.add_argument("--unit", default="artifact")
    add_parser.add_argument("--week", help="Any date in the target week (YYYY-MM-DD)")
    add_parser.set_defaults(func=command_add)

    list_parser = subparsers.add_parser("list", help="List commitments")
    list_parser.add_argument("--area")
    list_parser.add_argument("--week")
    list_parser.add_argument("--all", action="store_true")
    list_parser.set_defaults(func=command_list)

    done_parser = subparsers.add_parser("done", help="Record progress on a commitment")
    done_parser.add_argument("id", type=int)
    done_parser.add_argument("--value", type=float, default=1)
    done_parser.add_argument("--note")
    done_parser.set_defaults(func=command_done)

    evidence_parser = subparsers.add_parser("evidence", help="Record independent evidence")
    evidence_parser.add_argument("--area", required=True)
    evidence_parser.add_argument("--kind", required=True)
    evidence_parser.add_argument("--value", type=float, default=1)
    evidence_parser.add_argument("--note", required=True)
    evidence_parser.add_argument("--date")
    evidence_parser.set_defaults(func=command_evidence)

    dashboard_parser = subparsers.add_parser("dashboard", help="Show the operating dashboard")
    dashboard_parser.add_argument("--weeks", type=int, default=1)
    dashboard_parser.set_defaults(func=command_dashboard)

    idea_parser = subparsers.add_parser("idea", help="Apply the decision filter to an idea")
    idea_parser.add_argument("title")
    idea_parser.add_argument(
        "--helps",
        nargs="*",
        choices=["health", "job", "lens", "quant", "network"],
    )
    idea_parser.add_argument("--note")
    idea_parser.set_defaults(func=command_idea)

    review_parser = subparsers.add_parser("review", help="Generate a weekly review")
    review_parser.add_argument("--week", help="Any date in the reviewed week (YYYY-MM-DD)")
    review_parser.set_defaults(func=command_review)
    return parser


if __name__ == "__main__":
    arguments = build_parser().parse_args()
    arguments.func(arguments)
