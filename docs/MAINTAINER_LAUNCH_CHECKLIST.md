# Maintainer launch checklist

Use this checklist before broadly announcing the repository. It contains repository and GitHub-host settings that cannot be guaranteed by source changes alone.

## Credential and history safety

- [ ] Rotate the integration credential exposed during the local audit.
- [ ] Rotate every historical/example admin or encryption secret that may have been used outside disposable development.
- [ ] Run an approved secret scanner over the current tree and full Git history.
- [ ] Inspect old CI logs, release artifacts, database files and backup folders separately.
- [ ] Decide whether history rewriting is required and coordinate it before inviting contributors.
- [ ] Confirm `.env`, OAuth files, databases, logs and `backups/` are not tracked.

## Repository state

- [ ] Review and commit the hardening/community changes intentionally.
- [ ] Confirm the default branch is `main` and the remote contains the intended commit.
- [ ] Run the security test gate from a clean clone.
- [ ] Confirm both GitHub Actions workflows pass remotely.
- [ ] Confirm README links, badges and issue forms render correctly on GitHub.
- [ ] Keep the project classified as a development preview; do not publish a stable release from this state.

## GitHub settings

- [ ] Enable Issues.
- [ ] Enable private vulnerability reporting and repository security advisories.
- [ ] Protect `main` with required CI checks and at least one review when collaboration volume permits.
- [ ] Prevent force pushes and branch deletion on `main`.
- [ ] Enable Dependabot alerts/updates or document the chosen dependency-update process.
- [ ] Create initial labels such as `good first issue`, `help wanted`, `documentation`, `security`, `testing`, `architecture` and `needs triage`.
- [ ] Convert bounded roadmap work into issues with explicit acceptance criteria.
- [ ] Mark at least two genuinely bounded tasks as `good first issue`; do not use the label for architecture-critical work.

## Community operations

- [ ] Decide who will triage issues and review pull requests.
- [ ] Set realistic expectations for response time; no SLA is currently promised.
- [ ] Use public issues/PRs for ordinary decisions and private channels only for security, credentials, personal data or conduct reports.
- [ ] Prepare the announcement with an explicit statement that the tool is under construction and contributors are welcome.
- [ ] Link the announcement directly to `README.md`, `ROADMAP.md` and `CONTRIBUTING.md`.

## Suggested announcement facts

Safe claims supported by the repository:

- open-source MCP/OpenAPI control-plane experiment;
- development preview being built in public;
- 33 isolated security regression tests currently passing locally;
- contributions welcome in testing, network security, frontend hardening, MCP compatibility, migrations, documentation and developer experience;
- not production-ready and not approved for public-internet deployment.

Avoid claims such as “secure”, “enterprise-ready”, “production-ready”, “fully multi-tenant”, “certified” or “compatible with every MCP client”.

