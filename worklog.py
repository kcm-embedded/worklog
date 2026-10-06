#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import sys

from datetime import date, datetime, timedelta
from pathlib import Path


# ============================================================
# Configuration
# ============================================================

WORKLOG_DIR = Path(
    os.environ.get(
        "WORKLOG_DIR",
        Path.home() / "worklog",
    )
)

DAILY_DIR = WORKLOG_DIR / "daily"
JIRA_DIR = WORKLOG_DIR / "jira-drafts"


SECTIONS = {
    "note": "Thoughts",
    "task": "Actions",
    "decision": "Decisions",
    "risk": "Risks / Blockers",
    "followup": "Follow-up",
}


# ============================================================
# Setup
# ============================================================

def ensure_directories():
    DAILY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    JIRA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def initialise():
    ensure_directories()

    print("Worklog initialised.")
    print(f"Location: {WORKLOG_DIR}")


# ============================================================
# Daily files
# ============================================================

def daily_file(day=None):
    if day is None:
        day = date.today()

    year_dir = DAILY_DIR / str(day.year)
    month_dir = year_dir / f"{day.month:02}"

    month_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return month_dir / f"{day.isoformat()}.md"


def create_daily_file(day=None):
    if day is None:
        day = date.today()

    file = daily_file(day)

    if file.exists():
        return file

    content = f"""# {day.strftime("%A %d %B %Y")}

## Thoughts


## Actions


## Decisions


## Risks / Blockers


## Follow-up


"""

    file.write_text(
        content,
        encoding="utf-8",
    )

    return file


# ============================================================
# Markdown helpers
# ============================================================

def insert_line_into_section(
    file,
    section,
    entry,
):
    content = file.read_text(
        encoding="utf-8",
    )

    heading = f"## {section}"

    if heading not in content:
        content += f"\n{heading}\n\n"

    lines = content.splitlines()

    output = []
    inserted = False

    for line in lines:
        output.append(line)

        if line == heading and not inserted:
            output.append(entry)
            inserted = True

    file.write_text(
        "\n".join(output) + "\n",
        encoding="utf-8",
    )


def add_to_section(
    section,
    text,
):
    file = create_daily_file()

    if section == "Actions":
        entry = f"- [ ] {text}"
    else:
        entry = f"- {text}"

    insert_line_into_section(
        file,
        section,
        entry,
    )

    print(f"Added to {section}:")
    print(f"  {text}")


def add_entry(
    entry_type,
    text,
):
    add_to_section(
        SECTIONS[entry_type],
        text,
    )


def extract_section(
    content,
    section,
):
    heading = f"## {section}"

    lines = content.splitlines()

    found = False
    results = []

    for line in lines:

        if line == heading:
            found = True
            continue

        if found and line.startswith("## "):
            break

        if found and line.strip():
            results.append(
                line.strip()
            )

    return results


# ============================================================
# Task helpers
# ============================================================

def clean_task_text(task):
    text = re.sub(
        r"^- \[[ xX>]\]\s*",
        "",
        task,
    )

    text = re.sub(
        r"\s*<!--.*?-->\s*$",
        "",
        text,
    )

    return text.strip()


def get_open_tasks_for_file(file):
    if not file.exists():
        return []

    content = file.read_text(
        encoding="utf-8",
    )

    actions = extract_section(
        content,
        "Actions",
    )

    return [
        action
        for action in actions
        if action.startswith("- [ ]")
    ]


def get_completed_tasks_for_file(file):
    if not file.exists():
        return []

    content = file.read_text(
        encoding="utf-8",
    )

    actions = extract_section(
        content,
        "Actions",
    )

    return [
        action
        for action in actions
        if (
            action.startswith("- [x]")
            or action.startswith("- [X]")
        )
    ]


def get_carried_tasks_for_file(file):
    if not file.exists():
        return []

    content = file.read_text(
        encoding="utf-8",
    )

    actions = extract_section(
        content,
        "Actions",
    )

    return [
        action
        for action in actions
        if action.startswith("- [>]")
    ]


# ============================================================
# Show tasks
# ============================================================

