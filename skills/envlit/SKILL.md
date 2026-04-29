---
name: envlit
description: Use when you need to load project-specific environment variables or the user needs help with envlit CLI usage, `.envlit/*.yaml` profiles, dynamic flags, PATH operations, lifecycle hooks, or environment restore/state-tracking issues involving `envlit`, `el`, or `eul`.
---

# envlit — Environment Profile Manager

envlit lets you define named **environment profiles** in YAML files, then load/unload them with a single shell command. It tracks what it changed and intelligently restores your original environment, preserving any manual changes you made in between.

## When to use envlit

- Switching between dev/staging/prod configs in the same shell
- ML/AI workflows: manage `CUDA_VISIBLE_DEVICES`, model paths, backends per experiment
- Multi-project setups: each project has its own `.envlit/` folder committed to git
- Team consistency: share base configs via git, keep personal overrides locally

---

## Installation & Shell Setup

```bash
pip install envlit

# Add to ~/.bashrc or ~/.zshrc (once):
eval "$(envlit init)"
```

`envlit init` outputs shell function definitions for `el` (load) and `eul` (unload). Without this line, `el`/`eul` are not available.

Customize the alias names:
```bash
eval "$(envlit init --alias-load myload --alias-unload myunload)"
```

---

## Core Commands

| Command | What it does |
|---------|-------------|
| `el` | Load `.envlit/default.yaml` |
| `el <profile>` | Load `.envlit/<profile>.yaml` |
| `el <profile> --flag value` | Load with dynamic flag overrides |
| `el --config /path/to/any.yaml` | Load an arbitrary config file (bypasses `.envlit/` lookup) |
| `eul` | Unload and restore original environment |
| `envlit state` | Print tracked variables in `KEY=VALUE` format |
| `envlit state --from-env` | Print current shell values for tracked vars |
| `envlit state > .env` | Export tracked vars to a `.env` file |
| `envlit doctor` | Diagnose installation and config issues |

### `--config` / `-c` flag

`el` and `eul` accept `--config` (short: `-c`) to load any YAML file regardless of location:

```bash
el --config ~/shared/base.yaml           # load by path, no profile name
el dev --config /tmp/override.yaml       # profile name is ignored when --config is given
envlit load --config path/to/config.yaml # underlying command also supports it
```

### `envlit state` output format

Output is one `KEY=VALUE` per line, sorted alphabetically. Values containing spaces, tabs, `$`, backticks, quotes, or backslashes are wrapped in double quotes with special characters escaped. Plain values (only letters, digits, `/`, `:`, `.`, `-`, `_`, etc.) are output bare:

```
API_URL=https://api.example.com
DEBUG=true
PATH=/home/user/.local/bin:/usr/bin:/bin
PROJECT_DIR="/home/user/my project"
```

In the example above, `PATH` has no special characters so it is unquoted; `PROJECT_DIR` contains a space so it is double-quoted.

---

## Config File Format (`.envlit/<profile>.yaml`)

Config files live in a `.envlit/` directory in your project root.

### Full annotated example

```yaml
# Optional: inherit from another profile
extends: "./base.yaml"

# Environment variables
env:
  # 1. String shorthand — equivalent to op: set
  DEBUG: "true"
  API_URL: "https://api.example.com"

  # 2. Inline flag — CLI option defined alongside the variable it controls
  CUDA_VISIBLE_DEVICES:
    flag: ["--cuda", "-g"]   # CLI option names (list of strings)
    default: "0"              # value used when flag is not passed

  ML_COMPUTE_BACKEND:
    flag: ["--backend", "-b"]
    default: "c"
    map:                      # map CLI input → env var value
      c: "CPU"
      g: "GPU"
      t: "TPU"

  # 3. Single operation (dict syntax)
  PYTHONPATH:
    op: prepend
    value: "./src"

  OLD_VAR:
    op: unset

  # 4. Operation pipeline (list)
  PATH:
    - op: remove
      value: "/deprecated/bin"
    - op: prepend
      value: "./bin"
    - op: append
      value: "/opt/tools"

  # Shell variable expansion (default behaviour)
  DATA_DIR: "${HOME}/data"

  # Literal dollar sign — use interpolate: false
  PRICE_TAG:
    op: set
    value: "$9.99"
    interpolate: false

  # null (YAML null) is shorthand for op: unset
  REMOVED_VAR: null

# Lifecycle hooks — each hook has a name (string) and script (bash string)
# script can be a single line or a multiline block using YAML's | scalar
hooks:
  pre_load:
    - name: "Check docker"
      script: "command -v docker >/dev/null || echo 'Warning: docker not found'"
    - name: "Multi-line setup"
      script: |
        echo 'Starting setup...'
        mkdir -p /tmp/myapp
        echo 'Done'
  post_load:
    # post_load runs AFTER env vars are exported — can reference newly set vars
    - name: "Show status"
      script: "echo 'Loaded. DEBUG=${DEBUG}, MODE=${PROJECT_MODE}'"
  pre_unload:
    - name: "Cleanup"
      script: "echo 'Unloading...'"
  post_unload:
    - name: "Confirm"
      script: "echo 'Environment restored'"
```

