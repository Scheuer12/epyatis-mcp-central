## Problem

What problem does this change solve? Link the related issue when one exists.

## Approach

Describe the implementation and the important trade-offs.

## Verification

List the exact commands executed and their results. Do not mark checks that were not run.

- [ ] Relevant regression tests added or updated
- [ ] `python -m pytest -p no:cacheprovider tests/test_security_*.py -q`
- [ ] `ruff check --no-cache src tests`
- [ ] `bandit -q -r src/central -ll`
- [ ] Documentation updated when behavior/configuration changed

## Security and compatibility

- Does this change affect authentication, authorization, secrets, networking, subprocesses, persistence or MCP compatibility?
- Does it introduce a migration or rollback requirement?
- Were any checks intentionally not run? Why?

## Contributor checklist

- [ ] The change is focused and does not include unrelated rewrites.
- [ ] No credentials, private data, local databases, logs or backups are included.
- [ ] I understand and can explain submitted code, including AI-assisted code.
- [ ] I have read `CONTRIBUTING.md` and agree to follow `CODE_OF_CONDUCT.md`.