def show_tasks():
    file = create_daily_file()

    open_tasks = (
        get_open_tasks_for_file(file)
    )

    completed_tasks = (
        get_completed_tasks_for_file(file)
    )

    print()
    print("TODAY'S TASKS")
    print("=" * 60)

    print("\nOPEN")

    if open_tasks:
        for number, task in enumerate(
            open_tasks,
            start=1,
        ):
            text = clean_task_text(task)

            origin_match = re.search(
                r"<!--\s*from:(.*?)\s*-->",
                task,
            )

            if origin_match:
                origin = origin_match.group(1)

                print(
                    f"{number}. {text} "
                    f"[from {origin}]"
                )

            else:
                print(
                    f"{number}. {text}"
                )

    else:
        print("No open tasks.")

    print("\nCOMPLETED")

    if completed_tasks:
        for number, task in enumerate(
            completed_tasks,
            start=1,
        ):
            print(
                f"{number}. "
                f"{clean_task_text(task)}"
            )

    else:
        print("No completed tasks.")

    print()


# ============================================================
# Complete / reopen tasks
# ============================================================

def complete_task(task_number):
    file = create_daily_file()

    content = file.read_text(
        encoding="utf-8",
    )

    open_tasks = (
        get_open_tasks_for_file(file)
    )

    if not open_tasks:
        print("No open tasks for today.")
        return

    if not (
        1 <= task_number <= len(open_tasks)
    ):
        print(
            "Invalid task number. "
            f"Choose 1-{len(open_tasks)}."
        )
        return

    selected = open_tasks[
        task_number - 1
    ]

    completed = selected.replace(
        "- [ ]",
        "- [x]",
        1,
    )

    content = content.replace(
        selected,
        completed,
        1,
    )

    file.write_text(
        content,
        encoding="utf-8",
    )

    print(
        "Completed: "
        f"{clean_task_text(selected)}"
    )


def undo_task(task_number):
    file = create_daily_file()

    content = file.read_text(
        encoding="utf-8",
    )

    completed_tasks = (
        get_completed_tasks_for_file(file)
    )

    if not completed_tasks:
        print(
            "No completed tasks for today."
        )
        return

    if not (
        1
        <= task_number
        <= len(completed_tasks)
    ):
        print(
            "Invalid task number. "
            f"Choose 1-{len(completed_tasks)}."
        )
        return

    selected = completed_tasks[
        task_number - 1
    ]

    reopened = re.sub(
        r"^- \[[xX]\]",
        "- [ ]",
        selected,
        count=1,
    )

    content = content.replace(
        selected,
        reopened,
        1,
    )

    file.write_text(
        content,
        encoding="utf-8",
    )

    print(
        "Reopened: "
        f"{clean_task_text(selected)}"
    )


# ============================================================
# Carry tasks
# ============================================================

def get_log_dates():
    dates = []

    if not DAILY_DIR.exists():
        return dates

    for file in DAILY_DIR.rglob("*.md"):
        try:
            log_date = date.fromisoformat(
                file.stem
            )

            dates.append(log_date)

        except ValueError:
            continue

    return sorted(
        set(dates)
    )


def get_previous_log_date():
    today = date.today()

    previous = [
        day
        for day in get_log_dates()
        if day < today
    ]

    if not previous:
        return None

    return max(previous)


def mark_task_carried(
    source_file,
    task,
    destination_day,
):
    content = source_file.read_text(
        encoding="utf-8",
    )

    text = clean_task_text(task)

    carried = (
        f"- [>] {text} "
        f"<!-- carried-to:"
        f"{destination_day.isoformat()} -->"
    )

    content = content.replace(
        task,
        carried,
        1,
    )

    source_file.write_text(
        content,
        encoding="utf-8",
    )


def carry_from_day(
    source_day,
    destination_day,
    existing_texts,
):
    source_file = daily_file(
        source_day
    )

    destination_file = (
        create_daily_file(
            destination_day
        )
    )

    open_tasks = (
        get_open_tasks_for_file(
            source_file
        )
    )

    carried_count = 0

    for task in open_tasks:
        text = clean_task_text(task)

        normalized = text.lower()

        if normalized in existing_texts:
            continue

        entry = (
            f"- [ ] {text} "
            f"<!-- from:"
            f"{source_day.isoformat()} -->"
        )

        insert_line_into_section(
            destination_file,
            "Actions",
            entry,
        )

        mark_task_carried(
            source_file,
            task,
            destination_day,
        )

        existing_texts.add(
            normalized
        )

        carried_count += 1

        print(
            f"Carried: {text}"
        )

    return carried_count


