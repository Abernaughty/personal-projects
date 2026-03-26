# Git Commit Message Agent

An automated agent that scans your git repository, identifies branches with unpushed changes, and generates meaningful commit messages using Claude AI.

> Originally developed in [agent-dev](https://github.com/Abernaughty/agent-dev). Moved here as a standalone utility.

## Features

- Automatic branch scanning — finds all branches with unpushed commits
- AI-powered messages — generates conventional commit messages using Claude
- Staged changes support — works with `git add` workflow
- Interactive selection — choose which branch to process
- Auto-commit mode — generate and commit in one step
- Configurable via YAML config file
- JSON output for CI/CD integration

## Requirements

- Python 3.8+
- Git installed and accessible in PATH
- Anthropic API key

## Installation

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY='your-api-key-here'
```

## Usage

```bash
python git_commit_agent.py                    # Scan all branches
python git_commit_agent.py --staged           # Generate message for staged changes
python git_commit_agent.py --branch feature/x # Process specific branch
python git_commit_agent.py --staged --auto-commit  # Generate and commit
python git_commit_agent.py --json             # Output as JSON
```

See the full README at the original repo for detailed documentation, examples, and configuration options.
