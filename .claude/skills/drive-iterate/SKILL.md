---
name: drive-iterate
description: "Modify existing game design with automatic impact analysis. User describes the change, system auto-classifies severity (minor/moderate/major), executes the right workflow, and verifies nothing broke. Loops until smoke-check passes."
argument-hint: "[change description, or 'status'/'reset']"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, WebSearch, Task, AskUserQuestion
---

# Drive Iterate — Modify Game Design Automation Pipeline

This skill automates the process of modifying existing game design. The user
describes what they want to change, the system analyzes impact, auto-classifies
the change severity, and drives through the appropriate workflow until everything
is verified.

The user only needs to say **yes** or **no** at each step.

---

## Arguments

- **(no argument)** — Start by asking the user what they want to change
- **`[change description]`** — Start with the described change intent
- **`status`** — Show current position without proposing anything
- **`reset`** — Discard session state and re-assess from scratch

---

## The Drive Loop

On each iteration, follow these four phases in order:

### Phase 1: Assess

Read the following files:

1. `production/session-state/drive-iterate-state.md` — session progress (if exists)
2. `production/session-state/active.md` — any active work context
3. `production/stage.txt` — current stage

Then scan current project state:

```
- design/gdd/*.md                  (all GDD files — what systems exist)
- design/gdd/systems-index.md      (system dependency map)
- design/art/art-bible.md          (art bible — style reference)
- design/assets/specs/*.md         (existing asset specifications)
- design/assets/asset-manifest.md  (current asset inventory)
- docs/architecture/*.md           (all ADRs)
- docs/architecture/control-manifest.md  (current manifest)
- src/                             (current code)
- tests/                           (current tests)
- assets/data/                     (data/config files)
- design/quick-specs/              (existing quick specs)
```

### Phase 2: Propose

Present ONE proposed action:

```
=== Next Step: [Step ID] ===
Action: [Clear, specific description]
Delegates to: [/skill-name or agent-name]
Why now: [What the analysis found and why this is next]
Expected output: [What artifact this produces]
```

Then use `AskUserQuestion`:

- **Yes, proceed** — execute this step
- **Not now** — defer
- **Skip** — permanently skip
- **Why this step?** — explain reasoning

### Phase 3: Execute

Delegate to the appropriate skill or agent, wait for completion, verify output.

### Phase 4: Record

Update `production/session-state/drive-iterate-state.md`:

```markdown
# Drive-Iterate Session State

## Session Info
- Started: [ISO timestamp]
- Last Updated: [ISO timestamp]
- Change Intent: [user's original description]

## Impact Analysis
- Systems Affected: [list]
- ADRs Affected: [list]
- Change Level: [minor / moderate / major]

## Current Position
- Step ID: [last completed step ID]
- Next Step: [what the next iteration should propose]

## Steps Completed
1. [Step ID] [description] — [result]

## Notes
- [decisions, overrides, etc.]
```

Then **loop back to Phase 1**.

---

## Workflow Map

### Phase 1: Intake and Analysis

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| M.1 | Collect change intent | AskUserQuestion | Change description | None |
| M.2 | Scope analysis | `/scope-check` | Scope report | M.1 |
| M.3 | Auto-classify change level | Internal logic (see below) | LEVEL: minor/moderate/major | M.2 |
| M.4 | Impact analysis | `/propagate-design-change` | Change impact report | M.3 |

#### M.1: Collect Change Intent

Use `AskUserQuestion` with a free-form question:

```
What do you want to change? Describe the modification:
- Which system(s) are affected?
- What should work differently?
- What's the motivation (balance, fun, feasibility)?
```

If the user provided a change description as an argument, skip this step and
use the argument directly.

#### M.3: Auto-Classify Change Level

Read the change description and scan affected files to determine the level:

| Level | Indicators | Examples |
|-------|-----------|---------|
| **minor** | Only data/config values change; no rule changes; no new entities | Damage 10→15, spawn rate 0.5→0.3, max inventory 64→99 |
| **moderate** | Rules/mechanics change within one system; formulas change; new edge cases | Stamina regen formula changed, new status effect added, crafting recipe rework |
| **major** | System interactions change; new/removed systems; core loop modified; multiple GDDs affected | Combat-overhaul affects stamina+inventory+UI, removing crafting entirely, adding multiplayer |

**Always present the auto-classified level to the user with an option to override.**
Use `AskUserQuestion`:

```
=== Change Level: [auto-classified level] ===
Reasoning: [why this level was chosen]

Keep this level, or adjust?
- Yes, this is correct
- Treat as minor instead
- Treat as moderate instead
- Treat as major instead
```

#### M.4: Impact Analysis

- **minor level**: Skip propagate-design-change. Present a brief summary of
  which files will be touched. Proceed to M.5a.
- **moderate level**: Run `/propagate-design-change` on the affected GDD.
  Present the impact report. Proceed to M.5b.
- **major level**: Run `/propagate-design-change` on all affected GDDs.
  Present the full impact report. Proceed to M.5c.

### Phase 2: Design Change (branching by level)

#### Minor Path

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| M.5a | Quick design spec | `/quick-design [desc]` | `design/quick-specs/[name]-[date].md` | M.4 |

#### Moderate Path

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| M.5b | Update existing GDD | `/design-system [system]` (update mode) | Updated GDD | M.4 |
| M.6b | Review updated GDD | `/design-review [path]` | Review verdict | M.5b |