def carry_tasks(
    carry_all=False,
):
    today = date.today()

    today_file = (
        create_daily_file(today)
    )

    today_tasks = (
        get_open_tasks_for_file(
            today_file
        )
    )

    existing_texts = {
        clean_task_text(task).lower()
        for task in today_tasks
    }

    if carry_all:
        source_days = [
            day
            for day in get_log_dates()
            if day < today
        ]

    else:
        previous = (
            get_previous_log_date()
        )

        if previous is None:
            print(
                "No previous worklog "
                "was found."
            )
            return

        source_days = [previous]

    total = 0

    for source_day in source_days:
        total += carry_from_day(
            source_day,
            today,
            existing_texts,
        )

    if total == 0:
        print(
            "No unfinished tasks "
            "to carry forward."
        )

    else:
        print()
        print(
            f"Carried {total} "
            f"task(s) into today."
        )


# ============================================================
# Today
# ============================================================

def show_today():
    file = create_daily_file()

    print(
        file.read_text(
            encoding="utf-8",
        )
    )


# ============================================================
# Weekly report
# ============================================================

def monday_of_week(day):
    return day - timedelta(
        days=day.weekday()
    )


def print_simple_section(entries):
    if not entries:
        print("None")
        return

    for day, entry in entries:
        text = entry.removeprefix(
            "- "
        ).strip()

        print(
            f"{day:%a}: {text}"
        )


def weekly_summary():
    today = date.today()

    start = monday_of_week(
        today
    )

    sections = {
        "Actions": [],
        "Decisions": [],
        "Risks / Blockers": [],
        "Follow-up": [],
    }

    for offset in range(7):

        day = start + timedelta(
            days=offset
        )

        if day > today:
            break

        file = daily_file(day)

        if not file.exists():
            continue

        content = file.read_text(
            encoding="utf-8",
        )

        for section in sections:

            entries = extract_section(
                content,
                section,
            )

            for entry in entries:

                sections[
                    section
                ].append(
                    (
                        day,
                        entry,
                    )
                )

    print()
    print("=" * 60)
    print("WEEKLY WORKLOG")
    print(
        f"{start:%d %b %Y}"
        f" -> "
        f"{today:%d %b %Y}"
    )
    print("=" * 60)

    print("\nOPEN ACTIONS")

    open_entries = [
        (day, entry)
        for day, entry
        in sections["Actions"]
        if entry.startswith("- [ ]")
    ]

    if open_entries:
        for day, entry in open_entries:
            print(
                f"{day:%a}: "
                f"{clean_task_text(entry)}"
            )
    else:
        print("None")

    print("\nCOMPLETED")

    completed_entries = [
        (day, entry)
        for day, entry
        in sections["Actions"]
        if (
            entry.startswith("- [x]")
            or
            entry.startswith("- [X]")
        )
    ]

    if completed_entries:
        for day, entry in completed_entries:
            print(
                f"{day:%a}: "
                f"{clean_task_text(entry)}"
            )
    else:
        print("None")

    print("\nDECISIONS")

    print_simple_section(
        sections["Decisions"]
    )

    print("\nRISKS / BLOCKERS")

    print_simple_section(
        sections[
            "Risks / Blockers"
        ]
    )

    print("\nFOLLOW-UP")

    print_simple_section(
        sections["Follow-up"]
    )

    print()


# ============================================================
# Search
# ============================================================

def search_logs(query):
    if not DAILY_DIR.exists():
        print("No worklogs found.")
        return

    query_lower = query.lower()

    matches = []

    for file in sorted(
        DAILY_DIR.rglob("*.md")
    ):

        content = file.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for (
            line_number,
            line,
        ) in enumerate(
            content.splitlines(),
            start=1,
        ):

            if (
                query_lower
                in line.lower()
            ):

                matches.append(
                    (
                        file,
                        line_number,
                        line.strip(),
                    )
                )

    if not matches:

        print(
            f"No results for '{query}'."
        )

        return

    print()
    print(
        f"SEARCH RESULTS: {query}"
    )
    print("=" * 60)

    for (
        file,
        line_number,
        line,
    ) in matches:

        print(
            f"{file.stem}:"
            f"{line_number}: "
            f"{line}"
        )

    print()


