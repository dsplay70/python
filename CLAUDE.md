# CLAUDE.md

## Project Overview

A minimal Python project using core data-science libraries (NumPy, Pandas, Matplotlib). The entry point is `main.py`.

## Repository Structure

```
.
├── main.py              # Application entry point
├── requirements.txt     # pip dependencies
├── venv/                # Python virtual environment (not committed)
└── CLAUDE.md            # This file
```

## Development Environment

- **Python version**: 3.11
- **Virtual environment**: `venv/` (created via `python -m venv venv`)
- **Package manager**: pip with `requirements.txt`

### Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running

```bash
python main.py
```

## Dependencies

Defined in `requirements.txt` (unpinned):
- `numpy`
- `pandas`
- `matplotlib`

## Key Conventions

- No build system, linter, or test framework is configured yet.
- No `.gitignore` is present — avoid committing `venv/`, `__pycache__/`, or `.pyc` files.
- The `venv/` directory should never be committed.

## Git

- **Primary branch**: `main` (remote) / `master` (local)
- Single initial commit so far.
- No CI/CD pipelines configured.
- No pre-commit hooks.
