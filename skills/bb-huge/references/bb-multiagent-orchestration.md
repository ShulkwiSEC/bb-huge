# bb-multiagent-orchestration — Coordinator/Subagent Dispatch Loop

This file extends `bb-orchestrator.md` (single-session skill routing) with a
pattern for splitting a hunt across **specialist subagents** instead of doing
every step in one linear session. It requires no extra LLM subscription —
every subagent dispatched here is a normal Claude Code subagent, running
inside your existing session.

Use this when: you have several independent items ready for the same kind of
work (e.g. three hypotheses awaiting validation) and want to fan them out in
parallel, or when you want a specialist's undivided attention on one item
instead of doing it inline.

Skip this when: you're doing a normal single-target hunt solo — the existing
SOPs in `SKILL.md` and `bb-orchestrator.md` are still the default path.

---

## Roles

- **Coordinator** — this session. The only role with MCP/portal access.
  Finds claimable work, dispatches subagents, writes results back.
- **Specialist subagents** — dispatched via the Agent tool with
  `subagent_type` set to one of the `bountyforge:*` agents already available
  in this install. They are analysis-only: they read/write local files and
  return a text result, but do **not** call bb-huge MCP tools themselves.
  The coordinator is always the one that persists state.

| kind (work-queue) | model | ready when | dispatch to |
|---|---|---|---|
| `triage` | Observation | `status == "open"` | `bountyforge:recon-agent` or `bountyforge:chain-builder` to enrich before deciding whether to promote |
| `validate` | Hypothesis | `status in (open, testing)` | `bountyforge:validator` |
| `report` | Finding | `status == "confirmed"` | `bountyforge:report-writer` |

---

## The Loop

```
1. bb_get_next_work_item(kind, program_id)
   -> {"kind": "...", "item": {...} | null}
   If item is null, there's nothing of that kind ready. Try another kind,
   or you're caught up.

2. bb_claim_work_item(kind, id, claimed_by="<your session identifier>")
   -> claims it so a parallel dispatch (or another session) won't also
      grab it. If it returns an "already claimed" error, someone beat you
      to it — go back to step 1.

   Repeat 1-2 to build a batch of independent claimed items before
   dispatching, if you want parallel fan-out.

3. Dispatch the matching subagent(s) via the Agent tool. For independent
   items, send multiple Agent tool calls in the SAME message so they run
   in parallel — do not dispatch them one message at a time.

   Give each subagent everything it needs in the prompt (it has no portal
   access): the item's fields from bb_get_next_work_item, relevant program
   context (bb_get_program_brief), and what you want back (a verdict for
   validate, a submission-ready draft for report, enrichment notes for
   triage). If the work involves authenticated requests, also call
   bb_get_session(program_id, label) yourself first and paste the returned
   cookies/headers into the subagent's prompt — see
   bb-browser-and-sessions.md. The subagent should never have to log in.

4. On subagent success, write the result back yourself using the normal
   MCP tools — the subagent never does this:
   - triage  -> bb_update_observation(...) then, if warranted,
               bb_promote_observation(id, ...)
   - validate -> if PASS: bb_promote_hypothesis(id, ...)
               if KILL: bb_update_hypothesis(id, status="rejected", ...)
               if DOWNGRADE: bb_update_hypothesis(id, severity_hint=..., ...)
               then bb_promote_hypothesis if still warranted
   - report  -> bb_update_finding(id, description=..., poc=...) with the
               drafted report content

   Writing back moves the record's `status` out of the ready-filter, so it
   naturally leaves the work queue — no separate "release" call needed on
   success.

5. On subagent failure or timeout:
   bb_release_work_item(kind, id)
   so the item goes back into the pool instead of being stuck claimed
   forever. Note what went wrong in the record via bb_add_note or
   bb_update_* before releasing, so the next attempt has context.
```

---

## Notes

- This is additive to the existing pipeline — the `status` fields and
  promote endpoints are unchanged. A validator subagent's verdict becomes a
  normal status update, exactly like a human hunter would do by hand.
- There is deliberately no hard gate blocking `status` transitions without
  a claim/validation having happened — that would contradict bb-huge's
  "capture first, enrich later" rule (see `bb-orchestrator.md`). The claim
  mechanism exists to prevent duplicate dispatch, not to police workflow.
- If a claimed item sits stale (claimed but no progress for a long time),
  just release it — there's no automatic expiry.
- Autonomous/scheduled coordinator runs (no human in the loop) are a
  separate, later capability — not covered here. This loop assumes a human
  is driving the coordinator session.