# ============================================================
# Jira helpers
# ============================================================

def safe_filename(text):
    safe = "".join(
        char
        if char.isalnum()
        else "-"
        for char in text.lower()
    )

    return "-".join(
        part
        for part in safe.split("-")
        if part
    )


# ============================================================
# Jira Feature
# ============================================================

def feature_template(title):
    return f"""# FEATURE: {title}

## Summary

{title}


## Problem / Opportunity

What problem are we solving?

Why does this feature matter?


## Desired Outcome

Describe the outcome rather than the implementation.


## Benefit Hypothesis

We believe:

This will:

We will know this is successful when:


## Scope

### Included

-
-
-


### Out of Scope

-
-


## Feature Acceptance Criteria

- [ ]
- [ ]
- [ ]


## Functional Requirements

-
-


## Non-Functional Requirements

Consider where applicable:

- Performance
- Timing
- Reliability
- Security
- Safety
- Resource usage
- Compatibility
- Maintainability


## Dependencies

### Hardware

-


### Firmware

-


### Software

-


### External Teams

-


### Third-party APIs / Libraries

-


### Product Decisions Required

-


## Assumptions

-


## Risks / Unknowns

-


## Candidate Flow Items

### Flow Value

- [ ]


### Flow Accelerator

- [ ]


### Flow Defect

- [ ]


### Flow Quality

- [ ]


## Test / Verification Strategy

How will we demonstrate that the overall feature works?


## Definition of Done

- [ ] Feature acceptance criteria met
- [ ] Required flow items completed
- [ ] Integration complete
- [ ] Required reviews complete
- [ ] Tests implemented and passing
- [ ] Documentation updated
- [ ] Known limitations recorded
- [ ] Product acceptance obtained where required


"""


# ============================================================
# Jira Flow Value
# ============================================================

def flow_value_template(title):
    return f"""# FLOW VALUE: {title}

## Summary

{title}


## Parent Feature

FEATURE-


## Value / Outcome

What new behaviour, capability or system value
does this item deliver?


## Context

Why is this required?


## Requirement

The system shall:


## Acceptance Criteria

- [ ]
- [ ]
- [ ]


## Interfaces / Components

-


## Technical Context

Relevant information to help engineering understand
the problem without unnecessarily prescribing the solution.

-


## Dependencies

-


## Assumptions

-


## Risks / Unknowns

-


## Verification

How will we prove the required behaviour works?

- [ ]
- [ ]


## Definition of Done

- [ ] Acceptance criteria met
- [ ] Implementation complete
- [ ] Code reviewed
- [ ] Tests implemented
- [ ] Tests passing
- [ ] Integration verified
- [ ] Documentation updated where required


"""


# ============================================================
# Jira Flow Accelerator
# ============================================================

def flow_accelerator_template(title):
    return f"""# FLOW ACCELERATOR: {title}

## Summary

{title}


## Parent Feature

FEATURE-


## Purpose

What future work or delivery does this accelerate?


## Problem / Constraint

What is currently slowing, blocking or complicating delivery?


## Expected Improvement

After this work is completed, we expect:

-


## Work Required

-
-
-


## Enables

Which Features or Flow Value items does this enable?

-


## Technical Notes

-


## Dependencies

-


## Risks / Unknowns

-


## Acceptance Criteria

- [ ]
- [ ]
- [ ]


## Verification

How will we know this accelerator has achieved its purpose?

- [ ]


## Definition of Done

- [ ] Required capability available
- [ ] Intended downstream work can proceed
- [ ] Implementation reviewed
- [ ] Tests complete where applicable
- [ ] Documentation updated


"""


# ============================================================
# Jira Flow Defect
# ============================================================

