# Worklog

A lightweight, local Markdown-based worklog for engineers and Product Owners.

`worklog` is designed for environments where security restrictions make it difficult to use external productivity tools.

It uses only the Python standard library for its core functionality and stores your working notes locally as plain Markdown files.

It can be used to:

- Capture daily thoughts
- Track actions
- Mark actions as complete
- Reopen completed actions
- Carry unfinished actions into a new day
- Record engineering and Product decisions
- Record risks and blockers
- Record follow-up items
- Generate weekly summaries
- Search historical worklogs
- Create Jira Feature drafts
- Create Flow Value drafts
- Create Flow Accelerator drafts
- Create Flow Defect drafts
- Create Flow Quality drafts
- Convert Markdown drafts into Jira wiki markup
- Copy Jira-ready descriptions to the clipboard
- Create Jira issues directly through the Jira Data Center REST API

---

# Philosophy

Worklog is deliberately simple.

The daily worklog is your personal working memory.

Jira remains the official system of record for planned and tracked engineering work.

The intended workflow is:

```text
Thought
   ↓
Worklog
   ↓
Clarify
   ↓
Action / Decision / Risk
   ↓
Jira Draft
   ↓
Review / Refine
   ↓
Feature / Flow Item
   ↓
Jira
```

Worklog should help capture incomplete thoughts without forcing everything immediately into Jira.

---

# Requirements

- Python 3.9 or later recommended
- No third-party Python packages required
- macOS, Linux or Windows
- Jira Data Center REST access if using `jira-create`

The script uses only the Python standard library.

Clipboard support depends on the operating system:

- macOS: `pbcopy`
- Windows: `clip`
- Linux: `wl-copy`, `xclip`, or `xsel`

---

# Installation

## 1. Save the script

Save the script somewhere on your PATH.

For example:

```text
~/bin/worklog
```

The `.py` extension is not required.

Make sure the first line of the script is:

```python
#!/usr/bin/env python3
```

---

## 2. Make it executable

On macOS or Linux:

```bash
chmod +x ~/bin/worklog
```

---

## 3. Add `~/bin` to your PATH

For zsh, add this to:

```text
~/.zshrc
```

```bash
export PATH="$HOME/bin:$PATH"
```

Then reload the shell:

```bash
source ~/.zshrc
```

For bash, add the same line to either:

```text
~/.bashrc
```

or:

```text
~/.bash_profile
```

Verify the installation:

```bash
which worklog
```

Example:

```text
/Users/username/bin/worklog
```

---

# Initial Setup

Run:

```bash
worklog init
```

By default, Worklog stores its files under:

```text
~/worklog
```

The structure will look like:

```text
~/worklog/
├── daily/
│   └── 2026/
│       └── 10/
│           ├── 2026-10-05.md
│           └── 2026-10-06.md
│
└── jira-drafts/
    ├── 20261006-101500-feature-adf9084-support.md
    ├── 20261006-101500-feature-adf9084-support.jira.txt
    ├── 20261006-103000-flow-value-device-initialisation.md
    └── 20261006-103000-flow-value-device-initialisation.jira.txt
```

---

# Change the Worklog Location

Set the `WORKLOG_DIR` environment variable:

```bash
export WORKLOG_DIR="$HOME/Documents/worklog"
```

To make this permanent with zsh:

```bash
echo 'export WORKLOG_DIR="$HOME/Documents/worklog"' >> ~/.zshrc
source ~/.zshrc
```

---

# Daily Workflow

A typical start to the day:

```bash
worklog carry
worklog tasks
```

During the day:

```bash
worklog note "Need to investigate ADF9084 startup behaviour"

worklog task "Ask PM for calibration requirements"

worklog decision "Keep ioctl interface for configuration"

worklog risk "Hardware availability may affect integration testing"

worklog followup "Discuss reset sequence at tomorrow's meeting"
```

When something is finished:

```bash
worklog done 1
```

At the end of the day:

