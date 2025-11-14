# Claude Code Documentation Mirror

This directory contains markdown files derived from the official Anthropic Claude Code documentation website (https://code.claude.com/docs).

## Structure

The directory hierarchy mirrors the top-level categories from the Claude Code web documentation:

- `01-getting-started/` - Overview, quickstart, common workflows, and web usage
- `02-build-with-claude-code/` - Subagents, plugins, skills, hooks, CI/CD integrations, etc.
- `03-deployment/` - Enterprise deployment options (Bedrock, Vertex AI, network config, etc.)
- `04-administration/` - Advanced admin, IAM, security, data usage, monitoring, costs, analytics
- `05-configuration/` - Settings, IDE integrations, terminal config, model config, memory
- `06-reference/` - CLI reference, interactive mode, slash commands, checkpointing, hooks, plugins

## How This Was Created

Each markdown file was created by:
1. Navigating to the corresponding page on the Claude Code documentation website
2. Using the "Copy page" link functionality (visible in the web UI)
3. Pasting the content into appropriately named markdown files in the mirrored directory structure

## Important Note About Links

**The markdown files contain web-style links that do not properly resolve to local files.**

For example, in `06-reference/01-cli-reference.md`, you'll find links like:
```markdown
[Interactive mode](/en/interactive-mode)
```

These links were copied directly from the web documentation and reference the web URL structure (`/en/interactive-mode`). However, the actual content **is present locally** in this directory structure. In the example above, the content is located at:
```
reference/claude-code/claude-code-docs/06-reference/02-interactive-mode.md
```

### Finding Linked Content

When you encounter a link like `/en/some-topic`:
1. The content exists in one of the numbered directories
2. Look for a file with a name matching the topic
3. The numbering (01-, 02-, etc.) is for organization and not part of the web URL

**Do not be confused by these broken internal links** - all the referenced content from the official documentation is present in these local files, just with a different file path structure.

## Purpose

This local mirror serves as a reference for understanding Claude Code's official features and capabilities without needing to access the web documentation.