def flow_defect_template(title):
    return f"""# FLOW DEFECT: {title}

## Summary

{title}


## Parent Feature

FEATURE-


## Problem

Describe the incorrect behaviour.


## Expected Behaviour

What should happen?


## Actual Behaviour

What currently happens?


## Reproduction

1.
2.
3.


## Environment

### Hardware

-


### Software / Firmware Version

-


### Configuration

-


## Impact

What is the impact of this defect?


## Severity / Priority

Severity:

Priority:


## Root Cause

Unknown / To be investigated


## Fix

Describe once understood:

-


## Acceptance Criteria

- [ ] Expected behaviour restored
- [ ] Regression verified
- [ ] No known adverse impact introduced


## Verification

- [ ]
- [ ]


## Regression Testing

What else could this fix affect?

-


## Definition of Done

- [ ] Root cause understood where required
- [ ] Fix implemented
- [ ] Code reviewed
- [ ] Defect verification passed
- [ ] Regression tests passed
- [ ] Documentation updated if required


"""


# ============================================================
# Jira Flow Quality
# ============================================================

def flow_quality_template(title):
    return f"""# FLOW QUALITY: {title}

## Summary

{title}


## Parent Feature

FEATURE-


## Quality Objective

What aspect of quality are we improving?


## Current State

What is the current limitation, weakness or quality risk?


## Desired State

What should be improved after this work?


## Quality Area

Examples:

- Test coverage
- Reliability
- Maintainability
- Performance
- Security
- Static analysis
- Technical debt
- Documentation
- Diagnostics / observability
- Robustness


## Work Required

-
-
-


## Quality Criteria

- [ ]
- [ ]
- [ ]


## Measurement / Evidence

How will improvement be demonstrated?

-


## Dependencies

-


## Risks

-


## Verification

- [ ]
- [ ]


## Definition of Done

- [ ] Quality criteria met
- [ ] Evidence captured
- [ ] Relevant tests passing
- [ ] Reviews complete
- [ ] Documentation updated where required


"""


JIRA_TEMPLATES = {
    "feature": feature_template,
    "flow-value": flow_value_template,
    "flow-accelerator": flow_accelerator_template,
    "flow-defect": flow_defect_template,
    "flow-quality": flow_quality_template,
}


JIRA_DISPLAY_NAMES = {
    "feature": "Feature",
    "flow-value": "Flow Value",
    "flow-accelerator": "Flow Accelerator",
    "flow-defect": "Flow Defect",
    "flow-quality": "Flow Quality",
}


# ============================================================
# Create Jira draft
# ============================================================

def create_jira_draft(
    ticket_type,
    title,
):
    ensure_directories()

    timestamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    filename = (
        JIRA_DIR
        / (
            f"{timestamp}-"
            f"{ticket_type}-"
            f"{safe_filename(title)}.md"
        )
    )

    template_function = (
        JIRA_TEMPLATES[
            ticket_type
        ]
    )

    content = (
        template_function(title)
    )

    filename.write_text(
        content,
        encoding="utf-8",
    )

    display_name = (
        JIRA_DISPLAY_NAMES[
            ticket_type
        ]
    )

    print()
    print(
        f"Created Jira {display_name} draft:"
    )
    print(filename)
    print()


# ============================================================
# Interactive Jira menu
# ============================================================

def interactive_jira():
    options = [
        ("feature", "Feature"),
        ("flow-value", "Flow Value"),
        (
            "flow-accelerator",
            "Flow Accelerator",
        ),
        ("flow-defect", "Flow Defect"),
        ("flow-quality", "Flow Quality"),
    ]

    print()
    print("CREATE JIRA ITEM")
    print("=" * 40)
    print()

    for number, (_, display_name) in enumerate(
        options,
        start=1,
    ):
        print(
            f"{number}. {display_name}"
        )

    print()

    while True:
        choice = input(
            "Type: "
        ).strip()

        try:
            choice_number = int(choice)

            if (
                1
                <= choice_number
                <= len(options)
            ):
                break

        except ValueError:
            pass

        print(
            f"Choose a number between "
            f"1 and {len(options)}."
        )

    ticket_type = options[
        choice_number - 1
    ][0]

    print()

    while True:
        title = input(
            "Title: "
        ).strip()

        if title:
            break

        print(
            "A title is required."
        )

    create_jira_draft(
        ticket_type,
        title,
    )


# ============================================================
# Open today's file
# ============================================================

def open_today():
    file = create_daily_file()

    editor = os.environ.get(
        "EDITOR"
    )

    if editor:

        subprocess.call(
            [
                editor,
                str(file),
            ]
        )

        return

    if sys.platform.startswith(
        "win"
    ):

        os.startfile(file)

    elif sys.platform == "darwin":

        subprocess.call(
            [
                "open",
                str(file),
            ]
        )

    else:

        subprocess.call(
            [
                "xdg-open",
                str(file),
            ]
        )