**Hook execution order during load:**
1. `pre_load` hooks run first (env vars NOT yet set — see pre-load state)
2. Environment variables are exported
3. `post_load` hooks run (env vars ARE set — safe to reference `$MY_VAR`)

**Hook execution order during unload:**
1. `pre_unload` hooks run (env vars still set from the load)
2. Environment is restored to original state
3. `post_unload` hooks run (env vars are unset/restored)

---

## Environment Variable Operations

| Operation | When to use | Required fields |
|-----------|-------------|-----------------|
| `set` | Set a value (also the string shorthand) | `value` |
| `unset` | Remove a variable entirely | — |
| `prepend` | Insert at the front of a `:` separated list | `value` |
| `append` | Insert at the back of a `:` separated list | `value` |
| `remove` | Remove an entry from a `:` separated list | `value` |

All operations support an optional `separator` field (default `:`):
```yaml
env:
  PYTHONPATH:
    op: prepend
    value: "./src"
    separator: ":"   # explicit (same as default)
```

**`interpolate` field** (on single dict ops only, default `true`):
- `true` — `$VAR` and `${VAR}` in the value expand at shell runtime
- `false` — value is treated as a literal string; `$` is never expanded

> **Important**: `interpolate` is only recognised on a **single dict operation** (`{op: set, value: ..., interpolate: false}`). It is **not supported** inside a list pipeline — list steps always use double-quote (interpolate: true) mode. If you need a literal `$` in a pipeline, restructure to a single dict op.

```yaml
env:
  # $HOME expands when the shell sources the generated script
  BIN_DIR:
    op: set
    value: "${HOME}/.local/bin"
    interpolate: true   # default, can be omitted

  # $9.99 stays literally as $9.99
  PRICE:
    op: set
    value: "$9.99"
    interpolate: false

  # WRONG — interpolate is ignored in list pipelines:
  # BAD_EXAMPLE:
  #   - op: set
  #     value: "$9.99"
  #     interpolate: false   # has no effect here
```

**`null` shorthand**: A YAML `null` value is equivalent to `op: unset`:
```yaml
env:
  OLD_API_KEY: null   # same as: op: unset
```

> **Env var name constraint**: names must match `[a-zA-Z_][a-zA-Z0-9_]*`. Names with hyphens (e.g. `MY-VAR`) are rejected.

---

## Dynamic Flags

Flags are defined **inline inside `env:`** entries. The variable name is the key; add a `flag:` field to make it a CLI option:

```yaml
# .envlit/dev.yaml
env:
  CUDA_VISIBLE_DEVICES:
    flag: ["--cuda", "-g"]
    default: "0"

  ML_COMPUTE_BACKEND:
    flag: ["--backend", "-b"]
    default: "c"
    map:
      c: "CPU"
      g: "GPU"
      t: "TPU"
```

```bash
el dev                     # CUDA_VISIBLE_DEVICES=0, ML_COMPUTE_BACKEND=CPU
el dev --cuda 2            # CUDA_VISIBLE_DEVICES=2, ML_COMPUTE_BACKEND=CPU
el dev -g 0,1 -b g         # CUDA_VISIBLE_DEVICES=0,1, ML_COMPUTE_BACKEND=GPU
el dev --help              # Shows all flags including --cuda and --backend
```

Inline flag fields (all inside the `env:` entry):
- `flag` — CLI option name(s): a single string (`"--cuda"`) or list (`["--cuda", "-g"]`)
- `default` — value used when the flag is **not** passed on the CLI. A value passed on the CLI always overrides the default.
- `map` (optional) — dict mapping CLI input → env var value. Unknown values are passed through as-is (no error).

> **Deprecated**: The top-level `flags:` section (with `target:` field) still works but emits a deprecation warning. Migrate flags into `env:` entries as shown above.

---

## Config Inheritance

```yaml
# .envlit/dev.yaml
extends: "./base.yaml"   # path relative to this file
env:
  DEBUG: "true"          # overrides base
```

Merge rules:
- `env`: child wins (shallow merge per key)
- `flags`: child wins (shallow merge per key)
- `hooks`: lists are **concatenated** (base hooks run first)