If design-review returns NEEDS REVISION or MAJOR REVISION: propose fix steps
based on the review feedback, then re-run M.5b.

#### Major Path

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| M.5c | Rewrite affected GDD(s) (loop) | `/design-system [system]` | Updated GDDs | M.4 |
| M.6c | New ADR(s) if architecture changed | `/architecture-decision` | New ADRs | M.5c |
| M.7c | Review updated GDD(s) | `/design-review [path]` | Review verdicts | M.5c |

For M.5c: rewrite one GDD at a time, in dependency order (systems that are
depended on first).

### Phase 3: Consistency and Propagation

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| M.8 | Cross-GDD consistency check | `/consistency-check` | Conflict report | M.5a/b/c done |
| M.9 | Update affected ADRs and Stories | `/propagate-design-change` | Updated docs | M.8 |

If consistency-check finds conflicts: propose fixes for each conflict, then
re-run consistency-check.

For minor changes: M.8 and M.9 are optional. Use `AskUserQuestion`:

```
This is a minor change. Run full consistency and propagation checks?
- Yes, run both
- Consistency check only
- Skip both (quick change)
```

### Phase 4: Implementation

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| M.10 | Implement code changes (loop per task) | `/dev-story [path]` or `team-*` | Code + tests | M.9 (or M.5a for minor) |
| M.10b | Update asset specs if visual content changed | `/asset-spec [system]` | Updated specs in `design/assets/specs/` | M.5b or M.5c (moderate/major only) |
| M.10c | Regenerate affected art assets | delegate to `art-producer` | Updated art in `assets/art/` | M.10b |
| M.11 | Accept each completed story | `/story-done [path]` | Story Complete | M.10, M.10c (per task) |

For M.10: if the change doesn't have existing stories, use `AskUserQuestion` to
confirm creating quick stories. For minor changes, the implementation may be
small enough to handle directly without full story workflow.

For M.10b: only runs for moderate/major changes that modify visual requirements.
Check if the change touches the Visual/Audio section of any GDD. If not, skip.
Use `AskUserQuestion`: "This change affects visual content. Update asset specs?"

For M.10c: only runs if M.10b produced updated specs. Delegates to `art-producer`
to regenerate affected assets. Can run in parallel with M.11 for other stories.

### Phase 5: Verification

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| M.12 | Regression test | `/regression-suite` | Coverage report | M.11 |
| M.13 | Balance check (if data/formulas changed) | `/balance-check [system]` | Balance report | M.11 |
| M.14 | Smoke check | `/smoke-check` | PASS → **DONE** | M.12, M.13 |

For minor changes: M.12 and M.13 are optional. Use `AskUserQuestion`:

```
This is a minor change. Run full verification suite?
- Yes, run regression + balance + smoke
- Smoke check only
- Skip all verification
```

For moderate/major: M.12 and M.14 are required. M.13 runs if the change
affected formulas or balance data.

---

## Completion

When M.14 returns PASS (or user skips verification for minor changes), present:

```
=== Drive-Iterate Complete ===
Change: [original description]
Level: [minor/moderate/major]
Files modified: [count]
Tests: [pass/fail summary]

Suggested next steps:
- /drive-iterate [another change]  — make another modification
- /drive-add [new-system]         — add new features
- /smoke-check                    — run a broader smoke test
```

Write final state to drive-iterate-state.md with `Status: COMPLETE`.

---

## Special Modes

### Status Mode (`/drive-iterate status`)

Read `production/session-state/drive-iterate-state.md` and present:

```
=== Drive-Iterate Status ===
Change: [description]
Level: [minor/moderate/major]
Last Step: [ID and description]
Phase: [Analysis / Design / Consistency / Implementation / Verification]

Next Up: [what the next iteration would propose]
```

### Reset Mode (`/drive-iterate reset`)

Ask for confirmation, then delete `production/session-state/drive-iterate-state.md`
and restart from M.1.

---

## Edge Cases

### Change Affects Multiple Systems

When the impact analysis reveals multiple systems are affected:
1. List all affected systems
2. Propose changes in dependency order
3. After each system's GDD is updated, re-run consistency check
4. Present cumulative impact before proceeding to implementation

### Change Contradicts Existing ADR

If the change would violate an Accepted ADR:
1. Flag the conflict explicitly
2. Propose either: (a) revise the ADR via `/architecture-decision`, or
   (b) adjust the change to comply with the ADR
3. Do NOT proceed until the conflict is resolved

### Scope Creep Detected

If during the workflow, the change grows beyond its classified level:
1. Re-run M.3 classification
2. Present the escalation to the user
3. If user agrees, switch to the higher level's workflow path
4. Record the escalation in the state file

### No Existing Stories for the Change

If the change is not covered by existing stories:
1. For minor: implement directly (no stories needed)
2. For moderate/major: propose creating stories via `/quick-design` or a
   focused planning step before M.10
3. Use `AskUserQuestion` to confirm the approach

### User Interrupts with Free-Form Request

Handle the request, update state, resume the loop from Phase 1.

---

## Collaborative Protocol

1. **One step at a time** — never propose multiple actions
2. **Clear format** — always use the standardized proposal format
3. **User decides** — never auto-execute without approval
4. **Record everything** — update drive-iterate-state.md after every step
5. **Loop continuously** — after each step, immediately propose the next
6. **Respect "stop"** — exit the loop when the user says stop/pause/done
