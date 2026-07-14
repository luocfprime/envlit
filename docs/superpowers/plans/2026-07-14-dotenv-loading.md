# Dotenv Loading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow `.envlit/*.yaml` profiles to explicitly load one or more dotenv files with deterministic precedence, safe override warnings, atomic errors, and normal envlit restoration.

**Architecture:** Extend `envlit.config` with a focused dotenv parsing layer that converts `python-dotenv` parser bindings into sourced environment entries. Recursively resolve configuration as ordered layers—parent, local dotenv files, then local YAML env—while retaining source labels only during resolution. Return the existing normalized config shape so script generation and state tracking remain unchanged.

**Tech Stack:** Python 3.10+, PyYAML, python-dotenv, Click, pytest, uv, Ruff, mypy

---

## File Structure

- Modify `envlit/config.py`: warning classes, dotenv shape/path validation, atomic parsing, sourced env merging, and recursive inheritance resolution.
- Modify `tests/test_config.py`: unit coverage for parsing, paths, precedence, inheritance, warnings, and failure behavior.
- Modify `tests/test_cli.py`: prove warnings use stderr, failures emit no script, and generated output is sourceable.
- Modify `pyproject.toml` and `uv.lock`: add and lock `python-dotenv` runtime dependency.
- Modify `README.md`, `docs/index.md`, `docs/index.zh.md`, and `skills/envlit/SKILL.md`: document the public YAML syntax and precedence.

### Task 1: Dependency and Atomic Dotenv Parsing

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `envlit/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Add failing parser tests**

Add tests demonstrating the desired internal/public behavior through `load_config()`:

```python
def test_loads_single_dotenv_relative_to_config(tmp_path):
    (tmp_path / ".env").write_text("API_URL=https://example.test\nEMPTY=\n")
    config_file = tmp_path / "default.yaml"
    config_file.write_text('dotenv: "./.env"\n')
    config = load_config(str(config_file))
    assert config["env"] == {"API_URL": "https://example.test", "EMPTY": ""}


def test_malformed_dotenv_fails_atomically(tmp_path):
    (tmp_path / ".env").write_text('GOOD=value\nBROKEN="unterminated\n')
    config_file = tmp_path / "default.yaml"
    config_file.write_text('dotenv: "./.env"\n')
    with pytest.raises(ValueError, match=r"\.env.*line 2"):
        load_config(str(config_file))
```

Also cover an absolute path, `${VAR}` preservation, `KEY=` as empty string, and `KEY` without `=` being ignored with `ConfigDotenvWarning`.

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/test_config.py -k 'dotenv' -v`

Expected: FAIL because `dotenv` is not parsed and warning classes do not exist.

- [ ] **Step 3: Add and lock python-dotenv**

Add `"python-dotenv>=1.0.0"` to `[project].dependencies`, then run `uv lock`.

- [ ] **Step 4: Implement minimal atomic parser**

In `envlit/config.py`, define:

```python
class ConfigOverrideWarning(UserWarning):
    """An environment value replaced one from an earlier config source."""


class ConfigDotenvWarning(UserWarning):
    """A non-fatal dotenv entry was ignored."""
```

Normalize `dotenv` to `list[str]`; reject other types. Resolve paths against `config_file.parent`, require `is_file()`, open as UTF-8, eagerly collect `dotenv.parser.parse_stream()` bindings, and reject the whole file if any binding has `error=True`. Convert successful non-`None` key/value bindings to ordered entries without interpolation. Warn and ignore key-only bindings.

- [ ] **Step 5: Verify GREEN**

Run: `uv run pytest tests/test_config.py -k 'dotenv' -v`

Expected: all selected tests PASS.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock envlit/config.py tests/test_config.py
git commit -m "feat: parse dotenv files atomically"
```

### Task 2: Ordered Merge, Inheritance, and Safe Warnings

**Files:**
- Modify: `envlit/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Add failing precedence tests**

Cover these exact sequences:

```text
first dotenv < later dotenv < current YAML env
parent resolved env < child dotenv < child YAML env
```

