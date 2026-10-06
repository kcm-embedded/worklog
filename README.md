# Worklog

A lightweight, local Markdown-based worklog for engineers and Product Owners.

`worklog` is designed for environments where security restrictions make it difficult to use external productivity tools. It uses only the Python standard library and stores all data locally as plain Markdown files.

It can be used to:

- Capture daily thoughts and notes
- Track actions
- Mark actions as complete
- Carry unfinished actions into the next working day
- Record decisions
- Record risks and blockers
- Record follow-up items
- Generate weekly summaries
- Search historical worklogs
- Draft Jira Features
- Draft Flow Value items
- Draft Flow Accelerator items
- Draft Flow Defects
- Draft Flow Quality items

---

# Requirements

- Python 3.9 or later recommended
- No external Python packages are required
- macOS, Linux, or Windows

The script uses only the Python standard library.

---

# Installation

## 1. Save the script

Save the Python script somewhere convenient.

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

## 2. Make the script executable

On macOS or Linux:

```bash
chmod +x ~/bin/worklog
```

---

## 3. Add the directory to PATH

If `~/bin` is not already on your PATH, add this to your shell configuration.

For zsh:

```bash
export PATH="$HOME/bin:$PATH"
```

Add this to:

```text
~/.zshrc
```

Then reload your shell:

```bash
source ~/.zshrc
```

For bash, add the same line to:

```text
~/.bashrc
```

or:

```text
~/.bash_profile
```

You can verify the command is available with:

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

By default, Worklog stores its data in:

```text
~/worklog
```

The directory structure will look similar to:

```text
~/worklog/
├── daily/
│   └── 2026/
│       └── 10/
│           ├── 2026-10-05.md
│           └── 2026-10-06.md
└── jira-drafts/
```

You can change the storage location using the `WORKLOG_DIR` environment variable.

For example:

```bash
export WORKLOG_DIR="$HOME/Documents/worklog"
```

---

# Daily Workflow

A typical day might look like:

```bash
worklog carry
worklog tasks
```

Then throughout the day:

```bash
worklog note "Need to investigate startup sequence"

worklog task "Ask PM to confirm calibration requirements"

worklog decision "Keep ioctl interface for configuration"

worklog risk "Hardware availability could affect integration testing"

worklog followup "Discuss requirements at tomorrow's stand-up"
```

When an action is finished:

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

# Commands

## Help

Show available commands:

```bash
worklog --help
```

You can also show help for individual commands:

```bash
worklog jira --help
```

---

# Notes

Add a general thought or piece of information:

```bash
worklog note "ADF9084 startup sequence needs further investigation"
```

This is added to the `Thoughts` section of today's daily log.

Example:

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

This creates a Markdown checkbox:

```markdown
## Actions

- [ ] Review ADF9084 initialisation requirements
```

---

# View Tasks

Show today's open and completed actions:

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

Use the number shown by `worklog tasks`.

For example:

```bash
worklog done 2
```

This changes:

```markdown
- [ ] Review ADI startup sequence
```

to:

```markdown
- [x] Review ADI startup sequence
```

---

# Reopen an Action

If an action was completed accidentally:

```bash
worklog undo 1
```

The number refers to the completed task list shown by:

```bash
worklog tasks
```

---

# Carry Unfinished Work Forward

To carry unfinished actions from the most recent previous worklog into today:

```bash
worklog carry
```

For example, an unfinished Monday action:

```markdown
- [ ] Ask PM to confirm calibration requirement
```

is changed in Monday's log to:

```markdown
- [>] Ask PM to confirm calibration requirement <!-- carried-to:2026-10-06 -->
```

and today's log receives:

```markdown
- [ ] Ask PM to confirm calibration requirement <!-- from:2026-10-05 -->
```

This preserves the history of where the action originated.

## Carry All Outstanding Historical Actions

To find open actions across all previous logs and bring them into today:

```bash
worklog carry --all
```

Duplicate task text will not be copied into today's log multiple times.

---

# Decisions

Record an engineering, product, architecture, or process decision:

```bash
worklog decision "Use ioctl interface for device configuration"
```

Example:

```markdown
## Decisions

- Use ioctl interface for device configuration
```

This is useful for retaining lightweight decision history without needing a separate document for every small decision.

---

# Risks and Blockers

Record a risk or blocker:

```bash
worklog risk "Calibration acceptance criteria have not been defined"
```

Example:

```markdown
## Risks / Blockers

- Calibration acceptance criteria have not been defined
```

This can be useful for distinguishing technical progress from dependencies or unresolved Product decisions.

---

# Follow-up Items

Add something that needs to be revisited:

```bash
worklog followup "Raise calibration requirement at tomorrow's meeting"
```

Example:

```markdown
## Follow-up

- Raise calibration requirement at tomorrow's meeting
```

---

# View Today's Worklog

Print today's complete Markdown worklog:

```bash
worklog today
```

