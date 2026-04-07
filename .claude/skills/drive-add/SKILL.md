---
name: drive-add
description: "Add new game design with full pipeline: design GDD, review consistency, create stories, implement, and verify. User describes what to add, system drives the complete workflow until smoke-check passes."
argument-hint: "[new system/feature description, or 'status'/'reset']"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, WebSearch, Task, AskUserQuestion
---

# Drive Add — Add New Game Design Automation Pipeline

This skill automates the process of adding new systems, features, or content to
an existing game. The user describes what they want to add, and the system drives
through design, review, implementation, and verification.

The user only needs to say **yes** or **no** at each step.

---

## Arguments

- **(no argument)** — Start by asking the user what they want to add
- **`[feature description]`** — Start with the described addition intent
- **`status`** — Show current position without proposing anything
- **`reset`** — Discard session state and re-assess from scratch

---

## The Drive Loop

On each iteration, follow these four phases in order:

### Phase 1: Assess

Read the following files:

1. `production/session-state/drive-add-state.md` — session progress (if exists)
2. `production/session-state/active.md` — any active work context
3. `production/stage.txt` — current stage

Then scan current project state:

```
- design/gdd/game-concept.md          (game concept for context)
- design/gdd/systems-index.md         (existing systems and dependencies)
- design/gdd/*.md                      (all existing GDDs)
- design/art/art-bible.md              (art bible — style reference)
- docs/architecture/*.md              (existing ADRs)
- docs/architecture/control-manifest.md  (current manifest)
- production/sprints/*.md             (active sprint plans)
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

Update `production/session-state/drive-add-state.md`:

```markdown
# Drive-Add Session State

