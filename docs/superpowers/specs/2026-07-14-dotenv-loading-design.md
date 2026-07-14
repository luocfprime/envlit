# Dotenv Loading Design

## Summary

Envlit will allow a YAML profile to explicitly import one or more dotenv files. Imported values become ordinary `env` entries, so the existing script generation, state tracking, consecutive-load behavior, and unload restoration continue to work without dotenv-specific branches.

The feature is explicit: envlit will not search for or automatically load `.env` files.

## Configuration

A profile may declare one dotenv file with a string:

```yaml
dotenv: "./.env"

env:
  DEBUG: "true"
```

It may declare multiple files with a list:

```yaml
dotenv:
  - "./.env"
  - "./.env.local"

env:
  DEBUG: "true"
```

An empty list is valid and loads nothing. Every entry must be a path string. Relative paths are resolved from the directory containing the YAML file that declares them; absolute paths are accepted unchanged.

## Parsing

Envlit will add `python-dotenv` as a runtime dependency and use `dotenv_values()` to parse each file. It will not use `load_dotenv()` and will not mutate the Python process environment while parsing configuration.

Python-dotenv interpolation will be disabled. Parsed values such as `${HOME}/bin` will flow through envlit's existing value interpolation behavior, keeping dotenv and YAML values consistent.

Parsing results have these semantics:

- `KEY=value` sets `KEY` to `value`.
- `KEY=` sets `KEY` to the empty string.
- A key without `=` is ignored with a warning.
- Invalid environment variable names are rejected by envlit's existing validation before a load script is emitted.

## Merge and Inheritance Order

Configuration is applied in layers. From lowest to highest precedence, each YAML file contributes:

1. Its fully resolved parent configuration, if declared with `extends`.
2. Its dotenv files in listed order.
3. Its own `env` section.

For example, the complete order for a child profile is:

```text
parent's parent layers
→ parent dotenv files
→ parent env
→ child dotenv files
→ child env
```

Therefore, a later dotenv file overrides an earlier dotenv file, YAML `env` overrides dotenv values in the same profile, and any child layer may override a value inherited from its parent.

After resolution, the public configuration retains the normal unified `env` mapping consumed by `generate_load_script()`. Dotenv values require no changes to script generation or state tracking.

## Override Warnings

Every cross-source replacement of an environment variable emits a `ConfigOverrideWarning` through Python's `warnings` mechanism. Warnings go to stderr, leaving stdout safe for the shell script produced by `envlit load`.

Warnings identify the variable and both sources, for example:

```text
ConfigOverrideWarning: API_URL from ".env.local" overrides value from ".env"
ConfigOverrideWarning: API_URL from "default.yaml:env" overrides value from ".env.local"
```

Warnings never include old or new values because dotenv files commonly contain secrets. An override is still applied after its warning. Repeated declarations within a single dotenv file follow `python-dotenv` parsing behavior and are not separately diagnosed by envlit; the feature tracks precedence between configuration sources, not individual source lines.

## Failure Behavior

A declared dotenv file is required. Envlit stops configuration loading and emits no shell script if a path:

- does not exist;
- is not a regular file;
- cannot be read; or
- cannot be parsed as dotenv content.

An invalid `dotenv` YAML value, such as a mapping or a list containing a non-string, is also a configuration error. Errors identify the declaring YAML file and offending dotenv path where applicable.

There is no optional-file syntax, silent override mode, or automatic dotenv discovery in the initial version.

## Internal Structure

Configuration loading will keep source information while recursively resolving a profile. A small internal representation will associate each resolved environment value with a safe source label. It is used only to enforce ordered merging and produce warnings; source metadata does not become part of the generated environment.

The loading flow is:

1. Parse and validate the YAML mapping.
2. Recursively resolve `extends`.
3. Normalize `dotenv` to a list of paths.
4. Parse and merge each dotenv file in order.
5. Merge the YAML `env` mapping.
6. Return the normalized config with the resolved `env` mapping.

Existing merging behavior for flags and hooks remains unchanged. Hooks retain parent-first list concatenation.

## Testing

Unit tests will cover:

- a single dotenv string;
- multiple dotenv files and ordered replacement;
- YAML `env` overriding dotenv;
- child dotenv overriding inherited YAML and child YAML overriding child dotenv;
- relative and absolute path resolution;
- empty dotenv lists and invalid `dotenv` shapes;
- missing, non-file, unreadable, and malformed dotenv inputs;
- empty assignments and entries without `=`;
- warnings emitted on stderr without values or other secret content;
- stdout containing only a valid generated shell script;
- invalid environment variable names; and
- end-to-end restoration of dotenv-loaded variables through `eul`.

Existing config, script-generation, and state tests must continue to pass for profiles that do not declare `dotenv`.
