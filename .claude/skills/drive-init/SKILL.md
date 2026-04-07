---
name: drive-init
description: "Full automation pipeline from empty project to playable demo. Configures engine, designs systems, builds architecture, runs sprints, and exits when Production gate passes. User only approves each step."
argument-hint: "[optional: 'status' to see current position, 'reset' to restart]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, WebSearch, Task, AskUserQuestion
---

# Drive Init — Zero to Demo Automation Pipeline

This skill automates the entire journey from an empty project to a playable demo.
It follows the Drive Loop pattern: **Assess → Propose → Execute → Record**, looping
until the Production gate passes (smoke-check PASS + gate-check PASS).

The user only needs to say **yes** or **no** at each step.

---

## Arguments

- **(no argument)** — Start or continue the Drive-Init Loop
- **`status`** — Show current position without proposing anything
- **`reset`** — Discard session state and re-assess from scratch

---

## The Drive Loop

On each iteration, follow these four phases in order:

### Phase 1: Assess

Read the following files (in order):

1. `production/session-state/drive-init-state.md` — session progress (if exists)
2. `production/session-state/active.md` — any active work context
3. `production/stage.txt` — current stage (if exists)

Then scan key artifacts:

```
- CLAUDE.md                        (engine configured?)
- .claude/docs/technical-preferences.md  (preferences set?)
- design/gdd/game-concept.md       (concept exists?)
- design/gdd/game-pillars.md       (pillars defined?)
- design/art/art-bible.md          (art bible defined?)
- design/gdd/systems-index.md      (systems mapped?)
- design/gdd/*.md                  (list all GDD files)
- design/assets/specs/*.md         (asset specifications?)
- design/assets/asset-manifest.md  (asset manifest?)
- assets/art/                      (produced art assets?)
- docs/architecture/*.md           (ADR count)
- docs/architecture/control-manifest.md  (manifest exists?)
- prototypes/*/REPORT.md           (prototype reports)
- production/sprints/*.md          (sprint plans)
- production/milestones/*.md       (milestone definitions)
- src/                             (file count, directory structure)
- tests/                           (test files)
```

Determine the current position in the Workflow Map below by finding the first
step whose expected output artifact is missing.

### Phase 2: Propose

Present ONE proposed action:

```
=== Next Step: [Step ID] ===
Action: [Clear, specific description]
Delegates to: [/skill-name or agent-name]
Why now: [What exists and what's missing]
Expected output: [What artifact this produces]
```

Then use `AskUserQuestion`:

- **Yes, proceed** — execute this step
- **Not now** — defer, move to next step
- **Skip** — permanently skip this step
- **Why this step?** — explain reasoning, then re-ask

### Phase 3: Execute

When the user approves:

- **For skills**: Use the Skill tool with `skill: "[name]", args: "[arguments]"`
- **For agents**: Use the Task tool with `subagent_type: "[agent-name]"` and a
  detailed prompt including file paths, design doc references, and constraints
- Wait for completion
- Verify the expected output artifact was created (read or glob for it)
- If the artifact is missing, flag the step as incomplete

### Phase 4: Record

After execution, update `production/session-state/drive-init-state.md`:

```markdown
# Drive-Init Session State

## Session Info
- Started: [ISO timestamp]
- Last Updated: [ISO timestamp]

## Current Position
- Step ID: [last completed step ID]
- Next Step: [what the next iteration should propose]

## Steps Completed
1. [Step ID] [description] — [result: done / skipped / deferred]

## Notes
- [any user decisions affecting future steps]
```

Then **loop back to Phase 1**.

---

## Workflow Map

### Phase 1: Foundation

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| I.1 | Configure engine and preferences | `/setup-engine` | Updated CLAUDE.md, technical-preferences | None |
| I.2 | Brainstorm game concept | `/brainstorm` | `design/gdd/game-concept.md` | I.1 |
| I.3 | Review concept quality | `/design-review design/gdd/game-concept.md` | Review verdict | I.2 |
| I.3b | Create art bible | `/art-bible` | `design/art/art-bible.md` | I.3 |
| I.4 | Gate: Concept → Systems Design | `/gate-check systems-design` | PASS | I.3b |

### Phase 2: Systems Design

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| I.5 | Map all systems and dependencies | `/map-systems` | `design/gdd/systems-index.md` | I.4 PASS |
| I.6 | Design next system GDD (loop per system) | `/design-system [system]` | Individual GDD in `design/gdd/` | I.5 |
| I.7 | Design-review each completed GDD | `/design-review [path]` | Review verdict | I.6 (per system) |
| I.8 | Gate: Systems Design → Technical Setup | `/gate-check technical-setup` | PASS | All I.6/I.7 done |

For I.6: read `design/gdd/systems-index.md` to find which systems need GDDs.
Design them in the priority order specified by the systems index. This step
loops — propose one system at a time, get approval, execute, then propose the
next system.

### Phase 3: Technical Architecture

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| I.9 | Create master architecture document | `/create-architecture` | Architecture doc in `docs/architecture/` | I.8 PASS |
| I.10 | Create ADRs for core systems (loop) | `/architecture-decision` | ADRs in `docs/architecture/` | I.9 |
| I.11 | Architecture review and traceability | `/architecture-review` | TR-registry + review | I.10 |
| I.12 | Create control manifest | `/create-control-manifest` | `docs/architecture/control-manifest.md` | I.11 |
| I.12b | Generate asset specs for MVP systems | `/asset-spec system:[system]` (loop per MVP system) | Specs in `design/assets/specs/` | I.12 |
| I.13 | Gate: Technical Setup → Pre-Production | `/gate-check pre-production` | PASS | I.12b |

