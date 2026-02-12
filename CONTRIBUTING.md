# Contributing to envlit

Thank you for your interest in contributing to **envlit**, a tool for scalar field visualization using Polyscope.
This document outlines the minimal steps to set up a development environment, coding standards, and contribution guidelines.

---

## Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/luocfprime/envlit.git
   cd envlit
   ```

2. Install dependencies and pre-commit hooks:
   ```bash
   make install
   ```

---

## Tasks

The project uses `make` with `uv` for environment management and reproducibility. Some useful commands:

- **Install pre-commit**"
  ```bash
  pre-commit install
  ```

- **Format code**
  ```bash
  make format
  ```

- **Run quality checks (lint, type checks, lock validation)**
  ```bash
  make check
  ```

- **Run tests**
  ```bash
  make test
  ```

- **Build distribution**
  ```bash
  make build
  ```

- **Serve documentation**
  ```bash
  make docs
  ```

For a full list of tasks, run:
```bash
make help
```

---

## Guidelines

- Use `ruff` for linting and formatting.
- Ensure type annotations are correct; `mypy` is enforced.
- Write tests with `pytest` for new features and bug fixes.
- Update documentation (`docs/` via MkDocs) if behavior changes.
- Commit messages should be concise and descriptive in English, with a clear title.

---

## Pull Requests

- Keep changes focused and reasonably small.
- Ensure all checks (format, lint, tests) pass before submitting.
- Link relevant issues if applicable.

---

## Issues

Please use [GitHub Issues](https://github.com/luocfprime/envlit/issues) for bug reports, feature requests, or questions.
Include system details and reproduction steps where appropriate.

---

## License

Contributions are accepted under the [MIT License](LICENSE).
