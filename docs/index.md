# envlit

A minimal CLI tool to organize, load, and switch between your project's environment contexts.

## Installation

```bash
pip install envlit
```

## Quick Start

Initialize envlit in your shell (add to `.bashrc` or `.zshrc`):

```bash
eval "$(envlit init)"
```

Create a config file at `.envlit/default.yaml`:

```yaml
env:
  PROJECT_MODE: "Development"
  DEBUG: "true"
```

Load and unload environments:

```bash
el          # Load default profile
el dev      # Load dev profile
eul         # Unload environment
```

## Features

### Smart State Tracking
Automatically detects and preserves manual environment changes between load/unload cycles. Won't overwrite variables you've modified.

Example:
```bash
el dev                    # Load dev environment (sets DEBUG=true)
export DEBUG=false        # Manually change DEBUG
export CUSTOM_VAR=foo     # Add your own variable
eul                       # Unload: restores original DEBUG, keeps CUSTOM_VAR
```

envlit only restores variables it managed, preserving your manual changes.

### Dynamic Flags
Define short CLI flags in YAML that map to long environment variable names and values. Reduces typing burden:

```yaml
flags:
  cuda:
    flag: ["--cuda", "-g"]
    default: "0"
    target: "CUDA_VISIBLE_DEVICES"

  backend:
    flag: ["--backend", "-b"]
    default: "c"
    target: "ML_COMPUTE_BACKEND"
    map:
      c: "CPU"
      g: "GPU"
      t: "TPU"
```

Usage: `el dev --cuda 2 -b g` sets `CUDA_VISIBLE_DEVICES=2` and `ML_COMPUTE_BACKEND=GPU`

### Path Operations
Advanced PATH manipulation with prepend, append, and remove operations:

```yaml
env:
  PATH:
    - op: prepend
      value: "./bin"
    - op: remove
      value: "/old/path"
```

### Lifecycle Hooks
Execute custom scripts at four lifecycle points:

```yaml
hooks:
  pre_load:
    - name: "Validate setup"
      script: "echo 'Loading...'"
  post_load:
    - name: "Show status"
      script: "echo 'Ready!'"
  pre_unload: [...]
  post_unload: [...]
```

### Config Inheritance
Extend base configurations to reduce duplication:

```yaml
extends: "./base.yaml"
env:
  EXTRA_VAR: "value"
```

### Multiple Profiles
Switch between dev, test, and prod environments:

```bash
el dev      # Load .envlit/dev.yaml
el prod     # Load .envlit/prod.yaml
```

## Configuration

Create `.envlit/<profile>.yaml` files:

```yaml
# Optional: Inherit from base config
extends: "./base.yaml"

# Dynamic CLI flags - short flags map to long env var names and values
flags:
  cuda:
    flag: ["--cuda", "-g"]
    default: "0"
    target: "CUDA_VISIBLE_DEVICES"

  backend:
    flag: ["--backend", "-b"]
    default: "c"
    target: "ML_COMPUTE_BACKEND"
    map:
      c: "CPU"
      g: "GPU"
      t: "TPU"

# Environment variables
env:
  # Simple values
  DEBUG: "true"
  API_URL: "https://api.example.com"

  # Unset variables
  LEGACY_VAR: null

  # Shell expansion
  DATA_PATH: "${HOME}/data"

  # Path operations
  PATH:
    - op: prepend
      value: "./bin"
    - op: append
      value: "/usr/local/tools"
    - op: remove
      value: "/deprecated/path"

# Lifecycle hooks
hooks:
  pre_load:
    - name: "Check dependencies"
      script: "command -v docker >/dev/null || echo 'Warning: docker not found'"
  post_load:
    - name: "Show environment"
      script: "echo '✓ Environment loaded'"
  pre_unload:
    - name: "Cleanup"
      script: "echo 'Unloading...'"
  post_unload:
    - name: "Confirm"
      script: "echo '✓ Environment restored'"
```

## Commands

```bash
# Initialize shell integration
eval "$(envlit init)"

# Load environments
el                    # Load default profile
el dev                # Load dev profile
el dev --cuda 1       # Load with flags

# Unload environment
eul

# Check installation
envlit doctor
```

## Shell Integration

The `init` command creates shell functions that wrap envlit:
- `el` - Load environment
- `eul` - Unload environment

Customize aliases during initialization:

```bash
eval "$(envlit init --alias-load myload --alias-unload myunload)"
```

## How It Works

1. **Load Phase**:
   - Captures current environment state (snapshot A)
   - Runs pre-load hooks
   - Exports environment variables
   - Runs post-load hooks
   - Captures new state (snapshot B) and saves difference

2. **Unload Phase**:
   - Runs pre-unload hooks
   - Restores original environment from saved state
   - Runs post-unload hooks

3. **State Tracking**:
   - Detects manual changes between snapshots
   - Preserves user modifications during unload
   - Only restores variables changed by envlit (Note: those changed during hooks are not tracked, and should be taken care of in hooks themselves)

## Use Cases

- **Development environments** - Switch between dev/prod configs
- **ML/AI workflows** - Conveniently manage CUDA devices, model paths, backends, environment variables
- **Multi-project setup** - Isolated environments per project
- **Team consistency** - Share common environment configs via git, while keeping local overrides

## Links

- [GitHub](https://github.com/luocfprime/envlit)
- [PyPI](https://pypi.org/project/envlit/)