Example:

```markdown
# Tuesday 06 October 2026

## Thoughts

- Need to review ADI startup sequence

## Actions

- [ ] Ask PM for calibration requirements
- [x] Review SPI interface

## Decisions

- Keep ioctl configuration interface

## Risks / Blockers

- Hardware availability could affect integration

## Follow-up

- Discuss requirements tomorrow
```

---

# Open Today's Worklog

Open today's Markdown file using the configured/default editor:

```bash
worklog open
```

If the `EDITOR` environment variable is configured, Worklog will use it.

For example:

```bash
export EDITOR=vim
```

or:

```bash
export EDITOR=nvim
```

---

# Weekly Summary

Generate a summary for the current working week:

```bash
worklog week
```

Example:

```text
============================================================
WEEKLY WORKLOG
05 Oct 2026 -> 09 Oct 2026
============================================================

OPEN ACTIONS

Tue: Ask PM for calibration requirements

COMPLETED

Mon: Review SPI interface
Tue: Review ADI startup sequence

DECISIONS

Mon: Use ioctl for configuration

RISKS / BLOCKERS

Tue: Hardware availability could affect integration testing

FOLLOW-UP

Tue: Discuss calibration requirements with PM
```

This can be useful for:

- Weekly reviews
- Stand-up preparation
- PO status updates
- Engineering progress summaries
- Remembering what happened during the week
- Preparing for stakeholder meetings

---

# Search Historical Logs

Search all daily worklogs:

```bash
worklog search ADF9084
```

You can also search for phrases:

```bash
worklog search "calibration requirement"
```

Example output:

```text
SEARCH RESULTS: calibration requirement
============================================================

2026-10-05:12: - [>] Ask PM for calibration requirement
2026-10-06:7: - [ ] Ask PM for calibration requirement
```

---

# Jira Drafts

Worklog can create local Markdown drafts for Jira tickets.

Supported types are:

```text
Feature
Flow Value
Flow Accelerator
Flow Defect
Flow Quality
```

The drafts are stored in:

```text
~/worklog/jira-drafts/
```

The intent is to prepare and refine the ticket locally before entering it into Jira.

---

# Interactive Jira Creation

The easiest way to create a Jira draft is:

```bash
worklog jira
```

You will be shown:

```text
CREATE JIRA ITEM
========================================

1. Feature
2. Flow Value
3. Flow Accelerator
4. Flow Defect
5. Flow Quality

Type:
```

Choose a number.

For example:

```text
Type: 2
```

Then enter a title:

```text
Title: Implement ADF9084 initialisation
```

A Markdown draft will be created automatically.

---

# Create Jira Items Directly

You can bypass the interactive menu.

## Feature

```bash
worklog jira feature "ADF9084 Support"
```

Use a Feature for a larger capability or outcome.

A Feature should describe:

- The problem or opportunity
- Desired outcome
- Benefit hypothesis
- Scope
- Acceptance criteria
- Functional requirements
- Relevant non-functional requirements
- Dependencies
- Risks and unknowns
- Candidate Flow Items
- Verification strategy

---

## Flow Value

```bash
worklog jira flow-value "Implement ADF9084 device initialisation"
```

Use Flow Value for work that directly creates required product or system capability.

Examples:

```text
Implement ADF9084 device initialisation

Support runtime ADC configuration

Provide application interface for reading converter status
```

A Flow Value draft includes:

- Value / outcome
- Context
- Requirement
- Acceptance criteria
- Interfaces/components
- Technical context
- Dependencies
- Risks
- Verification
- Definition of Done

---

## Flow Accelerator

```bash
worklog jira flow-accelerator "Create reusable ADI device API wrapper"
```

Use Flow Accelerator for work that makes future delivery faster or removes constraints.

Examples:

```text
Create common SPI abstraction

Build reusable ADI API wrapper

Create hardware simulation environment

Automate firmware deployment to target hardware
```

The key question is:

> What future delivery becomes easier or faster because this work exists?

---

## Flow Defect

```bash
worklog jira flow-defect "ADF9084 fails to initialise after warm restart"
```

Use Flow Defect when existing behaviour is incorrect.

The template captures:

- Problem
- Expected behaviour
- Actual behaviour
- Reproduction steps
- Environment
- Impact
- Severity
- Root cause
- Fix
- Regression testing
- Verification

---

## Flow Quality

```bash
worklog jira flow-quality "Add automated ADF9084 register verification"
```

Use Flow Quality for work that improves engineering or product quality.

Examples include:

```text
Increase test coverage

Improve driver robustness

Reduce technical debt

Improve diagnostics

Improve static analysis results

Add automated integration testing

Improve documentation

Improve error handling
```

The template focuses on:

- Current quality state
- Desired quality state
- Quality criteria
- Evidence
- Verification
- Definition of Done

---

# Suggested Jira Structure

A typical Feature could be decomposed as:

```text
Feature: ADF9084 Support

├── Flow Value
│   ├── Initialise ADF9084 device
│   ├── Configure ADC paths
│   └── Expose converter status to application
│
├── Flow Accelerator
│   ├── Create common ADI API wrapper
│   └── Add reusable SPI test utilities
│
├── Flow Quality
│   ├── Add register configuration verification
│   └── Add automated startup testing
│
└── Flow Defect
    └── Fix initialisation failure following warm restart
```

The Feature represents the overall capability.

The Flow Items represent the independently understandable pieces of work required to deliver and sustain that capability.

---

# File Format

Worklog deliberately uses plain Markdown.

This means the files can be:

- Read in any text editor
- Opened in VS Code
- Opened in Vim/Neovim
- Searched using normal command-line tools
- Stored in Git if company policy allows
- Processed by Python
- Used by approved AI tooling where permitted
- Migrated later without proprietary export formats

No database is required.

---

# Example Daily File

```markdown
# Tuesday 06 October 2026

## Thoughts

- ADI API startup ordering needs further investigation
- Requirement around calibration behaviour is unclear

## Actions

- [x] Review SPI driver
- [ ] Ask PM for calibration acceptance criteria
- [ ] Create Flow Value for device initialisation

## Decisions

- Character-device architecture retained

## Risks / Blockers

- Calibration behaviour is not defined at Product level

## Follow-up

- Discuss calibration requirements at Wednesday meeting
```

---

# Recommended Daily Routine

## Start of Day

```bash
worklog carry
worklog tasks
```

This brings outstanding work forward and gives you a short list of today's actions.

---

## During the Day

Capture things immediately rather than trying to remember them:

```bash
worklog note "Need to check ADI API behaviour"

worklog task "Check AD9084 reset requirements"

worklog decision "Use existing SPI driver"

worklog risk "Hardware delivery may slip"

worklog followup "Ask systems team about reset sequence"
```

---

## Complete Work

```bash
worklog tasks
worklog done 2
```

---

## Create Jira Work

When a piece of work becomes substantial enough to track formally:

```bash
worklog jira
```

Draft it locally, refine it, then transfer it into Jira.

---

## End of Week

Run:

```bash
worklog week
```

Use the output to prepare:

- Team updates
- PO reviews
- Stakeholder updates
- Weekly reflections
- PI progress discussions

---

# Security Considerations

Worklog is intentionally local-first.

It does not:

- Connect to cloud services
- Call external APIs
- Send telemetry
- Upload notes
- Require an account
- Require third-party Python packages

However, the information stored by Worklog may still contain sensitive company information.

Follow your organisation's policies regarding:

- Storage locations
- Source-control repositories
- Backups
- Encryption
- Sensitive programme information
- Export-controlled information
- Customer information
- Security classifications

Do not automatically synchronise the Worklog directory to a personal cloud service unless your organisation explicitly permits it.

---

# Configuration

## Change Worklog Location

Set:

```bash
export WORKLOG_DIR="/path/to/worklog"
```

For example:

```bash
export WORKLOG_DIR="$HOME/Documents/worklog"
```

To make the setting permanent, add it to your shell configuration.

For zsh:

```bash
echo 'export WORKLOG_DIR="$HOME/Documents/worklog"' >> ~/.zshrc
```

Then:

```bash
source ~/.zshrc
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
    Record something requiring follow-up.

worklog tasks
    Display today's open and completed actions.

worklog done <number>
    Complete one of today's open actions.

worklog undo <number>
    Reopen one of today's completed actions.

worklog carry
    Carry open actions from the most recent previous log.

worklog carry --all
    Carry all outstanding historical actions into today.

worklog today
    Print today's worklog.

worklog open
    Open today's Markdown file.

worklog week
    Produce a weekly summary.

worklog search <query>
    Search historical worklogs.

worklog jira
    Open the interactive Jira item creator.

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
```

---

# Examples

```bash
# Start the day
worklog carry
worklog tasks

# Capture information
worklog note "Need to confirm JESD reset sequence"
worklog task "Speak to systems engineer"
worklog risk "Requirement remains undefined"

# Finish an action
worklog tasks
worklog done 1

# Record a decision
worklog decision "Use character-device interface"

# Create Jira work
worklog jira

# Search previous notes
worklog search JESD

# End-of-week review
worklog week
```

---

# Philosophy

Worklog is intentionally simple.

The daily log is your private working memory.

Jira remains the official record of planned engineering work.

The aim is not to duplicate Jira. The aim is to make it easier to capture incomplete thoughts, actions, decisions, risks, and emerging work before deciding what needs to become formal Jira work.

The workflow is:

```text
Thought
   ↓
Worklog
   ↓
Clarify
   ↓
Action / Decision / Risk
   ↓
Jira draft
   ↓
Feature / Flow Item
   ↓
Jira
```

This keeps everyday note-taking lightweight while still supporting structured Product Owner and engineering workflows.