## Session Info
- Started: [ISO timestamp]
- Last Updated: [ISO timestamp]
- Addition Intent: [user's original description]

## New System
- Name: [system name]
- Dependencies: [list of existing systems it depends on]
- Depended By: [list of future systems that will depend on it]

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

### Phase 1: Intake and Integration Planning

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| A.1 | Collect addition intent | AskUserQuestion | Feature description | None |
| A.2 | Update systems index | `/map-systems` (incremental) | Updated `design/gdd/systems-index.md` | A.1 |

#### A.1: Collect Addition Intent

Use `AskUserQuestion` with a free-form question:

```
What new system or feature do you want to add? Describe:
- What should it do?
- How does it interact with existing systems?
- What's the player-facing experience?
```

If the user provided a feature description as an argument, skip this step.

#### A.2: Update Systems Index

Run `/map-systems` to integrate the new system into the dependency map. This
identifies:
- Which existing systems the new system depends on
- Where the new system fits in the design priority order
- Any immediate conflicts with existing system boundaries

### Phase 2: Design

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| A.3 | Design new system GDD (section-by-section) | `/design-system [new-system]` | New GDD in `design/gdd/` | A.2 |
| A.4 | Review new GDD quality | `/design-review [path]` | Review verdict | A.3 |
| A.4b | Generate asset specs for the new system | `/asset-spec system:[new-system]` | Specs in `design/assets/specs/` | A.4 APPROVED |
| A.5 | Create new ADR if needed | `/architecture-decision` | New ADR (if applicable) | A.4 |

For A.3: `/design-system` handles the full section-by-section authoring with
specialist delegation (same as normal GDD creation). The Drive-Add loop proposes
each section for approval, but `/design-system` manages the section-level flow.

For A.4: if design-review returns NEEDS REVISION or MAJOR REVISION:
1. Present the review findings
2. Propose targeted fixes (one at a time)
3. After fixes, re-propose the review
4. Do NOT proceed to A.5 until verdict is APPROVED

For A.5: use `AskUserQuestion` to determine if an ADR is needed:

```
Does this new system require an architectural decision?
Examples: new rendering approach, new data storage pattern, new networking model,
new input handling, new save/load strategy.

- Yes, create an ADR
- No ADR needed (standard pattern)
```

### Phase 3: Cross-System Validation

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| A.6 | Cross-GDD consistency check | `/consistency-check` | Conflict report | A.4 APPROVED |
| A.7 | Cross-GDD holistic review | `/review-all-gdds since-last-review` | Review report | A.6 |

For A.6: scan for conflicts between the new GDD and existing GDDs:
- Same entity with different stats
- Same formula with different variables
- Overlapping responsibilities
- Missing dependency references

If conflicts found: propose fixes, resolve each, re-run consistency check.

For A.7: run the holistic review focused on changes since the last review.
This catches system-level design issues that per-GDD review misses.

If the review-all-gdds report has MAJOR findings: propose addressing them
before proceeding. Minor findings can be noted for future sprints.

**Fast path**: If the new system is independent (no dependencies on existing
systems), A.6 and A.7 run quickly with minimal findings. Present results and
proceed without dwelling on them.

### Phase 4: Planning

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| A.8 | Create epic for the new system | `/create-epics` | Epic file | A.7 |
| A.9 | Break epic into stories | `/create-stories [epic-slug]` | Story files | A.8 |
| A.10 | Plan sprint for new stories | `/sprint-plan` | Sprint plan | A.9 |

For A.8: the new system becomes one or more epics. If the system is large,
`/create-epics` may split it into sub-modules.

For A.9: stories are created with embedded GDD requirements, ADR guidance,
and acceptance criteria. Use `/story-readiness` on the first story to validate
before proceeding.

For A.10: integrate the new stories into the current sprint, or create a new
sprint if the current one is full.

### Phase 5: Implementation (Sprint Cycle)

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| A.11 | Implement next story (loop) | `/dev-story [path]` or `team-*` | Code + tests | A.10 |
| A.11b | Produce art assets for new system (parallel) | delegate to `art-producer` | Art assets in `assets/art/` | A.11 (per story with visual needs) |
| A.12 | Accept each completed story | `/story-done [path]` | Story Complete | A.11, A.11b (per story) |

For A.11: read the sprint plan to identify stories for the new system. Propose
one story at a time. Use the appropriate `team-*` skill for cross-domain stories,
or `/dev-story` for single-domain stories.

For A.11b: after implementing a story with visual asset requirements, delegate
to `art-producer` to generate assets from the specs created in A.4b. This can
run in parallel with the next story's code implementation.

A.11/A.12 loop until all stories for the new system are complete.

### Phase 6: Verification

| ID | Action | Skill/Agent | Output | Prerequisite |
|----|--------|-------------|--------|--------------|
| A.13 | Content audit for new system | `/content-audit [system]` | Gap report | A.12 all done |
| A.14 | Smoke check | `/smoke-check` | PASS → **DONE** | A.13 |

For A.13: verify that what was designed in the GDD matches what was implemented.
If gaps are found, propose creating follow-up stories to fill them.

---

## Completion

When A.14 returns PASS, present:

```
=== Drive-Add Complete ===
New System: [system name]
Stories Implemented: [count]
Tests: [pass/fail summary]
Content Coverage: [planned vs implemented]

Suggested next steps:
- /drive-add [another system]       — add more features
- /drive-iterate [change to new system]  — tune the new system
- /review-all-gdds                  — full cross-GDD review
- /content-audit                    — broader content gap analysis
```

Write final state to drive-add-state.md with `Status: COMPLETE`.

---

## Special Modes

### Status Mode (`/drive-add status`)

Read `production/session-state/drive-add-state.md` and present:

```
=== Drive-Add Status ===
New System: [name]
Last Step: [ID and description]
Phase: [Intake / Design / Validation / Planning / Implementation / Verification]

Next Up: [what the next iteration would propose]
```

### Reset Mode (`/drive-add reset`)

Ask for confirmation, then delete `production/session-state/drive-add-state.md`
and restart from A.1.

---

## Edge Cases

### New System Depends on Unimplemented System

If the systems index shows the new system depends on another system that has a
GDD but no implementation:

1. Flag the dependency as unimplemented
2. Propose implementing the dependency first (start a new `/drive-add` for it)
3. Or propose adjusting the new system's design to remove the dependency
4. Do NOT proceed to implementation until dependencies are resolved

### New System Conflicts with Existing ADR

If the new system's design violates an existing Accepted ADR:

1. Flag the specific ADR and the conflict
2. Propose either: (a) revise the ADR via `/architecture-decision`, or
   (b) redesign the new system to comply
3. Do NOT proceed until the conflict is resolved

### Multiple New Systems at Once

If the user wants to add multiple related systems:

1. Run A.1-A.2 for all systems together (map them all)
2. Design them in dependency order (A.3-A.5 for each, deepest dependency first)
3. Run a single A.6/A.7 covering all new systems
4. Create epics for all systems (A.8-A.9)
5. Plan sprints to cover all (A.10)
6. Implement in dependency order (A.11-A.12)

### Adding Content to Existing System (Not New System)

If the user wants to add content (new levels, new items, new enemies) rather
than a new system:

1. Skip A.2 (no new system to map)
2. Use `/quick-design` instead of `/design-system` (A.3)
3. Skip A.5 (no new ADR needed for content)
4. Skip A.6/A.7 (consistency checks are lighter for content)
5. Go straight to A.8-A.14

Use `AskUserQuestion` to confirm: "This looks like content addition, not a new
system. Use the lighter content workflow?"

### User Interrupts with Free-Form Request

Handle the request, update state, resume the loop from Phase 1.

---

## Collaborative Protocol

1. **One step at a time** — never propose multiple actions
2. **Clear format** — always use the standardized proposal format
3. **User decides** — never auto-execute without approval
4. **Record everything** — update drive-add-state.md after every step
5. **Loop continuously** — after each step, immediately propose the next
6. **Respect "stop"** — exit the loop when the user says stop/pause/done
