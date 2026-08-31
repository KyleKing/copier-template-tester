# Agent guidelines

## Commands

- `./run main` runs the default gates: lint, auto-format, and test coverage
- `./run lint.fix test` fixes lint findings and runs the tests
- `./run --help` lists every available calcipy task
- `uv run pytest tests -k <pattern>` runs a subset directly when that is faster

Run `./run main` before reporting work as done.

## Layout

- Source lives in `copier_template_tester/` and tests under `tests/`
- Docs live in `docs/docs/` and build with mkdocs

## Conventions

- Python runs through uv (`uv run <tool>`).
    Never install tools globally for this project
- ruff formats and lints, and mypy and pyright must both pass
- Commit messages follow Conventional Commits and commitizen bumps versions from them

This file is template-owned and `copier update` keeps it current.
Put project-specific guidance in `AGENTS.local.md` (loaded below when present) or in a
nested `AGENTS.md` scoped to its directory.

@AGENTS.local.md