For I.10: create ADRs for architecturally significant systems only (rendering,
data management, networking, core loop). Not every system needs an ADR. Read
the systems index and architecture doc to determine which systems need ADRs.

For I.12b: read the systems index to find MVP systems. Run `/asset-spec` for
each MVP system that has visual requirements. This loops — one system at a time.
Only generate specs for systems whose GDDs have a Visual/Audio Requirements section.

For I.20b: after a story is implemented via I.20, check if the story has visual
asset requirements. If yes, delegate to `art-producer` to generate assets from
the spec. This runs in parallel with the next story's implementation.

### Phase 4: Pre-Production

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| I.14 | Prototype core mechanic | `/prototype [core-mechanic]` | Prototype + report in `prototypes/` | I.13 PASS |
| I.15 | Playtest report for prototype | `/playtest-report` | Playtest report | I.14 |
| I.16 | Go/no-go decision | delegate to `creative-director` | Decision documented | I.15 |
| I.17 | Create first milestone | delegate to `producer` | Milestone in `production/milestones/` | I.16 go |
| I.18 | Plan first sprint | `/sprint-plan new` | Sprint plan in `production/sprints/` | I.17 |
| I.19 | Gate: Pre-Production → Production | `/gate-check production` | PASS | I.18 |

If I.16 returns "no-go": propose pivoting the prototype or redesigning the core
mechanic. Loop back to I.14 with adjusted parameters.

### Phase 5: Production (Sprint Cycle)

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| I.20 | Implement sprint tasks (one at a time) | `/dev-story [path]` or `team-*` | Code + tests | I.19 PASS |
| I.20b | Produce art assets for implemented stories (parallel) | delegate to `art-producer` | Art assets in `assets/art/` | I.20 (per story with visual needs) |
| I.21 | Accept each completed story | `/story-done [path]` | Story Complete | I.20, I.20b (per task) |
| I.22 | Sprint retrospective | `/retrospective` | Retro findings | Sprint done |
| I.23 | Plan next sprint (if core loop incomplete) | `/sprint-plan` | Sprint plan | I.22 |
| I.24 | Smoke check (when core loop complete) | `/smoke-check` | PASS | All sprints done |
| I.25 | Gate: Production → Polish | `/gate-check polish` | PASS → **DONE** | I.24 PASS |

For I.20: read the sprint plan to identify tasks. Propose one task at a time.
Use the appropriate `team-*` skill for cross-domain tasks, or `/dev-story` for
single-domain tasks.

I.23 loops back to I.20 until the core game loop is fully playable and all MVP
systems are implemented. When the sprint plan shows no remaining MVP stories,
proceed to I.24.

---

## Completion

When I.25 returns PASS, present:

```
=== Drive-Init Complete ===
Demo is ready: core loop playable, all MVP systems implemented, smoke-check passed.

Suggested next steps:
- /drive-add [new-system]     — add new features beyond MVP
- /drive-iterate [change]     — tune or modify existing systems
- /gate-check polish          — advance to polish phase
- /playtest-report            — run a full playtest session
```

Write final state to drive-init-state.md with `Status: COMPLETE`.

---

## Special Modes

### Status Mode (`/drive-init status`)

Read `production/session-state/drive-init-state.md` and present:

```
=== Drive-Init Status ===
Last Step: [ID and description]
Steps Completed: [N] / 25
Current Phase: [Foundation / Systems Design / Technical Architecture / Pre-Production / Production]

Next Up: [what the next iteration would propose]
```

### Reset Mode (`/drive-init reset`)

Ask for confirmation, then delete `production/session-state/drive-init-state.md`
and re-assess from scratch.

---

## Edge Cases

### Empty Project

The most common starting point. Auto-detect as Step I.1, propose `/setup-engine`.

### Gate Check Fails

If any `/gate-check` returns FAIL:
1. Read the gate check output to identify which items failed
2. Propose targeted fix steps (one at a time)
3. After fixes, re-propose the gate check
4. Do NOT advance until PASS is achieved

### User Interrupts with Free-Form Request

If the user types a request that's not a yes/no answer:
1. Handle their request directly or delegate to the appropriate agent/skill
2. After handling, update drive-init-state.md
3. Resume the Drive Loop from Phase 1

### Step Dependencies Not Met

If a step's prerequisite is marked as skipped or deferred:
1. Warn the user that the prerequisite was not completed
2. Offer to go back and complete it, or proceed with acknowledged risk
3. Record the decision in drive-init-state.md

### Context Window Pressure

If the conversation is getting long:
1. Ensure drive-init-state.md is fully up to date
2. Suggest the user run `/compact Focus on Drive-Init — state is in production/session-state/drive-init-state.md`
3. After compaction, the loop will read state file to recover

---

## Collaborative Protocol

1. **One step at a time** — never propose multiple actions
2. **Clear format** — always use the standardized proposal format
3. **User decides** — never auto-execute without approval
4. **Record everything** — update drive-init-state.md after every step
5. **Loop continuously** — after each step, immediately propose the next
6. **Respect "stop"** — exit the loop when the user says stop/pause/done
