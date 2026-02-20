---
name: post-implementation-commit
description: Git commit workflow for this repository. Use when a new feature or code change has been implemented and the task should end with staging the whole project (`git add .`) and creating a commit that follows Conventional Commits v1.0.0.
---

# Post Implementation Commit

Use this skill when implementation work is done and the user expects a commit.

## Required workflow

1. Verify what changed:
- Run `git status --short`.
- Run `git diff --stat`.

2. Pick Conventional Commit type from the actual change:
- `feat`: new functionality
- `fix`: bug fix
- `refactor`: code change without behavior change
- `perf`: performance improvement
- `test`: adding/updating tests
- `docs`: documentation-only changes
- `build`: build system or dependency changes
- `ci`: CI/CD changes
- `chore`: maintenance tasks not fitting the above

3. Create commit message in Conventional Commits format:
- Format: `<type>(<optional-scope>): <description>`
- Use imperative, concise description.
- Optional body can explain motivation and key changes.

4. Stage and commit:
- Run `git add .` (entire project, as requested).
- Run `git commit -m "<conventional-commit-subject>"`.

## Safety checks

- Do not amend commits unless user explicitly asks.
- If there are unrelated or unexpected changes, stop and ask the user before committing.
- If there are no staged changes after `git add .`, report that no commit was created.

## Example subjects

- `feat(api): add async training generation endpoint`
- `fix(frontend): handle empty exercise list state`
- `docs(readme): update local backend startup steps`