```bash
worklog today
```

At the end of the week:

```bash
worklog week
```

---

# Command Reference

```text
worklog init
    Initialise the Worklog directories.

worklog note <text>
    Add a thought or note.

worklog task <text>
    Add an action.

worklog decision <text>
    Record a decision.

worklog risk <text>
    Record a risk or blocker.

worklog followup <text>
    Record a follow-up item.

worklog tasks
    Show today's open and completed actions.

worklog done <number>
    Mark an open action as complete.

worklog undo <number>
    Reopen a completed action.

worklog carry
    Carry unfinished actions from the most recent previous log.

worklog carry --all
    Carry unfinished actions from all historical logs.

worklog today
    Print today's complete worklog.

worklog open
    Open today's Markdown file.

worklog week
    Generate a weekly summary.

worklog search <query>
    Search historical daily logs.

worklog jira
    Open the interactive Jira draft creator.

worklog jira feature <title>
    Create a Feature draft.

worklog jira flow-value <title>
    Create a Flow Value draft.

worklog jira flow-accelerator <title>
    Create a Flow Accelerator draft.

worklog jira flow-defect <title>
    Create a Flow Defect draft.

worklog jira flow-quality <title>
    Create a Flow Quality draft.

worklog jira-copy
    Convert the latest Jira Markdown draft into Jira wiki markup
    and copy it to the clipboard.

worklog jira-copy <draft>
    Convert and copy a specific Jira draft.

worklog jira-create
    Create a Jira issue from the latest Jira draft.

worklog jira-create <draft>
    Create a Jira issue from a specific Jira draft.

worklog jira-create --dry-run
    Show the REST payload without creating anything.

worklog jira-create --yes
    Create the issue without asking for confirmation.

worklog jira-create --force
    Allow creation even if the draft was already used
    to create a Jira issue.
```

---

# Notes

Add a general thought:

```bash
worklog note "ADF9084 startup sequence needs further investigation"
```

Produces:

```markdown
## Thoughts

- ADF9084 startup sequence needs further investigation
```

---

# Actions

Add an action:

```bash
worklog task "Review ADF9084 initialisation requirements"
```

Produces:

```markdown
## Actions

- [ ] Review ADF9084 initialisation requirements
```

---

# View Tasks

Run:

```bash
worklog tasks
```

Example:

```text
TODAY'S TASKS
============================================================

OPEN
1. Ask PM for calibration requirements
2. Review ADI startup sequence

COMPLETED
1. Review SPI interface
```

---

# Complete an Action

Use the number shown by `worklog tasks`:

```bash
worklog done 2
```

Changes:

```markdown
- [ ] Review ADI startup sequence
```

to:

```markdown
- [x] Review ADI startup sequence
```

---

# Reopen an Action

If a task was completed accidentally:

```bash
worklog undo 1
```

The number refers to the completed-task section displayed by:

```bash
worklog tasks
```

---

# Carry Unfinished Actions Forward

Run:

```bash
worklog carry
```

This takes open actions from the most recent previous worklog and adds them to today's log.

For example:

```markdown
- [ ] Ask PM to confirm calibration requirement
```

becomes this in the original file:

```markdown
- [>] Ask PM to confirm calibration requirement <!-- carried-to:2026-10-06 -->
```

and this is added to today's file:

```markdown
- [ ] Ask PM to confirm calibration requirement <!-- from:2026-10-05 -->
```

This preserves the history of where an action originated.

To carry open actions from all historical logs:

```bash
worklog carry --all
```

Worklog avoids carrying duplicate task text into today's log.

---

# Decisions

Record a decision:

```bash
worklog decision "Use ioctl interface for device configuration"
```

Produces:

```markdown
## Decisions

- Use ioctl interface for device configuration
```

This provides a lightweight historical record of engineering, Product, or architectural decisions.

---

# Risks and Blockers

Record a risk:

```bash
worklog risk "Calibration acceptance criteria have not been defined"
```