# ============================================================
# CLI
# ============================================================

def main():
    ensure_directories()

    parser = argparse.ArgumentParser(
        prog="worklog",
        description=(
            "Markdown engineering "
            "and Product Owner worklog"
        ),
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # --------------------------------------------------------
    # Initialise
    # --------------------------------------------------------

    sub.add_parser(
        "init",
        help="Initialise worklog",
    )

    # --------------------------------------------------------
    # Capture
    # --------------------------------------------------------

    for command in SECTIONS:

        cmd = sub.add_parser(
            command,
            help=f"Add a {command}",
        )

        cmd.add_argument(
            "text",
            nargs="+",
        )

    # --------------------------------------------------------
    # View
    # --------------------------------------------------------

    sub.add_parser(
        "today",
        help="Show today's worklog",
    )

    sub.add_parser(
        "open",
        help="Open today's worklog",
    )

    # --------------------------------------------------------
    # Tasks
    # --------------------------------------------------------

    sub.add_parser(
        "tasks",
        help="Show today's tasks",
    )

    done = sub.add_parser(
        "done",
        help=(
            "Mark an open task "
            "as complete"
        ),
    )

    done.add_argument(
        "task_number",
        type=int,
    )

    undo = sub.add_parser(
        "undo",
        help=(
            "Reopen a completed task"
        ),
    )

    undo.add_argument(
        "task_number",
        type=int,
    )

    carry = sub.add_parser(
        "carry",
        help=(
            "Carry unfinished tasks "
            "into today"
        ),
    )

    carry.add_argument(
        "--all",
        action="store_true",
        help=(
            "Carry open tasks from "
            "all previous logs instead "
            "of only the most recent log"
        ),
    )

    # --------------------------------------------------------
    # Reports
    # --------------------------------------------------------

    sub.add_parser(
        "week",
        help=(
            "Generate weekly summary"
        ),
    )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    search = sub.add_parser(
        "search",
        help="Search all worklogs",
    )

    search.add_argument(
        "query",
        nargs="+",
    )

    # --------------------------------------------------------
    # Jira
    # --------------------------------------------------------

    jira = sub.add_parser(
        "jira",
        help=(
            "Create a Jira draft "
            "interactively or directly"
        ),
    )

    jira.add_argument(
        "ticket_type",
        nargs="?",
        choices=[
            "feature",
            "flow-value",
            "flow-accelerator",
            "flow-defect",
            "flow-quality",
        ],
    )

    jira.add_argument(
        "title",
        nargs="*",
    )

    # --------------------------------------------------------
    # Parse
    # --------------------------------------------------------

    args = parser.parse_args()

    # --------------------------------------------------------
    # Execute
    # --------------------------------------------------------

    if args.command == "init":

        initialise()

    elif args.command in SECTIONS:

        add_entry(
            args.command,
            " ".join(args.text),
        )

    elif args.command == "today":

        show_today()

    elif args.command == "open":

        open_today()

    elif args.command == "tasks":

        show_tasks()

    elif args.command == "done":

        complete_task(
            args.task_number
        )

    elif args.command == "undo":

        undo_task(
            args.task_number
        )

    elif args.command == "carry":

        carry_tasks(
            carry_all=args.all
        )

    elif args.command == "week":

        weekly_summary()

    elif args.command == "search":

        search_logs(
            " ".join(args.query)
        )

    elif args.command == "jira":

        # No type supplied:
        # launch interactive Jira wizard.
        if args.ticket_type is None:

            interactive_jira()

        else:

            title = " ".join(
                args.title
            ).strip()

            # A type was supplied,
            # but no title.
            # Ask interactively for title.
            if not title:

                display_name = (
                    JIRA_DISPLAY_NAMES[
                        args.ticket_type
                    ]
                )

                print(
                    f"\nCreating "
                    f"{display_name}\n"
                )

                while not title:
                    title = input(
                        "Title: "
                    ).strip()

            create_jira_draft(
                args.ticket_type,
                title,
            )


if __name__ == "__main__":
    main()