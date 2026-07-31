# Skill Change Approval Gate

This gate applies when changing the official local V4 Skill repository itself. It does not gate ordinary project edits made from an already-approved Skill.

## Non-negotiable order

1. Keep the official Skill tree at its sealed baseline.
2. Create a scoped change request before implementation.
3. For a visual or semantic change, build stills or short motion previews in an isolated copy. Do not edit the official Skill yet.
4. Show every materially different style, color, layout, copy, routing, motion, or component behavior to the user.
5. Record approval only after the user explicitly confirms those preview artifacts.
6. Apply only the approved scope to the official Skill.
7. Seal the implementation, run the gate verification, then run the format regression suite.
8. Finalize the new baseline only after the approved implementation and both required format suites pass.
9. Git commit and push still require separate explicit authorization. Approval of a sample is not approval to commit, push, deploy, or change the other format.

`structural-nonvisual` is limited to changes that cannot alter rendered pixels, spoken meaning, routing, timing, layout, motion, audio, or output behavior. It still requires explicit user confirmation, but it does not require a preview artifact. If there is uncertainty, classify the change as `visual-semantic`.

## Commands

Create a request while the official tree still matches the sealed baseline:

```powershell
python scripts/skill_change_approval_gate.py create `
  --change-id <stable-id> `
  --change-class visual-semantic `
  --summary "What will change" `
  --scope references/visual-system.md `
  --scope assets/remotion-template/src/components
```

After the user explicitly approves the shown files:

```powershell
python scripts/skill_change_approval_gate.py approve `
  --confirmation "Exact concise user confirmation" `
  --sample C:\absolute\path\approved-still.png `
  --sample C:\absolute\path\approved-motion.mp4
```

Apply the approved change, then bind the official implementation to the approval:

```powershell
python scripts/skill_change_approval_gate.py seal
python scripts/skill_change_approval_gate.py verify
python scripts/run_skill_regression.py
```

After verification and all required format tests pass:

```powershell
python scripts/skill_change_approval_gate.py finalize
python scripts/skill_change_approval_gate.py verify
```

The active request and archived evidence live under `qa/skill-change-approval/`, which is intentionally local and ignored by Git. The repository-level `.skill-change-gate.json` stores only the sealed protected-tree fingerprint and policy metadata; it contains no media or account credentials.

## Failure behavior

The gate fails when:

- the Skill tree changes before a request is created;
- a visual/semantic request has no approved still or motion preview;
- an approved preview is missing or its bytes have changed;
- implementation touches a file outside the declared scope;
- implementation changes after it is sealed;
- a request was created against an obsolete baseline;
- regression runs while the official tree is neither at baseline nor at an approved sealed state.

Never repair a failure by editing `.skill-change-gate.json` or the active approval JSON manually. Return to the last sealed state or create a fresh request after resolving the active one.
