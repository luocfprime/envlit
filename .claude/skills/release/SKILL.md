---
name: release
description: Bump the envlit version in pyproject.toml, commit, and publish a GitHub release with handwritten notes. Usage: /release <new-version>
argument-hint: "<new-version>"
---

## Release envlit

Argument: new version string (e.g. `0.0.7`).

### Steps

**1. Confirm version**

Read `pyproject.toml` to get the current version. Tell the user: current → new. Ask for confirmation before proceeding.

**2. Gather changes since last release**

```bash
# Get the previous release tag
PREV=$(gh release list --limit 1 --json tagName --jq '.[0].tagName')

# Fetch that tag locally so git log works
git fetch origin tag "$PREV" --no-tags 2>/dev/null || true

# List commits since then
git log "${PREV}..HEAD" --oneline
```

Read the commit list and write concise release notes in this format — focus on user-visible changes, group by type, omit chore/internal noise unless significant:

```markdown
## What's changed

### Features
- ...

### Fixes
- ...

### Docs
- ...
```

Omit any section that has nothing to list. Keep bullets short (one line each).

**3. Bump version**

Edit `pyproject.toml`: replace `version = "<old>"` with `version = "<new>"`.

**4. Commit and push**

```bash
git add pyproject.toml
git commit -m "chore: bump version to <new>"
git push
```

**5. Publish release**

```bash
gh release create v<new> \
  --title "v<new>" \
  --notes "<release notes markdown>"
```

Return the release URL to the user.