Assert each replacement emits one `ConfigOverrideWarning`, warning messages contain the variable and resolved old/new source paths, and messages do not contain either secret value. Assert profiles without `dotenv` retain existing env/flags/hooks behavior.

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/test_config.py -k 'override or precedence or inheritance' -v`

Expected: new precedence/source-warning assertions FAIL.

- [ ] **Step 3: Implement sourced ordered merge**

Introduce a private sourced-value representation or parallel `dict[str, str]` source map. Refactor recursive loading so each YAML layer applies in this order:

```python
resolved_parent
merge(each_local_dotenv)
merge(local_yaml_env)
```

On an existing key, call `warnings.warn(..., ConfigOverrideWarning, stacklevel=...)` before replacing it. Include only variable name and resolved source labels, never values. Preserve existing shallow flags merging and parent-first hook concatenation.

- [ ] **Step 4: Verify GREEN and regression safety**

Run: `uv run pytest tests/test_config.py -v`

Expected: all config tests PASS.

- [ ] **Step 5: Commit**

```bash
git add envlit/config.py tests/test_config.py
git commit -m "feat: merge dotenv layers with override warnings"
```

### Task 3: CLI Error/Stream Behavior and Restoration Acceptance

**Files:**
- Modify: `tests/test_cli.py`
- Modify if required: `envlit/cli.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_internal.py`

- [ ] **Step 1: Add failing CLI tests**

Use `CliRunner(mix_stderr=False)` where supported, or Click's captured stderr API, to prove:

- a successful override prints `ConfigOverrideWarning` to stderr;
- stdout begins with the generated script and contains no warning;
- a missing or malformed declared dotenv exits nonzero and stdout contains no generated shebang;
- a dotenv variable appears in the generated export command.

Add an acceptance test that runs the generated load script in a bash subprocess with the project command entry points available, then runs restore and proves a pre-existing dotenv-loaded variable returns to its original value and a newly introduced variable is unset.

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/test_cli.py -k 'dotenv' -v`

Expected: FAIL until CLI stream/error behavior and acceptance fixture are correct.

- [ ] **Step 3: Make minimal CLI changes if tests expose a gap**

Keep configuration warnings on stderr through Python's warning mechanism. Ensure dynamic flag preloading does not duplicate parsing/warnings and exceptions are rendered as CLI errors without emitting partial shell output. Do not add dotenv logic to `script_generator.py`.

- [ ] **Step 4: Verify GREEN**

Run: `uv run pytest tests/test_cli.py tests/test_internal.py -v`

Expected: all selected tests PASS.

- [ ] **Step 5: Commit**

```bash
git add envlit/cli.py tests/test_cli.py tests/test_internal.py
git commit -m "test: verify dotenv CLI and restoration behavior"
```

Only include files actually changed in the commit.

### Task 4: User Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/index.md`
- Modify: `docs/index.zh.md`
- Modify: `skills/envlit/SKILL.md`

- [ ] **Step 1: Add concise public examples**

Document string and list syntax, config-relative paths, required-file errors, and precedence:

```yaml
dotenv:
  - "./.env"
  - "./.env.local"

env:
  DEBUG: "true"
```

State that later dotenv files replace earlier ones with warnings, YAML env wins last, values are never printed in warnings, and envlit does not auto-discover dotenv files.

- [ ] **Step 2: Verify documentation consistency**

Run: `rg -n "dotenv|\.env.local|自动发现|auto-discover" README.md docs/index.md docs/index.zh.md skills/envlit/SKILL.md`

Expected: all four public surfaces describe compatible syntax and precedence.

- [ ] **Step 3: Build docs**

Run: `uv run mkdocs build --strict`

Expected: exit 0.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/index.md docs/index.zh.md skills/envlit/SKILL.md
git commit -m "docs: document dotenv profile imports"
```

### Task 5: Full Verification and Requirement Audit

**Files:**
- Verify all changed files

- [ ] **Step 1: Run formatting and lint checks**

Run:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv lock --locked
```

Expected: every command exits 0.

- [ ] **Step 2: Run complete test suite**

Run: `uv run pytest --cov --cov-report=term`

Expected: exit 0 with no failed tests.

- [ ] **Step 3: Build distribution**

Run: `make build`

Expected: wheel and source distribution build successfully with `python-dotenv` listed as a runtime requirement.

- [ ] **Step 4: Run manual shell acceptance scenario**

Create temporary `.envlit/default.yaml`, `.env`, and `.env.local` fixtures outside the repository. Invoke `envlit load`, verify precedence and stderr warnings, source the script in bash, invoke restore, and assert original variables are restored. Do not persist fixture secrets or files.

- [ ] **Step 5: Audit against the design spec**

Re-read `docs/superpowers/specs/2026-07-14-dotenv-loading-design.md` and map each requirement to a passing test, command output, or inspected artifact. Address any missing evidence before completion.

- [ ] **Step 6: Inspect final diff and repository state**

Run: `git diff HEAD~4 --check`, `git status --short`, and `git log --oneline -8`.

Expected: no whitespace errors, no unintended files, and focused commits.
