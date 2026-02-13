# envlit Testing Guide for AI Agents

## Quick Start

```bash
# Navigate to the examples directory (pre-configured test environment)
cd examples

# Initialize shell integration
eval "$(envlit init)"

# Now you can use 'el' and 'eul' aliases
el dev --cuda 2
eul
```

## What You're Testing

This guide helps you **validate** envlit's behavior, not prescribe every test case. Use the pre-configured `examples/.envlit/` configs and explore freely in a fresh terminal.

## Core Validation Guidelines

### 1. Help System & Dynamic Flags

**What to check:**
- Run `envlit load dev --help` - Do flags from YAML (`--cuda`, `--backend`) appear?
- Are flag aliases working? (e.g., `-g` for `--cuda`)
- Do default values show up in help text?
- Can you set flags: `el dev --cuda 3 --backend g`?

**Expected behavior:**
- YAML-defined flags become real CLI options
- Help messages reflect current config
- Flags override env section values

### 2. Configuration Loading

**What to check:**
```bash
# Load dev profile with flags
el dev --cuda 2 --backend t

# Verify variables are set
echo $CUDA_VISIBLE_DEVICES  # Should be "2"
echo $ML_COMPUTE_BACKEND    # Should be "TPU" (mapped from "t")
echo $PROJECT_MODE          # Should be "Development"
echo $DEBUG                 # Should be "true"
```

**Expected behavior:**
- Variables are exported correctly
- Flag mappings work (backend: c→CPU, g→GPU, t→TPU)
- PATH operations apply (check `echo $PATH` for prepended values)
- Hooks execute and print messages

### 3. State Tracking - The Critical Part

This is where the Compare-and-Swap algorithm matters most.

#### Scenario A: Normal Consecutive Loads
```bash
# Start fresh
export CUDA_VISIBLE_DEVICES="0"
echo "Initial: $CUDA_VISIBLE_DEVICES"

# Load 1
el dev --cuda 1
echo "After load 1: $CUDA_VISIBLE_DEVICES"  # Should be "1"

# Load 2 (without unload)
el dev --cuda 2
echo "After load 2: $CUDA_VISIBLE_DEVICES"  # Should be "2"

# Unload
eul
echo "After unload: $CUDA_VISIBLE_DEVICES"  # Should be "0" (original!)
```

**Expected:** Unload restores to the *very first* original value (`0`), not `1` or `2`.

#### Scenario B: Manual Interference Detection
```bash
# Start fresh
export CUDA_VISIBLE_DEVICES="0"

# Load 1
el dev --cuda 1
echo "After load: $CUDA_VISIBLE_DEVICES"  # Should be "1"

# Manual intervention (you change it yourself)
export CUDA_VISIBLE_DEVICES="7"
echo "After manual change: $CUDA_VISIBLE_DEVICES"  # Is "7"

# Load 2 (envlit detects interference!)
el dev --cuda 3
echo "After load 2: $CUDA_VISIBLE_DEVICES"  # Should be "3"

# Unload
eul
echo "After unload: $CUDA_VISIBLE_DEVICES"  # Should be "7" (respects your manual change!)
```

**Expected:** When you manually change a tracked variable, envlit treats that as the new "original" to restore to. This is the smart part of Compare-and-Swap.

#### Scenario C: Manual Changes Before Unload
```bash
# Start fresh (DEBUG not set)
unset DEBUG

# Load dev profile
el dev
echo "After load: $DEBUG"  # Should be "true" (from config)

# Manual change after load
export DEBUG=false
echo "After manual change: $DEBUG"  # Is "false"

# Unload directly (without reload)
eul
echo "After unload: $DEBUG"  # Should be "false" (preserves your manual change!)
```

**Expected:** envlit detects manual changes at unload time and preserves them. If you changed `DEBUG` from `true` to `false`, unload will restore it to `false`, not unset it or revert to the config value.

