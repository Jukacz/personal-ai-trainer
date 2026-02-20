---
name: project-rules-core
description: Core project conventions for AI Personal Trainer. Use when changing architecture, dependencies, environment setup, build/run/test commands, or shared coding standards across backend and frontend so implementation stays consistent and documentation stays current.
---

# Project Rules Core

Follow these global rules for every non-trivial change in this repository.

## Read full baseline

Load `references/claude-rules.md` when you need full project context (tech stack, architecture assumptions, and command baseline).

## Keep docs in sync

Always update `README.md` after project-wide changes, especially when modifying:

- Build process or Docker configuration
- Environment variables
- Project structure
- Tech stack versions
- Startup commands
- Major services or dependencies

## Use standard commands

Use these canonical commands unless the user asks otherwise:

- Setup venv: `python -m venv venv && source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Run app: `python main.py`
- Tests: `pytest`
- Formatting/linting: `black .` or `ruff check . --fix`

## Enforce code quality baseline

For Python and LangChain code:

- Follow PEP 8.
- Use type hints for functions and important variables.
- Prefer LCEL (`|`) over legacy Chain classes.
- Keep concerns split into modules:
  - `tools/` for external integrations and helpers
  - `prompts/` for prompt templates
  - `database/` for persistence logic

## Preserve runtime conventions

- Work inside virtual environment.
- For Google Calendar changes, document required OAuth scopes and credential paths.
- Persist conversation state to SQLite after each interaction.
- Add unit tests for tools and integration tests for LangChain flows.
