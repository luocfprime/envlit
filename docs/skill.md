# envlit Skill

!!! abstract
    This page contains an OpenCode-compatible SKILL.md file that you can copy and paste into your project at `.opencode/skills/envlit/SKILL.md`. It helps AI agents understand and use envlit CLI effectively.

Copy and paste this SKILL.md into your project at `.opencode/skills/envlit/SKILL.md` to help agents understand and use envlit.

````markdown
---
name: envlit
description: A CLI tool to organize, load, and switch between environment variable contexts via YAML configs
license: MIT
compatibility: opencode
metadata:
  audience: developers
  tool: envlit
  language: shell
---

## What I do
- Help you understand and use envlit for environment variable management
- Guide config file creation and YAML syntax
- Explain state tracking, dynamic flags, PATH operations, and hooks
- Debug issues with loading/unloading environments

## When to use me
- User wants to use envlit CLI (`envlit`, `el`, `eul`)
- User wants to manage environment variables with YAML configs
- Need to set up envlit in a project
- Configuring dynamic CLI flags or lifecycle hooks
- Debugging state restoration issues

## Quick Start

```bash
# Install
pip install envlit

# Initialize shell (add to .bashrc/.zshrc)
# This sets up `el` and `eul` aliases
eval "$(envlit init)"

# Create config at .envlit/default.yaml, then:
el          # Load default profile (alias for envlit load)
eul         # Unload and restore (alias for envlit unload)
```

## Core Commands

| Command | Shell Alias | Purpose |
|---------|-------------|---------|
| `envlit init` | - | Output shell integration code (sets up aliases below) |
| `envlit load <profile>` | `el` | Load environment from config |
| `envlit unload` | `eul` | Restore original state |

**Note:** `el` and `eul` are shell aliases created by `envlit init`. They only work after running `eval "$(envlit init)"`.

## Config Format (.envlit/<profile>.yaml)

### Simple Values
```yaml
env:
  PROJECT_MODE: "Development"
  DEBUG: "true"
```

### Explicit Operations
```yaml
env:
  API_URL:
    op: set
    value: "http://localhost:8000"

  OLD_VAR:
    op: unset

  PATH:
    - op: prepend
      value: "./bin"
    - op: append
      value: "/opt/tools"
    - op: remove
      value: "/old/path"
```

### Dynamic CLI Flags
```yaml
flags:
  cuda:
    env: CUDA_VISIBLE_DEVICES
    help: "GPU device ID"
    default: "0"
    aliases: ["g"]

  backend:
    env: ML_COMPUTE_BACKEND
    choices:
      c: "CPU"
      g: "GPU"
      t: "TPU"
```

Usage: `el dev --cuda 2 --backend g`

### Lifecycle Hooks
```yaml
hooks:
  pre-load:
    - echo "Loading..."
  post-load:
    - echo "Ready!"
  pre-unload:
    - echo "Unloading..."
  post-unload:
    - echo "Done!"
```

### Config Inheritance
```yaml
extends: base.yaml  # Load base.yaml first, then merge
```

## State Tracking (Compare-and-Swap)

envlit preserves user changes:

```bash
export CUDA_VISIBLE_DEVICES="0"
el dev --cuda 1       # Sets to "1"
export CUDA_VISIBLE_DEVICES="7"  # User changes it
el dev --cuda 2       # Sets to "2"
eul                   # Restores to "7" (user's value, not "0")
```

## Special Characters

```yaml
env:
  PRICE: "Costs {{DOLLAR}}100"     # Literal $
  PATH: "${HOME}/bin"               # Variable expansion
  CMD: "Use `ls` command"           # Backticks auto-escaped
```

## Common Patterns

### Development Profile
```yaml
# .envlit/dev.yaml
env:
  DEBUG: "true"
  LOG_LEVEL: "debug"
flags:
  port:
    env: APP_PORT
    default: "8000"
```

### Production Profile
```yaml
# .envlit/prod.yaml
extends: base.yaml
env:
  DEBUG: "false"
  LOG_LEVEL: "warn"
```

## Troubleshooting

Run `envlit doctor` to diagnose common issues.

- **Command not found**: Run `eval "$(envlit init)"` first
- **Config not loading**: Check file is at `.envlit/<name>.yaml`
- **Variables not restored**: Check `eul` was run in same shell session
- **Flags not appearing**: Verify YAML syntax, check `el <profile> --help`

## Links

- Docs: https://luocfprime.github.io/envlit/
- Repo: https://github.com/luocfprime/envlit
````
