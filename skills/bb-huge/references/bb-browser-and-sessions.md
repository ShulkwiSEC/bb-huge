# bb-browser-and-sessions — Real Browser Navigation + Session Ownership

Two capability gaps this file fixes, observed across prior hunting sessions:
1. The agent only ever tested the **unauthenticated** surface — no way to
   establish or reuse a login, so it never reached IDOR/BOLA/privilege-
   escalation-class bugs that live behind auth.
2. The agent discovered endpoints by curl-fetching raw HTML/JS and
   regexing paths out of (often minified/obfuscated) bundles — slow and
   lossy compared to watching what a real browser actually loads.

Neither fix requires building a browser or an HTML/JS parser. Both use
tools that already exist.

---

## Part 1 — Navigation: use browsermcp, not curl

`browsermcp` is a real, Chrome-backed browser automation MCP. When
connected, its tools are: `browser_navigate`, `browser_click`,
`browser_type`, `browser_snapshot` (accessibility-tree/DOM view),
`browser_screenshot`, `browser_get_console_logs`, `browser_hover`,
`browser_select_option`, `browser_press_key`, `browser_go_back`,
`browser_go_forward`, `browser_wait`.

**Default to browsermcp over curl for exploring the live site.** The
browser executes the JS itself — no reverse-engineering obfuscated bundles
to guess routes. Navigate, take a snapshot, click through the visible
flows, and read the rendered structure directly.

**What browsermcp does NOT give you**: raw HTTP request/response pairs. It
has no cookie/localStorage export tool and no JS-eval tool. It cannot hand
you something replayable via curl, and it can't read `HttpOnly` cookies
(nothing client-side can — that's the point of the flag). For that, see
Part 2.

If browsermcp is not connected in your current session, curl remains the
fallback for the unauthenticated/static parts of a hunt — but authenticated
testing depends on Part 2 regardless of whether browsermcp is available.

---

## Part 2 — Session ownership: HAR export/import

**The problem this solves**: some agent, subagent, or curl command needs a
real authenticated session to test anything behind login. Handling login
itself (forms, MFA, OAuth redirects, CSRF) is exactly the kind of thing a
scripted flow is bad at and a real browser is good at. So: do the login
once, in a real browser, and let everyone else reuse the result.

### The one-time capture step

1. Log into the target **once**, normally — via browsermcp, or your own
   browser if browsermcp isn't connected. Use whatever test account/role
   you want to capture (see labels below for multi-account testing).
2. Export a HAR: Chrome DevTools → Network tab → right-click → "Save all
   as HAR with content". This is one button, not an ongoing process.
3. Run the importer:
   ```bash
   python skills/bb-huge/scripts/bb-import-har.py capture.har \
       --program-id <id> --label user_a
   ```
   This does two things in one pass:
   - Files every non-static request/response pair as an `EvidenceRecord`
     (`evidence_type=http_exchange`) — real endpoints, not guesses.
   - Extracts the freshest cookies + auth-relevant headers
     (`Authorization`, CSRF tokens) for the target host and saves them as
     an `AuthSession` under the given label.

Running this script *is* what makes you the session owner — there's no
separate role to invoke.

### Multi-account testing (labels)

Cross-account IDOR/BOLA testing (log in as A, try to access B's data using
A's session) is one of the highest-value things this unlocks. Capture each
identity under its own label:
```bash
python skills/bb-huge/scripts/bb-import-har.py user_a.har --program-id 3 --label user_a
python skills/bb-huge/scripts/bb-import-har.py user_b.har --program-id 3 --label user_b
python skills/bb-huge/scripts/bb-import-har.py admin.har  --program-id 3 --label admin
```
Each label is a separate row — re-importing the same label refreshes it in
place rather than creating duplicates.

### Consuming a session (every other agent's job)

Any subagent or curl-based test — never handling login itself — calls:
```
bb_get_session(program_id=3, label="user_a")
-> {"cookies": {...}, "headers": {...}, "auth_type": "cookie", "status": "active", ...}
```
and attaches the returned cookies/headers to its own curl requests. That's
the entire integration surface. No login flow, no MFA, no CSRF handling —
all of that was already solved once by whoever ran the importer.

### When a session goes stale

If a request comes back 401 or redirected to a login page, don't try to
re-authenticate programmatically. Instead:
```
bb_update_session(id=<session_id>, status="invalid")
```
and report back to the coordinator that label needs a fresh HAR import.
The browser (human-like login flow) handles re-auth far more reliably than
scripting it would.

---

## Notes

- No always-on proxy/traffic-capture daemon is used here (an earlier design
  considered `mitmproxy` running continuously; rejected as overbuilt for
  this phase — HAR export/import covers the need with far less
  infrastructure).
- This is additive to existing evidence/portal conventions — sessions and
  evidence use the same `account_label`/`auth_type` fields the portal
  already had.
- See `bb-multiagent-orchestration.md` for how a dispatched subagent should
  be briefed to call `bb_get_session` before making authenticated requests.
