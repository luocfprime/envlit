---
name: envlit-dev
description: Guidelines for AI agents working on the envlit project - a CLI tool for managing environment variable contexts
license: MIT
compatibility: opencode
metadata:
  audience: developers
  project: envlit
  language: python
---

## What I do
- Help AI agents understand the envlit codebase structure and testing approach
- Provide guidance on implementing features, fixing bugs, and validating changes
- Direct agents to relevant code files based on the task at hand
- Guide testing using the TESTING_GUIDE.md validation approach

## When to use me
Use this skill when:
- You are asked to modify or extend the envlit codebase
- You need to understand how a specific feature works (state tracking, config loading, hooks, etc.)
- You are debugging issues related to environment variable management
- You need to run tests or validate behavior

## Project Overview

**envlit** is a Python CLI tool for organizing, loading, and switching between environment variable contexts.

- **Language**: Python 3.10+
- **CLI Framework**: Click
- **Config Format**: YAML
- **Key Features**: Smart state tracking, dynamic CLI flags, PATH operations, lifecycle hooks, config inheritance

## Code Structure

```
envlit/
├── cli.py              # Main CLI commands, dynamic flag injection
├── config.py           # YAML parsing, config inheritance
├── state.py            # Compare-and-Swap algorithm, state tracking
├── internal.py         # State management (begin/end/restore)
├── operations.py       # Environment variable operations (set/unset/prepend/append/remove)
├── script_generator.py # Shell script generation & escaping
├── constants.py        # Project constants
└── __main__.py         # Entry point
```

## Key Design Patterns

### Compare-and-Swap Algorithm
The core of envlit's smart state tracking:
- Tracks `original` (restore point) and `current` (last value envlit set)
- On load: compares actual shell value with `current`
- If different: user interference detected, `original` is updated
- On unload: restores to what user expects, not what envlit first saw

### Dynamic CLI Flags
- YAML `flags` section defines CLI options
- Flags become real Click options at runtime
- Support for aliases, defaults, choices, and mappings

### Config Inheritance
- `extends` key references parent config
- Parent loaded first, then child merges/overrides
- Hooks from both configs execute in order

## Quick Commands

```bash
# Install dependencies
make install

# Run tests
pytest

# Run linting
ruff check envlit/

# Type checking
mypy envlit/

# Test in examples directory
cd examples
eval "$(envlit init)"
el dev --cuda 2
eul
```

## Testing Approach

**Use the examples/ directory for validation**:
```bash
cd examples
eval "$(envlit init)"

# Test dynamic flags
envlit load dev --help

# Test state tracking
export CUDA_VISIBLE_DEVICES="0"
el dev --cuda 1
echo $CUDA_VISIBLE_DEVICES  # Should be "1"
el dev --cuda 2
echo $CUDA_VISIBLE_DEVICES  # Should be "2"
eul
echo $CUDA_VISIBLE_DEVICES  # Should be "0" (original!)

# Test manual interference detection
el dev --cuda 1
export CUDA_VISIBLE_DEVICES="7"  # Manual change
el dev --cuda 3
eul
echo $CUDA_VISIBLE_DEVICES  # Should be "7" (preserves manual change!)
```

## File Reference by Task

| Task | Primary Files |
|------|---------------|
| State tracking issues | `state.py`, `internal.py` |
| CLI/flag problems | `cli.py` |
| Config loading/YAML | `config.py` |
| Shell script bugs | `script_generator.py` |
| PATH operations | `operations.py` |
| Special chars/escaping | `script_generator.py`, `operations.py` |
| Hook execution | `config.py`, `cli.py` |

## Important Implementation Details

### State Variable Naming
State is stored in `__ENVLIT_STATE_<hash>` environment variable (JSON format)

### Operation Order
PATH operations apply in sequence: remove → prepend → append

### Hook Execution Order
1. Base config pre-load hooks
2. Child config pre-load hooks
3. Set variables
4. Base config post-load hooks
5. Child config post-load hooks

### Special Character Handling
- `{{DOLLAR}}` → literal `$`
- `${VAR}` → variable expansion
- Backticks are auto-escaped
- Use YAML alternation for quotes

## Validation Checklist

Before considering a change complete:
- [ ] Test passes in examples/ directory
- [ ] State tracking works correctly (unload restores original)
- [ ] Manual interference is detected and respected
- [ ] Dynamic flags appear in --help
- [ ] Hooks execute in correct order
- [ ] PATH operations work (prepend/append/remove)
- [ ] Unit tests pass (`pytest`)
- [ ] Linting passes (`ruff check`)
- [ ] Type checking passes (`mypy`)

## Common Pitfalls

❌ **Don't** assume consecutive loads are independent - state accumulates
❌ **Don't** forget that manual changes become the new "original"
❌ **Don't** treat unset and empty string as the same - envlit distinguishes them
❌ **Don't** forget to test in a fresh terminal for each scenario

## Success Criteria

A good implementation should:
✅ Preserve idempotency (loading same config twice is safe)
✅ Maintain reversibility (unload restores original state)
✅ Respect user manual changes (Compare-and-Swap algorithm)
✅ Provide clear error messages
✅ Pass all tests in TESTING_GUIDE.md scenarios
