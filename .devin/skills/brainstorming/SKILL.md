---
name: brainstorming
description: Use when starting any new feature or project to refine ideas into designs before writing code
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design and get user approval.

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## The Process

### 1. Understand Context

First, understand the current state of the project:
- What exists already?
- What are the constraints?
- What patterns does this codebase follow?

### 2. Ask Questions

Ask questions ONE AT A TIME to refine the idea:
- What problem are we solving?
- Who is the user?
- What are the must-haves vs nice-to-haves?
- Are there existing patterns to follow?

Don't ask all questions at once. Wait for answers before proceeding.

### 3. Present Design

Once you understand the requirements, present a design document that includes:

```markdown
# [Feature Name] Design Document

## Problem Statement
[What are we solving?]

## Solution Overview
[High-level approach]

## Key Decisions
[Architecture choices and why]

## Implementation Notes
[Specific technical details]

## Open Questions
[Anything still to resolve]
```

Present the design section by section for validation.

### 4. Get Approval

**Wait for explicit approval before proceeding.**

User responses like:
- "Yes, that's right"
- "Approved"
- "Let's do it"
- "Looks good"

Are approval signals. Anything else means continue discussion.

## After the Design

Once approved, save the design to:
```
docs/superpowers/plans/YYYY-MM-DD-<feature-name>-design.md
```

Then use `writing-plans` skill to break this into implementation tasks.

## Key Principles

- **No code before design** - Hard gate, no exceptions
- **One question at a time** - Don't overwhelm with questions
- **Present in sections** - Don't dump the whole design at once
- **Wait for approval** - Don't proceed until explicitly cleared
