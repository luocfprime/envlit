# AI Agent Skill

Envlit provides a skill definition for Claude Code and OpenCode. With it installed, your AI assistant understands how to load/unload environment profiles, configure YAML flags, manage PATH operations, and debug state-tracking issues.

## Install

### Claude Code

**Via marketplace (recommended)**

```bash
/plugin marketplace add luocfprime/envlit
/plugin install envlit-skill@envlit
```

**Manual**

Copy `skills/envlit/SKILL.md` to `~/.claude/skills/envlit/SKILL.md`.

### OpenCode

Copy the skill to `.opencode/skills/envlit/SKILL.md`:

````markdown
--8<-- "skills/envlit/SKILL.md"
````
