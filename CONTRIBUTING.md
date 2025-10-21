# Contributing to Micro-Consent-Pipeline

We welcome contributions! Thank you for taking the time to help improve this project.

## Getting Started

1. Fork the repository and clone your fork.
2. Create a feature branch:

```bash
git checkout -b feat/my-feature
```

3. Make your changes, write tests, and run the test suite locally.

## Code Style

- Follow PEP8 and idiomatic Python.
- Use `black` for formatting and `isort` for import sorting.
- Add or update unit tests for new logic or bug fixes.

## Commit Messages

Please use Conventional Commits:

- `feat:` - A new feature
- `fix:` - A bug fix
- `docs:` - Documentation only changes
- `style:` - Code style changes (no functional change)
- `refactor:` - Refactoring without adding features or fixing bugs
- `perf:` - Performance improvements
- `test:` - Adding or fixing tests
- `chore:` - Maintenance tasks

Example:

```bash
git commit -m "feat: add async job processing for privacy scans"
```

## Branching & PRs

- Target `main` for release-ready PRs.
- Use `develop` if you'd like to accumulate changes between releases.
- Make small, focused PRs with a clear description of changes.
- Tag your PR with one of: `semver:patch`, `semver:minor`, or `semver:major` to indicate the intended version bump.

## Release Labels

We use a small set of GitHub labels to drive automatic semantic version bumps and to help triage PRs. The recommended labels are:

- `semver:patch` — Backwards-compatible bug fixes
- `semver:minor` — New backwards-compatible features
- `semver:major` — Breaking changes that require a major version bump

You can create these labels automatically with the included script:

```bash
bash scripts/create_labels.sh owner/repo
```

This requires the `gh` (GitHub CLI) tool and an authenticated session (for CI, set GITHUB_TOKEN). The script will attempt to read the repo from the `origin` remote if you don't provide one.

## Tests

Run the full test suite locally before opening a PR:

```bash
pytest -v
```

## Review Process

- At least one maintainer must review and approve your PR.
- Address feedback promptly and keep the PR up-to-date with the target branch.

## Contributor License Agreement

By contributing to this project, you agree that your contributions will be licensed under the project's LICENSE (MIT) unless otherwise specified.

## Further Help

See [SUPPORT.md](SUPPORT.md) for details on how to get help and report issues.

Thank you for contributing!
