# QuantTrade project rules

## Scope and engineering

- This is the canonical QuantTrade repository, based on the QuantTradeSys source snapshot documented in `docs/consolidation/MERGE_PLAN.md`.
- Use Python 3.14 unless the project explicitly changes its supported version. Prefer type hints, small functions and pytest.
- Before changes, read the project description, relevant configuration and existing tests. Explain requirements, module/state boundaries, tradeoffs and verification before implementation.
- Reproduce defects where possible; inspect inputs, configuration, logs and the call chain before choosing a minimal fix. Reuse existing modules and dependencies; preserve unrelated user changes.
- API/CLI research execution shares `core/backtrader_runner.py`. Strategy class definitions are registered through `strategies/registry.py`. Imports must not start schedulers or place orders.
- Default tests use test doubles and synthetic data, with exchange networking prohibited. External sync, sandbox orders, live orders, publishing and pushes require authorization appropriate to the current task.
- Never commit keys, tokens, cookies, authentication files, databases or local runtime directories. Use environment variables or local secure storage. Verify exact targets before deletion, overwrite, migration or pushing, and prefer recoverable backups.

## Complete project-status synchronization contract

- For substantive progress, first update existing task/acceptance records in this project, then update root `PROJECT_STATUS.md`. Before delivery, check status, actual maintenance date, wording and evidence paths.
- The status file begins with YAML frontmatter without duplicate keys. Required keys: `project_id`, `updated`, `status`, `overview`, `progress`, `next`, `evidence`. `project_id` is the workspace-relative project path with `/` replaced by `-`; here it is `QuantTrade`. `updated` is an unquoted actual `YYYY-MM-DD` maintenance date. `overview`, `progress`, and `next` are nonempty strings.
- Allowed status values are `active`, `waiting`, `paused`, `unknown`. Use `active` for ongoing work; never `in_progress`. Tracking status does not mean feature/deployment acceptance. Use `unknown` when facts cannot be established.
- `evidence` is a nonempty list of existing project-relative files using `/`. Reject URLs, prose, absolute paths, traversal, hidden paths, self-reference, credentials, authentication files and runtime directories. Files under `runtime/`, `tmp/`, `temp/`, `logs/`, or `storage/logs/` are not canonical evidence.
- Record actual acceptance date, environment, results and unverified items in stable acceptance documents. Record test/deployment/URL/runtime observations there before citing them. Historical material must identify its source and cannot be represented as a current retest. Valid formatting, file existence and Git changes alone do not establish business completion.
- Keep this full synchronization contract in this project's own `AGENTS.md` so it remains effective outside the current workspace. Independent new projects need their own rules and summaries; examples and submodules normally belong to their containing project.
- Maintain only this project. Do not automatically write to an Obsidian vault, scan/register other projects, or access cross-project synchronization tools. Cross-project access and registration require explicit authorization for the current request; otherwise self-check this project without omitting status maintenance.
