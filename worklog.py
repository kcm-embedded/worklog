#!/usr/bin/env python3

import argparse
import base64
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.request

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


JIRA_DISPLAY_NAMES = {
    "feature": "Feature",
    "flow-value": "Flow Value",
    "flow-accelerator": "Flow Accelerator",
    "flow-defect": "Flow Defect",
    "flow-quality": "Flow Quality",
}


JIRA_HEADING_NAMES = {
    "FEATURE": "feature",
    "FLOW VALUE": "flow-value",
    "FLOW ACCELERATOR": "flow-accelerator",
    "FLOW DEFECT": "flow-defect",
    "FLOW QUALITY": "flow-quality",
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


def add_to_section(section, text):
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


def add_entry(entry_type, text):
    add_to_section(
        SECTIONS[entry_type],
        text,
    )


def extract_section(content, section):
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
# Tasks
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


def show_tasks():
    file = create_daily_file()

    open_tasks = get_open_tasks_for_file(
        file
    )

    completed_tasks = (
        get_completed_tasks_for_file(
            file
        )
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
                print(
                    f"{number}. {text} "
                    f"[from {origin_match.group(1)}]"
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


def complete_task(task_number):
    file = create_daily_file()

    content = file.read_text(
        encoding="utf-8",
    )

    tasks = get_open_tasks_for_file(
        file
    )

    if not tasks:
        print("No open tasks for today.")
        return

    if not 1 <= task_number <= len(tasks):
        print(
            f"Choose a task between "
            f"1 and {len(tasks)}."
        )
        return

    selected = tasks[
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

    tasks = (
        get_completed_tasks_for_file(
            file
        )
    )

    if not tasks:
        print(
            "No completed tasks for today."
        )
        return

    if not 1 <= task_number <= len(tasks):
        print(
            f"Choose a task between "
            f"1 and {len(tasks)}."
        )
        return

    selected = tasks[
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

    for file in DAILY_DIR.rglob(
        "*.md"
    ):
        try:
            dates.append(
                date.fromisoformat(
                    file.stem
                )
            )
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

    tasks = get_open_tasks_for_file(
        source_file
    )

    count = 0

    for task in tasks:
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

        count += 1

        print(
            f"Carried: {text}"
        )

    return count


def carry_tasks(carry_all=False):
    today = date.today()

    today_file = create_daily_file(
        today
    )

    existing_texts = {
        clean_task_text(task).lower()
        for task
        in get_open_tasks_for_file(
            today_file
        )
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
                "No previous worklog found."
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

    if total:
        print(
            f"\nCarried {total} "
            "task(s) into today."
        )
    else:
        print(
            "No unfinished tasks "
            "to carry forward."
        )


# ============================================================
# Daily views
# ============================================================

def show_today():
    print(
        create_daily_file().read_text(
            encoding="utf-8"
        )
    )


def open_today():
    file = create_daily_file()

    editor = os.environ.get(
        "EDITOR"
    )

    if editor:
        subprocess.call(
            [editor, str(file)]
        )
        return

    if sys.platform.startswith(
        "win"
    ):
        os.startfile(file)

    elif sys.platform == "darwin":
        subprocess.call(
            ["open", str(file)]
        )

    else:
        subprocess.call(
            ["xdg-open", str(file)]
        )


# ============================================================
# Weekly summary
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
        text = entry

        if text.startswith("- "):
            text = text[2:]

        print(
            f"{day:%a}: {text.strip()}"
        )


def weekly_summary():
    today = date.today()
    start = monday_of_week(today)

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
            encoding="utf-8"
        )

        for section in sections:
            for entry in extract_section(
                content,
                section,
            ):
                sections[
                    section
                ].append(
                    (day, entry)
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
            or entry.startswith("- [X]")
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
        sections["Risks / Blockers"]
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

        for line_number, line in enumerate(
            content.splitlines(),
            start=1,
        ):
            if query_lower in line.lower():
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
# Jira templates
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


def flow_value_template(title):
    return f"""# FLOW VALUE: {title}

## Summary

{title}


## Parent Feature

FEATURE-


## Value / Outcome

What new behaviour, capability or system value does this item deliver?


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

Relevant information to help engineering understand the problem
without unnecessarily prescribing the implementation.


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


# ============================================================
# Markdown -> Jira Wiki Markup
# ============================================================

def convert_inline_markdown(text):
    """
    Convert common inline Markdown constructs to Jira wiki markup.
    """

    # Links: [label](url) -> [label|url]
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r"[\1|\2]",
        text,
    )

    # Bold
    text = re.sub(
        r"\*\*(.+?)\*\*",
        r"*\1*",
        text,
    )

    # Inline code
    text = re.sub(
        r"`([^`]+)`",
        r"{{\1}}",
        text,
    )

    return text


def markdown_to_jira(markdown):
    """
    Convert the subset of Markdown used by Worklog templates
    into Jira Data Center wiki markup.
    """

    lines = markdown.splitlines()

    output = []
    in_code_block = False
    first_h1_skipped = False
    skip_jira_issue_section = False

    for line in lines:

        # Do not copy local post-create metadata into Jira.
        if line.strip() == "## Jira Issue":
            skip_jira_issue_section = True
            continue

        if (
            skip_jira_issue_section
            and line.startswith("## ")
        ):
            skip_jira_issue_section = False

        if skip_jira_issue_section:
            continue

        if line.startswith("```"):
            if in_code_block:
                output.append("{code}")
                in_code_block = False
            else:
                output.append("{code}")
                in_code_block = True
            continue

        if in_code_block:
            output.append(line)
            continue

        # Skip the top H1 because Jira already has a Summary.
        if line.startswith("# ") and not first_h1_skipped:
            first_h1_skipped = True
            continue

        heading_match = re.match(
            r"^(#{1,6})\s+(.+)$",
            line,
        )

        if heading_match:
            level = len(
                heading_match.group(1)
            )

            title = convert_inline_markdown(
                heading_match.group(2)
            )

            output.append(
                f"h{level}. {title}"
            )
            continue

        task_match = re.match(
            r"^-\s+\[([ xX])\]\s*(.*)$",
            line,
        )

        if task_match:
            checked = (
                task_match.group(1).lower()
                == "x"
            )

            marker = "[x]" if checked else "[ ]"

            text = convert_inline_markdown(
                task_match.group(2)
            )

            output.append(
                f"* {marker} {text}"
            )
            continue

        bullet_match = re.match(
            r"^(\s*)-\s+(.*)$",
            line,
        )

        if bullet_match:
            indent = len(
                bullet_match.group(1)
            )

            depth = max(
                1,
                indent // 2 + 1,
            )

            stars = "*" * depth

            output.append(
                f"{stars} "
                f"{convert_inline_markdown(bullet_match.group(2))}"
            )
            continue

        numbered_match = re.match(
            r"^(\s*)\d+\.\s+(.*)$",
            line,
        )

        if numbered_match:
            indent = len(
                numbered_match.group(1)
            )

            depth = max(
                1,
                indent // 2 + 1,
            )

            hashes = "#" * depth

            output.append(
                f"{hashes} "
                f"{convert_inline_markdown(numbered_match.group(2))}"
            )
            continue

        if line.startswith("> "):
            output.append(
                "bq. "
                + convert_inline_markdown(
                    line[2:]
                )
            )
            continue

        if re.match(
            r"^[-*_]{3,}$",
            line.strip(),
        ):
            output.append("----")
            continue

        # Strip internal worklog comments.
        line = re.sub(
            r"\s*<!--.*?-->\s*",
            "",
            line,
        )

        output.append(
            convert_inline_markdown(
                line
            )
        )

    return "\n".join(output).strip() + "\n"


# ============================================================
# Jira draft management
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


def jira_text_path(
    markdown_path,
):
    return markdown_path.with_name(
        markdown_path.stem
        + ".jira.txt"
    )


def sync_jira_text(
    markdown_path,
):
    content = markdown_path.read_text(
        encoding="utf-8"
    )

    jira_content = markdown_to_jira(
        content
    )

    target = jira_text_path(
        markdown_path
    )

    target.write_text(
        jira_content,
        encoding="utf-8",
    )

    return target


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

    content = JIRA_TEMPLATES[
        ticket_type
    ](
        title
    )

    filename.write_text(
        content,
        encoding="utf-8",
    )

    jira_file = sync_jira_text(
        filename
    )

    print()
    print(
        "Created Jira "
        f"{JIRA_DISPLAY_NAMES[ticket_type]} draft:"
    )
    print(filename)

    print()
    print("Jira-ready text:")
    print(jira_file)
    print()


def interactive_jira():
    options = list(
        JIRA_DISPLAY_NAMES.items()
    )

    print()
    print("CREATE JIRA ITEM")
    print("=" * 40)
    print()

    for number, (
        _,
        display_name,
    ) in enumerate(
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
            number = int(choice)

            if 1 <= number <= len(options):
                break

        except ValueError:
            pass

        print(
            f"Choose 1-{len(options)}."
        )

    ticket_type = options[
        number - 1
    ][0]

    print()

    while True:
        title = input(
            "Title: "
        ).strip()

        if title:
            break

        print("A title is required.")

    create_jira_draft(
        ticket_type,
        title,
    )


# ============================================================
# Find / parse Jira drafts
# ============================================================

def latest_jira_markdown():
    files = list(
        JIRA_DIR.glob("*.md")
    )

    if not files:
        return None

    return max(
        files,
        key=lambda file: (
            file.stat().st_mtime
        ),
    )


def resolve_jira_draft(
    value=None,
):
    if value is None:
        file = latest_jira_markdown()

        if file is None:
            raise RuntimeError(
                "No Jira drafts found."
            )

        return file

    candidate = Path(value).expanduser()

    if not candidate.exists():
        candidate = (
            JIRA_DIR / value
        )

    # If .jira.txt was supplied,
    # prefer the associated Markdown file.
    if (
        candidate.name.endswith(
            ".jira.txt"
        )
    ):
        name = candidate.name[
            :-len(".jira.txt")
        ]

        markdown_candidate = (
            candidate.with_name(
                name + ".md"
            )
        )

        if markdown_candidate.exists():
            candidate = markdown_candidate

    if not candidate.exists():
        raise RuntimeError(
            f"Draft not found: {value}"
        )

    if candidate.suffix != ".md":
        raise RuntimeError(
            "jira-copy and jira-create "
            "expect a Markdown Jira draft."
        )

    return candidate


def parse_jira_draft(
    markdown_path,
):
    content = markdown_path.read_text(
        encoding="utf-8",
    )

    first_heading = None

    for line in content.splitlines():
        if line.startswith("# "):
            first_heading = line[2:].strip()
            break

    if not first_heading:
        raise RuntimeError(
            "Could not find Jira draft heading."
        )

    match = re.match(
        r"^(FEATURE|FLOW VALUE|"
        r"FLOW ACCELERATOR|FLOW DEFECT|"
        r"FLOW QUALITY):\s*(.+)$",
        first_heading,
        re.IGNORECASE,
    )

    if not match:
        raise RuntimeError(
            "The first heading does not identify "
            "a recognised Worklog Jira type."
        )

    heading_type = (
        match.group(1).upper()
    )

    title = match.group(2).strip()

    ticket_type = JIRA_HEADING_NAMES[
        heading_type
    ]

    return (
        ticket_type,
        title,
        content,
    )


def extract_section_first_value(
    markdown,
    section_name,
):
    lines = markdown.splitlines()

    heading = f"## {section_name}"

    found = False

    for line in lines:

        if line.strip() == heading:
            found = True
            continue

        if (
            found
            and line.startswith("## ")
        ):
            return None

        if found and line.strip():
            return line.strip()

    return None


# ============================================================
# Clipboard
# ============================================================

def copy_to_clipboard(text):
    commands = []

    if sys.platform == "darwin":
        commands = [
            ["pbcopy"],
        ]

    elif sys.platform.startswith(
        "win"
    ):
        commands = [
            ["clip"],
        ]

    else:
        commands = [
            ["wl-copy"],
            ["xclip", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--input"],
        ]

    for command in commands:

        if not shutil.which(
            command[0]
        ):
            continue

        process = subprocess.run(
            command,
            input=text,
            text=True,
            check=False,
        )

        if process.returncode == 0:
            return True

    return False


def jira_copy(
    draft=None,
):
    markdown_file = (
        resolve_jira_draft(draft)
    )

    jira_file = sync_jira_text(
        markdown_file
    )

    text = jira_file.read_text(
        encoding="utf-8"
    )

    if copy_to_clipboard(text):
        print(
            "Copied Jira-ready description "
            "to clipboard."
        )
        print(
            f"Source: {markdown_file}"
        )
    else:
        print(
            "No supported clipboard command "
            "was found."
        )
        print(
            f"Jira-ready text: {jira_file}"
        )


# ============================================================
# Jira REST configuration
# ============================================================

def jira_issue_type_name(
    ticket_type,
):
    env_name = (
        "JIRA_TYPE_"
        + ticket_type
        .upper()
        .replace("-", "_")
    )

    return os.environ.get(
        env_name,
        JIRA_DISPLAY_NAMES[
            ticket_type
        ],
    )


def load_json_environment(
    name,
):
    value = os.environ.get(
        name
    )

    if not value:
        return {}

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"{name} contains invalid JSON: "
            f"{error}"
        )

    if not isinstance(parsed, dict):
        raise RuntimeError(
            f"{name} must contain "
            "a JSON object."
        )

    return parsed


def jira_extra_fields(
    ticket_type,
):
    fields = {}

    fields.update(
        load_json_environment(
            "JIRA_EXTRA_FIELDS_JSON"
        )
    )

    suffix = (
        ticket_type
        .upper()
        .replace("-", "_")
    )

    fields.update(
        load_json_environment(
            f"JIRA_EXTRA_FIELDS_"
            f"{suffix}_JSON"
        )
    )

    return fields


def jira_auth_header():
    token = os.environ.get(
        "JIRA_TOKEN"
    )

    username = os.environ.get(
        "JIRA_USERNAME"
    )

    password = os.environ.get(
        "JIRA_PASSWORD"
    )

    auth_mode = os.environ.get(
        "JIRA_AUTH"
    )

    if auth_mode:
        auth_mode = (
            auth_mode.lower()
        )

    elif token:
        auth_mode = "pat"

    elif username and password:
        auth_mode = "basic"

    else:
        raise RuntimeError(
            "No Jira authentication configured.\n"
            "Set JIRA_TOKEN for PAT authentication "
            "or JIRA_USERNAME and JIRA_PASSWORD "
            "for basic authentication."
        )

    if auth_mode == "pat":

        if not token:
            raise RuntimeError(
                "JIRA_AUTH=pat requires "
                "JIRA_TOKEN."
            )

        return (
            "Authorization",
            f"Bearer {token}",
        )

    if auth_mode == "basic":

        if not username or not password:
            raise RuntimeError(
                "Basic authentication requires "
                "JIRA_USERNAME and JIRA_PASSWORD."
            )

        credentials = (
            f"{username}:{password}"
        )

        encoded = base64.b64encode(
            credentials.encode(
                "utf-8"
            )
        ).decode("ascii")

        return (
            "Authorization",
            f"Basic {encoded}",
        )

    raise RuntimeError(
        "JIRA_AUTH must be "
        "'pat' or 'basic'."
    )


def jira_ssl_context():
    ca_bundle = os.environ.get(
        "JIRA_CA_BUNDLE"
    )

    if ca_bundle:
        return ssl.create_default_context(
            cafile=ca_bundle
        )

    return ssl.create_default_context()


# ============================================================
# Jira creation
# ============================================================

def existing_jira_key(
    markdown,
):
    match = re.search(
        r"<!--\s*jira-created:"
        r"\s*([A-Z][A-Z0-9_]*-\d+)"
        r"\s*-->",
        markdown,
    )

    if match:
        return match.group(1)

    return None


def build_jira_payload(
    markdown_file,
):
    ticket_type, title, markdown = (
        parse_jira_draft(
            markdown_file
        )
    )

    project_key = os.environ.get(
        "JIRA_PROJECT_KEY"
    )

    if not project_key:
        raise RuntimeError(
            "JIRA_PROJECT_KEY is not set."
        )

    description = markdown_to_jira(
        markdown
    )

    fields = {
        "project": {
            "key": project_key,
        },
        "summary": title,
        "description": description,
        "issuetype": {
            "name": jira_issue_type_name(
                ticket_type
            ),
        },
    }

    # Optional common labels.
    labels = os.environ.get(
        "JIRA_LABELS"
    )

    if labels:
        fields["labels"] = [
            item.strip()
            for item in labels.split(",")
            if item.strip()
        ]

    # Optional company-specific custom fields.
    fields.update(
        jira_extra_fields(
            ticket_type
        )
    )

    # Optional Parent Feature custom field.
    #
    # Example:
    # JIRA_PARENT_FEATURE_FIELD=customfield_12345
    #
    parent_field = os.environ.get(
        "JIRA_PARENT_FEATURE_FIELD"
    )

    if parent_field:
        parent = (
            extract_section_first_value(
                markdown,
                "Parent Feature",
            )
        )

        if (
            parent
            and parent != "FEATURE-"
        ):
            fields[parent_field] = parent

    return {
        "fields": fields
    }


def record_created_issue(
    markdown_file,
    issue_key,
    issue_url,
):
    content = markdown_file.read_text(
        encoding="utf-8"
    )

    marker = (
        f"<!-- jira-created:"
        f"{issue_key} -->"
    )

    if marker in content:
        return

    addition = f"""

## Jira Issue

- Key: {issue_key}
- URL: {issue_url}

{marker}
"""

    markdown_file.write_text(
        content.rstrip()
        + "\n"
        + addition,
        encoding="utf-8",
    )

    sync_jira_text(
        markdown_file
    )


def jira_create(
    draft=None,
    dry_run=False,
    assume_yes=False,
    force=False,
):
    markdown_file = (
        resolve_jira_draft(
            draft
        )
    )

    ticket_type, title, markdown = (
        parse_jira_draft(
            markdown_file
        )
    )

    already_created = (
        existing_jira_key(
            markdown
        )
    )

    if (
        already_created
        and not force
    ):
        print(
            f"This draft was already created "
            f"as {already_created}."
        )
        print(
            "Use --force only if you "
            "intentionally want a duplicate."
        )
        return

    payload = build_jira_payload(
        markdown_file
    )

    base_url = os.environ.get(
        "JIRA_BASE_URL"
    )

    if not base_url:
        raise RuntimeError(
            "JIRA_BASE_URL is not set."
        )

    base_url = (
        base_url.rstrip("/")
    )

    endpoint = (
        f"{base_url}"
        "/rest/api/2/issue"
    )

    print()
    print("JIRA CREATE")
    print("=" * 60)
    print(
        "Type:    "
        f"{JIRA_DISPLAY_NAMES[ticket_type]}"
    )
    print(
        f"Summary: {title}"
    )
    print(
        "Project: "
        f"{payload['fields']['project']['key']}"
    )
    print(
        "Jira type: "
        f"{payload['fields']['issuetype']['name']}"
    )
    print(
        f"Draft:   {markdown_file}"
    )
    print(
        f"Server:  {base_url}"
    )
    print()

    if dry_run:
        safe_payload = payload.copy()

        print(
            json.dumps(
                safe_payload,
                indent=2,
            )
        )
        return

    if not assume_yes:
        answer = input(
            "Create this Jira issue? [y/N]: "
        ).strip().lower()

        if answer not in (
            "y",
            "yes",
        ):
            print("Cancelled.")
            return

    payload_bytes = json.dumps(
        payload
    ).encode("utf-8")

    auth_name, auth_value = (
        jira_auth_header()
    )

    request = urllib.request.Request(
        endpoint,
        data=payload_bytes,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            auth_name: auth_value,
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            context=jira_ssl_context(),
            timeout=30,
        ) as response:

            response_body = (
                response.read().decode(
                    "utf-8"
                )
            )

    except urllib.error.HTTPError as error:

        body = error.read().decode(
            "utf-8",
            errors="replace",
        )

        print(
            f"\nJira returned HTTP "
            f"{error.code}."
        )

        try:
            error_json = json.loads(
                body
            )

            print(
                json.dumps(
                    error_json,
                    indent=2,
                )
            )

        except json.JSONDecodeError:
            print(body)

        return

    except urllib.error.URLError as error:
        print(
            "\nUnable to connect to Jira:"
        )
        print(error.reason)
        return

    try:
        result = json.loads(
            response_body
        )

    except json.JSONDecodeError:
        print(
            "Jira returned an unexpected response:"
        )
        print(response_body)
        return

    issue_key = result.get(
        "key"
    )

    if not issue_key:
        print(
            "Issue may have been created, "
            "but Jira did not return a key."
        )
        print(result)
        return

    issue_url = (
        f"{base_url}/browse/"
        f"{issue_key}"
    )

    record_created_issue(
        markdown_file,
        issue_key,
        issue_url,
    )

    print()
    print("=" * 60)
    print(
        f"Created: {issue_key}"
    )
    print(issue_url)
    print("=" * 60)
    print()


# ============================================================
# CLI
# ============================================================

def main():
    ensure_directories()

    parser = argparse.ArgumentParser(
        prog="worklog",
        description=(
            "Local engineering and "
            "Product Owner worklog"
        ),
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    sub.add_parser(
        "init",
        help="Initialise worklog",
    )

    # Capture commands
    for command in SECTIONS:

        cmd = sub.add_parser(
            command,
            help=f"Add a {command}",
        )

        cmd.add_argument(
            "text",
            nargs="+",
        )

    # Views
    sub.add_parser(
        "today",
        help="Show today's worklog",
    )

    sub.add_parser(
        "open",
        help="Open today's worklog",
    )

    # Tasks
    sub.add_parser(
        "tasks",
        help="Show today's tasks",
    )

    done = sub.add_parser(
        "done",
        help="Complete an open task",
    )

    done.add_argument(
        "task_number",
        type=int,
    )

    undo = sub.add_parser(
        "undo",
        help="Reopen a completed task",
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
    )

    # Reports
    sub.add_parser(
        "week",
        help="Generate weekly summary",
    )

    # Search
    search = sub.add_parser(
        "search",
        help="Search worklogs",
    )

    search.add_argument(
        "query",
        nargs="+",
    )

    # Jira draft
    jira = sub.add_parser(
        "jira",
        help=(
            "Create Jira draft "
            "interactively or directly"
        ),
    )

    jira.add_argument(
        "ticket_type",
        nargs="?",
        choices=list(
            JIRA_DISPLAY_NAMES.keys()
        ),
    )

    jira.add_argument(
        "title",
        nargs="*",
    )

    # Jira copy
    jira_copy_parser = (
        sub.add_parser(
            "jira-copy",
            help=(
                "Convert the latest Jira "
                "draft and copy it "
                "to the clipboard"
            ),
        )
    )

    jira_copy_parser.add_argument(
        "draft",
        nargs="?",
    )

    # Jira create
    jira_create_parser = (
        sub.add_parser(
            "jira-create",
            help=(
                "Create a Jira issue from "
                "a Worklog Jira draft"
            ),
        )
    )

    jira_create_parser.add_argument(
        "draft",
        nargs="?",
    )

    jira_create_parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Show the payload without "
            "creating the issue"
        ),
    )

    jira_create_parser.add_argument(
        "--yes",
        action="store_true",
        help=(
            "Skip the confirmation prompt"
        ),
    )

    jira_create_parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Allow creation even if this "
            "draft was previously created"
        ),
    )

    args = parser.parse_args()

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
            args.all
        )

    elif args.command == "week":
        weekly_summary()

    elif args.command == "search":
        search_logs(
            " ".join(args.query)
        )

    elif args.command == "jira":

        if args.ticket_type is None:
            interactive_jira()

        else:
            title = " ".join(
                args.title
            ).strip()

            if not title:

                display = (
                    JIRA_DISPLAY_NAMES[
                        args.ticket_type
                    ]
                )

                print(
                    f"\nCreating {display}\n"
                )

                while not title:
                    title = input(
                        "Title: "
                    ).strip()

            create_jira_draft(
                args.ticket_type,
                title,
            )

    elif args.command == "jira-copy":
        jira_copy(
            args.draft
        )

    elif args.command == "jira-create":
        jira_create(
            draft=args.draft,
            dry_run=args.dry_run,
            assume_yes=args.yes,
            force=args.force,
        )


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)

    except RuntimeError as error:
        print(
            f"Error: {error}",
            file=sys.stderr,
        )
        sys.exit(1)