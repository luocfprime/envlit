# envlit Examples

This directory contains example configuration files for `envlit`.

## Quick Start

1. **Copy the `.envlit` directory** to your project root:
   ```bash
   cp -r examples/.envlit /path/to/your/project/
   ```

2. **Load the default environment**:
   ```bash
   eval "$(envlit load)"
   ```

3. **Load a specific profile**:
   ```bash
   eval "$(envlit load --profile dev)"
   ```

4. **Use smart flags** (for `dev.yaml`):
   ```bash
   eval "$(envlit load --profile dev --cuda 2 --backend g)"
   ```

5. **Unload the environment**:
   ```bash
   eval "$(envlit unload)"
   ```

## Configuration Files

### `default.yaml`
Basic configuration with simple environment variables and hooks. Good starting point for learning envlit.

### `dev.yaml`
Development environment with:
- Smart flags for CUDA and backend selection
- PATH and PYTHONPATH modifications
- Development-specific hooks

### `prod.yaml`
Production environment with:
- Production-specific settings
- Security warnings
- Production API endpoints

## Configuration Structure

```yaml
# Smart Flags (optional)
flags:
  flag_name:
    flag: ["--flag", "-f"]
    default: "default_value"
    target: "ENV_VAR_NAME"

# Environment Variables
env:
  SIMPLE_VAR: "value"

  # Path operations
  PATH:
    - op: prepend
      value: "./bin"
    - op: remove
      value: "/old/path"

# Lifecycle Hooks (optional)
hooks:
  pre_load:
    - name: "Hook name"
      script: "echo 'Running...'"
  post_load: [...]
  pre_unload: [...]
  post_unload: [...]
```

## Features Demonstrated

### 1. Simple Variables (`default.yaml`)
```yaml
env:
  DEBUG: "true"
  LOG_LEVEL: "INFO"
```

### 2. Smart Flags (`dev.yaml`)
```yaml
flags:
  cuda:
    flag: ["--cuda", "-g"]
    default: "0"
    target: "CUDA_VISIBLE_DEVICES"
```

Usage: `eval "$(envlit load --profile dev --cuda 2)"`

### 3. Environment Variable Operations

**Simple values (shortcut for `op: set`):**
```yaml
env:
  PROJECT_MODE: "Development"
  DEBUG: "true"
```

**Explicit set operation:**
```yaml
env:
  API_URL:
    op: set
    value: "http://localhost:8000"
```

**Unset operation:**
```yaml
env:
  PRODUCTION_KEY:
    op: unset
```

**Single path operation:**
```yaml
env:
  PATH:
    op: prepend
    value: "./venv/bin"
```

**Pipeline of operations:**
```yaml
env:
  PATH:
    - op: remove
      value: "/old/path"
    - op: prepend
      value: "./bin"
    - op: append
      value: "/opt/bin"
```

### 4. Lifecycle Hooks (`all examples`)
Execute custom scripts before/after loading/unloading:
```yaml
hooks:
  post_load:
    - name: "Show status"
      script: "echo 'Environment ready!'"
```

## Best Practices

1. **Start Simple**: Begin with `default.yaml` and add complexity as needed
2. **Use Smart Flags**: For variables that change frequently during development
3. **Leverage Hooks**: For validation, notifications, or cleanup tasks
4. **Test Unload**: Always test that `envlit unload` correctly restores your environment
5. **Version Control**: Commit your `envlit/` directory to share with team

## Tips

- Use `export` in your shell profile for persistent access:
  ```bash
  # In ~/.bashrc or ~/.zshrc
  alias eload='eval "$(envlit load)"'
  alias eunload='eval "$(envlit unload)"'
  ```

- Multiple profiles for different scenarios:
  - `dev.yaml` - local development
  - `test.yaml` - testing environment
  - `prod.yaml` - production settings

- Check what envlit will do before applying:
  ```bash
  envlit load --profile dev  # See the generated script
  ```
