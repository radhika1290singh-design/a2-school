# Skills

Custom slash commands and reusable task scripts for the a2-school project.

## Structure

Each skill is a markdown file that defines a reusable prompt or workflow.

```
skills/
  <skill-name>.md    # Skill definition file
```

## How to Add a Skill

Create a new `.md` file in this directory for reusable workflow documentation.

> **Note:** For commands that actually run as `/command-name` in Claude Code,
> place the `.md` file in `.claude/commands/` instead — that is the folder
> Claude Code reads for custom slash commands.
>
> Current slash commands: see [`../.claude/commands/`](../commands/)