**Why this matters:** This ensures manual tweaks made during development aren't lost when switching contexts.

### 4. Path Operations

**What to check:**
```bash
# Append /usr/local/old-tools
export PATH="$PATH:/usr/local/old-tools"

echo "Before: $PATH"
el dev
echo "After: $PATH"

# Verify:
# - "./bin" and "./scripts" are prepended
# - "/usr/local/old-tools" is removed (if it was there)
```

**Expected behavior:**
- `prepend` adds to front
- `append` adds to end
- `remove` eliminates all occurrences
- Operations apply in order

### 5. Lifecycle Hooks

**What to check:**
```bash
el dev 2>&1 | grep -E "Hello|Checking dependencies|Development environment loaded"
eul 2>&1 | grep -E "Unloading|restored"
```

**Expected behavior:**
- Pre-load hooks run *before* variables are set
- Post-load hooks run *after* variables are set
- Hook output is visible
- Inheritance works (base.yaml hooks + dev.yaml hooks both execute)

### 6. Config Inheritance

**What to check:**
```bash
# dev.yaml extends base.yaml
el dev 2>&1

# Look for:
# "Hello, this is pre-load hook from common base." (from base.yaml)
# "🐍 Checking dependencies..." or similar (from dev.yaml)
```

**Expected behavior:**
- Base config is loaded first
- Child config merges/overrides
- Hooks from both configs execute

## Hard Corner Cases to Test

### Case 1: Unload Without Load
```bash
# Fresh terminal, no envlit state
eul
# Expected: Should handle gracefully, not crash
```

### Case 2: Multiple Profiles
```bash
el dev --cuda 1
echo $DEBUG $CUDA_VISIBLE_DEVICES  # Should be "true" and "1"
el prod  # Load different profile without unload
echo $DEBUG $CUDA_VISIBLE_DEVICES  # Should be "false" and "1"

# Current behavior: Variables accumulate (this might be expected or not)
```

### Case 3: Environment Variable Operations

**String values (shortcut for set):**
```bash
cat > /tmp/test-ops.yaml << 'EOF'
env:
  PROJECT_MODE: "Development"
  DEBUG: "true"
EOF

el -c /tmp/test-ops.yaml
echo $PROJECT_MODE  # Should be "Development"
echo $DEBUG         # Should be "true"
eul
```

**Explicit operations:**
```bash
cat > /tmp/test-ops2.yaml << 'EOF'
env:
  API_URL:
    op: set
    value: "http://localhost:8000"

  PRODUCTION_KEY:
    op: unset

  PATH:
    op: prepend
    value: "./venv/bin"
EOF

export PRODUCTION_KEY="secret"
el -c /tmp/test-ops2.yaml
echo $API_URL           # Should be "http://localhost:8000"
echo $PRODUCTION_KEY    # Should be unset (no output)
echo $PATH | head -c 20 # Should start with "./venv/bin"
eul
```

**Operation pipeline:**
```bash
cat > /tmp/test-pipeline.yaml << 'EOF'
env:
  PATH:
    - op: remove
      value: "/old/path"
    - op: prepend
      value: "./bin"
    - op: append
      value: "/opt/bin"
EOF

export PATH="/usr/bin:/old/path:/bin"
el -c /tmp/test-pipeline.yaml
echo $PATH  # Should be "./bin:/usr/bin:/bin:/opt/bin" (removed /old/path)
eul
echo $PATH  # Should be "/usr/bin:/old/path:/bin" (restored)
```

