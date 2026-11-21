# Wave Rules - standard process for every backend and web wave

Place at `docs/wave-rules.md` in Mediateappweb and Mediateappbackend-api. Every wave prompt says "follow docs/wave-rules.md". These rules add to rules.md; they never replace it.

## 1. Golden rules
- Everything is dynamic: business data, options, labels of data, counts, settings, designation names, action names, module names come from the backend API. No such value is hardcoded in the web or in application code. UI text (button labels, titles), layout, theme, route names and icons may stay in code.
- All initial data is seeded by the backend seed/ package: one file per seeder (seed_units.py style), config values in seed/data/*.json, registered in seed/seed_all.py, idempotent. Config seeds always run, synthetic dev seeds only with --dev.
- No real personal data anywhere (code, seeds, tests, docs). Development data is synthetic.
- Reuse before creating: existing tables, services, pages and components are extended, never duplicated.
- Never invent screens, fields or business meaning. When the reference screens were not seen, build only what our own docs define, mark it provisional, or stop and write the questions in docs/waiting-ui/<key>.md.

## 2. Stage 0: inspect first (no code changes)
Write docs/audit/<wave>-inspection.md: what already exists, what is missing, and a table "claim versus evidence" for anything an earlier summary said was done (page exists, API called, test or screenshot).

## 3. Build rules
- Only the scope of the wave. Do not start other features.
- Small files, one responsibility per file (web about 300 lines at most, backend about 200), full type hints and strict TypeScript without any, no print() or console.log, no duplicated logic, strings in one place.
- Every list: server-side pagination, search, loading, empty and error states. Every form: validation, friendly server errors, unsaved changes guard.
- Permissions on every endpoint and every page; data scope through core/scope.py; MANAGER and MR must be blocked where required.
- Every state change is audited through the single AuditService; soft delete only (BR-11).
- Stock, money and approvals use database transactions and are idempotent.

## 4. Seed rules
- Separate files, idempotent (run twice, nothing changes). Registered in seed_all.py in dependency order.
- Values that come from assumptions (not from the reference screens or our docs) are seeded with is_provisional = true and shown with a Provisional chip and a Confirm action.
- Stated minimums for the wave (for example 30 records) are checked by a script that fails below the minimum.

## 5. Verification protocol (mandatory before saying done)
Backend: ruff, mypy, pytest green; make seed-dev twice with no change; scripts/smoke_all_endpoints.py (every GET endpoint and every drill-down as ADMIN, MANAGER, MR on seeded data) with zero 500 and zero unexpected 403 or 404; role and scope tests; grep proof that nothing is hardcoded; self-review of the diff against rules.md; make openapi.
Web: lint, typecheck, vitest, build green; npm run check:static with zero violations; npm run smoke:routes (every route as ADMIN, plus MANAGER and MR for permissions: no blank page, console error, failed request or 5xx); grep proof of no hardcoded business values; screenshots of each new screen in docs/ui/<wave>/; self-review of the diff against rules.md.
Both: write docs/audit/<wave>-<backend or web>-verification.md with command outputs as evidence, assumptions and open questions; write docs/testing/<wave>-<backend or web>-test-guide.md (manual steps and expected results); update CHANGELOG, task.md and memory.md.

## 6. Reporting
- Say done only when every check passes. If something fails, say so, fix it and run the check again.
- Final message: a table with item, status (LIVE, PARTIAL, STUB, WAITING_UI, DECISION, DEFERRED), evidence file. LIVE means a real page, a real API, working for ADMIN, role checks done, and evidence.
- Open questions are listed, never guessed.

## 7. Status vocabulary
LIVE (built and proven), PARTIAL (works but a known part is missing), STUB (not built), WAITING_UI (needs the owner's screenshots), DECISION (needs an owner decision), DEFERRED (postponed on purpose).