**Multi-level chaining is supported**: `dev.yaml` → `staging.yaml` → `base.yaml` all resolve correctly. Each file's `extends` is resolved before merging, so the full ancestor chain is flattened in order.

---

## State Tracking

envlit uses a Compare-and-Swap algorithm so it never clobbers manual changes:

```bash
el dev                            # envlit sets DEBUG=true
export DEBUG=verbose              # you change it manually
eul                               # envlit restores DEBUG to original value
                                  # (NOT to "verbose" — envlit saw you changed it)
```

Three scenarios on unload:
1. **Variable was unset before load** → unset it again
2. **Variable was set before load, not touched since** → restore original value
3. **You modified it after load** → leave it at your value (not restored)

> `eul` works only in the same shell session as `el`. Opening a new terminal loses the tracking state.

**Running `el` twice without `eul`**: Safe. The CAS algorithm detects that each variable's value matches what the previous `el` set (no manual interference), keeps the original pre-first-load value, and just updates `current`. `eul` restores to the state before the **first** `el` in the session.

**`eul` with no prior `el`**: If `eul` is run in a shell where `el` was never called (no tracking state exists), it is a no-op — it outputs a comment and makes no changes.

**No parent-directory traversal**: `el` only looks for `.envlit/` in the **current working directory**. It does not walk up to parent directories. Run `el` from your project root (where `.envlit/` lives), or use `--config` to point at a file by path.

---

## Config Inheritance Pattern (Multi-profile Setup)

```
.envlit/
├── base.yaml      # shared: API URLs, common tools
├── dev.yaml       # extends base, debug flags
└── prod.yaml      # extends base, prod settings
```

```yaml
# base.yaml
env:
  APP_NAME: "myapp"
  LOG_FORMAT: "json"
hooks:
  post_load:
    - name: "Banner"
      script: "echo 'Loaded ${APP_NAME}'"

# dev.yaml
extends: "./base.yaml"
env:
  DEBUG: "true"
  LOG_LEVEL: "debug"
  API_URL: "http://localhost:8000"

# prod.yaml
extends: "./base.yaml"
env:
  DEBUG: "false"
  LOG_LEVEL: "warn"
  API_URL: "https://api.example.com"
```

---

## Special Characters Reference

| YAML value | Shell sees | Notes |
|-----------|-----------|-------|
| `"$HOME/data"` | `/Users/you/data` | Shell expands `$HOME` (interpolate: true) |
| `"${PATH:-/usr/bin}"` | default expansion | Full `${VAR:-default}` syntax supported |
| `"price $9.99"` | `price $9.99` (⚠ $9 expands!) | Use `interpolate: false` for literal `$` |
| `"Use \`ls\`"` | `` Use `ls` `` | Backticks auto-escaped in double-quote mode |
| `'has "double" quotes'` | `has "double" quotes` | YAML single-quote wrapping |

> `${VAR:-${OTHER}}` (nested expansions) are **not** supported — the inner `}` terminates the match early.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `el: command not found` | Shell not initialized | Add `eval "$(envlit init)"` to `.bashrc`/`.zshrc`, then `source ~/.zshrc` |
| Config not loading | Wrong filename | File must be `.envlit/<profile>.yaml` (or `.yml`), in the current directory |
| Dynamic flags missing from `--help` | YAML syntax error in `env:` flag entry | Check indentation; `flag:` must be inside an `env:` entry; run `envlit doctor` |
| Variables not restored after `eul` | Different shell session | `eul` only works in the shell that ran `el` |
| `Invalid environment variable name` | Hyphen/space in YAML key | Rename key to match `[a-zA-Z_][a-zA-Z0-9_]*` |
| Hook not running | Wrong key name | Hook keys are `pre_load`, `post_load`, `pre_unload`, `post_unload` (underscore) |

Run `envlit doctor` for automated diagnosis.

---

## How to Help Users

1. **New setup** → guide through `pip install envlit`, `eval "$(envlit init)"`, create `.envlit/default.yaml`
2. **YAML errors** → check hook key names (underscores), flag field names (`flag`/`target`/`map`), valid env var names
3. **State confusion** → explain CAS algorithm; `eul` only works in same shell session
4. **Flags not working** → use inline flag syntax in `env:` (not deprecated top-level `flags:`); verify `flag` is a list, `map` keys match what user passes on CLI
5. **PATH operations** → use pipeline syntax (list of dicts); `separator` defaults to `:`

---

## Links

- Docs: https://luocfprime.github.io/envlit/
- Repo: https://github.com/luocfprime/envlit
