# AGENT.md

> Process guide for working on Roadies-CityRide issues. Follow this workflow for every assignment.

## Overview

This project has a 50-assignment roadmap in `docs/assignments.md`. Each assignment is a GitHub Issue. The workflow is: pick an issue, implement it on a branch, open a PR, merge, close the issue, update the tracker.

---

## Step-by-Step Process

### 1. Pick an Issue

- Read `docs/assignments.md` to find the next available assignment.
- Read the GitHub Issue for full requirements.
- Check dependencies — some issues require earlier ones to be completed first.

### 2. Inspect the Repository

Before changing anything:

```bash
git status
git log --oneline -5
```

Read these files to understand current state:

- `README.md`
- `docs/architecture.md`
- `docs/assignments.md`
- `pyproject.toml`
- `src/roadies/config.py`
- Any files referenced by the issue

### 3. Create a Branch

Branch naming convention:

```
assignment/XX-short-name
```

Examples:
- `assignment/06-repository-structure`
- `assignment/07-python-uv-setup`
- `assignment/12-synthetic-dataset-generator`

```bash
git checkout -b assignment/XX-short-name
```

### 4. Implement the Changes

- Follow the issue requirements exactly.
- Keep changes focused — do not implement later assignments.
- Use existing project patterns (config, package structure, tests).
- Add dependencies with `uv add` (not manually editing pyproject.toml when possible).
- Run `uv sync` after any dependency change.

### 5. Validate

Always run before committing:

```bash
uv sync
uv run pytest
```

If the issue requires specific validation (e.g., generating a dataset, running a script), do that too.

### 6. Commit

Use a clear commit message:

```
feat: #XX short description
```

Examples:
- `feat: #6 design repository structure`
- `feat: #7 set up python project with uv`
- `feat: #12 build reproducible synthetic dataset generator`

### 7. Push and Open PR

```bash
git push -u origin assignment/XX-short-name
```

Open a PR with:

**Title:**
```
feat: #XX short description
```

**Body must include:**
- Assignment number and title
- What changed
- Validation results
- `Closes #XX` (this auto-closes the issue when merged)

PR body template:

```markdown
## Assignment
#XX — Assignment Title

## Objective
What this assignment accomplishes.

## Changes
- Bullet list of changes

## Validation
How you verified it works.

## Out of Scope
What this assignment did NOT cover.

Closes #XX
```

### 8. After Merge

Once the PR is merged:

1. Switch to main and pull:
   ```bash
   git checkout main
   git pull
   ```

2. Close the issue (if not auto-closed):
   ```bash
   gh issue close XX --repo kalviumcommunity/Roadies-CityRide --comment "Closed via PR #YY (merged)"
   ```

3. Update the tracker in `docs/assignments.md`:
   - Change status from `Available` to `Completed`
   - Add the PR link

4. Commit and push the tracker update:
   ```bash
   git add docs/assignments.md
   git commit -m "docs: mark assignment #XX as completed in tracker"
   git push
   ```

---

## Key Rules

1. **Do NOT implement later assignments.** Stay within the scope of the current issue.
2. **Always include `Closes #XX` in the PR body.** This auto-closes the issue on merge.
3. **Always update the tracker** after merge. Keep `docs/assignments.md` current.
4. **Always run tests** before committing. Never commit broken code.
5. **Do not modify unrelated files.** Keep changes focused.
6. **Use the project's config system** (`src/roadies/config.py`) for any settings.
7. **Keep dependencies minimal.** Only add what the current assignment needs.

---

## Project Structure Reference

```
Roadies-CityRide/
├── src/roadies/           # Python package
│   ├── config.py          # Configuration
│   ├── ingestion/         # Data loading/generation
│   ├── quality/           # Data cleaning
│   ├── features/          # Feature engineering
│   ├── analysis/          # Statistical analysis
│   ├── database/          # SQL integration
│   ├── visualization/     # Charts
│   └── pipeline/          # Orchestration
├── scripts/               # CLI entry points
├── tests/                 # Pytest tests
├── docs/                  # Documentation
├── sql/                   # SQL queries
├── notebooks/             # Jupyter notebooks
├── dashboard/             # Streamlit app
├── data/                  # Data directories
└── pyproject.toml         # Project config
```

---

## Common Commands

```bash
# Setup
uv sync

# Tests
uv run pytest
uv run pytest tests/test_file.py -v

# Generate dataset
uv run python scripts/generate_dataset.py

# Add dependency
uv add package-name
uv add --group dev package-name

# Git
git status
git diff
git add -A
git commit -m "feat: #XX description"
git push -u origin branch-name

# GitHub
gh issue close XX --repo kalviumcommunity/Roadies-CityRide --comment "Closed via PR #YY (merged)"
gh pr create --repo kalviumcommunity/Roadies-CityRide --title "feat: #XX ..." --body "..."
```

---

## Tracker Format

In `docs/assignments.md`, each assignment is a row:

```markdown
| XX | Assignment Title | [#XX](url) | Completed | — | [#YY](pr_url) |
```

Status values: `Available`, `In Progress`, `Completed`