### Case 4: Special Characters
```bash
# Create test config with special chars
cat > /tmp/test-special.yaml << 'EOF'
env:
  FOO: 0
  BAR: $FOO
  BAZ: ${SOME_ENV_VAR:-default}
  # Literal dollar with {{DOLLAR}} placeholder
  PRICE: "Item costs {{DOLLAR}}100"
  DOLLAR_VAR: "{{DOLLAR}}JAVA_HOME is the variable name"
  # Mixed: literal dollar and variable expansion
  MIXED: 'Price: {{DOLLAR}}50, Path: ${HOME}'
  # Backticks are always literal (auto-escaped)
  NOTE: "Use `command` syntax"
  # Quotes work via YAML alternation
  SINGLE: "Has 'single' quotes"
  DOUBLE: 'Has "double" quotes'
  TEST_REF: '${HOME}/path'
EOF

el -c /tmp/test-special.yaml
echo $FOO          # Should be "0"
echo $BAR          # Should be "0" (expanded from $FOO)
echo $BAZ          # Should be "default"
echo $PRICE        # Should be "$100" (literal dollar)
echo $DOLLAR_VAR   # Should be "$JAVA_HOME is the variable name"
echo $MIXED        # Should be "Price: $50, Path: /Users/you" ($ literal, ${HOME} expanded)
echo $NOTE         # Should be "Use `command` syntax" (backticks literal)
echo $TEST_REF     # ${HOME} should be expanded by shell
```

### Case 4: Unset vs Empty String
```bash
# Variable starts unset
unset CUDA_VISIBLE_DEVICES

el dev --cuda 0  # If config sets CUDA_VISIBLE_DEVICES
eul     # Should CUDA_VISIBLE_DEVICES be unset again (not empty string)?

env | grep CUDA_VISIBLE_DEVICES  # Expected: No output (still unset)

# Variable starts empty
export CUDA_VISIBLE_DEVICES=""
el dev --cuda 0
eul     # Should CUDA_VISIBLE_DEVICES be "" (empty), not unset?
env | grep CUDA_VISIBLE_DEVICES  # Expected: CUDA_VISIBLE_DEVICES="" (still set, but empty)
```

**Expected:** envlit distinguishes between `null` (unset) and `""` (empty).

## What "Right" Looks Like

### Properties to Verify

✅ **Idempotency**: Loading the same config twice should be safe
✅ **Reversibility**: Unload should restore original state
✅ **Transparency**: User can see what envlit will do before sourcing
✅ **Predictability**: Manual changes are respected (Compare-and-Swap)
✅ **Informativeness**: Error messages guide users to solutions

### Red Flags

❌ Variables not restored correctly after unload
❌ Dynamic flags missing from `--help`
❌ Hooks not executing or executing in wrong order
❌ Special characters causing shell injection or errors
❌ State corruption after manual interference
❌ Cryptic error messages

## Exploration Tips

1. **Use fresh terminals** for each test scenario to avoid state pollution
2. **Check intermediate state**: Look at `$__ENVLIT_STATE_<hash>` to see tracked variables (it's JSON)
3. **Read generated scripts**: `envlit load dev` shows what *would* be sourced
4. **Test error paths**: Try loading non-existent profiles, invalid YAML, missing flags
5. **Verify hooks**: Add `set -x` in hooks to see execution trace
6. **Compare outputs**: Does behavior match design spec from the main document?

## Success Criteria

An AI agent should be able to:
- Load any example config and verify variables are set correctly
- Perform the two main Compare-and-Swap scenarios successfully
- Identify when behavior deviates from design spec
- Propose fixes for any issues found

## Files to Examine When Investigating Issues

- `envlit/state.py` - Compare-and-Swap algorithm implementation
- `envlit/internal.py` - State tracking (begin/end/restore)
- `envlit/script_generator.py` - Shell script generation & escaping
- `envlit/config.py` - YAML parsing & inheritance
- `envlit/cli.py` - Dynamic flag injection
- `tests/test_*.py` - Unit tests show expected behavior

## Key Design Principle to Validate

**The Compare-and-Swap Algorithm:**
> envlit tracks `original` (restore point) and `current` (last value envlit set). When loading, it compares the actual shell value with `current`. If they differ, user interference is detected, and `original` is updated to the user's value. This ensures unload always restores to what the user expects, not what envlit first saw.

Your testing should confirm this principle holds in practice.
