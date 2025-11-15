# About CLAUDE.md Files

## What These Files Are

**CLAUDE.md files are context files maintained by Claude Code as part of the codebase.**

These files:
- Are automatically loaded by Claude Code at session startup
- Contain instructions, conventions, and project context
- Guide Claude Code's behavior when working in this codebase
- Are loaded on-demand when reading files in subdirectories
- **Are written and maintained by Claude Code**, guided by user direction

**Key Point:** These are part of the codebase that Claude Code maintains, serving as living documentation of project conventions and current understanding.

## How They Work

When Claude Code starts a session or reads a file:
1. It loads the nearest CLAUDE.md file in the directory hierarchy
2. Uses the content as context for understanding project conventions
3. Follows the instructions and patterns defined in the file
4. Updates these files as understanding evolves

**Example:** If `backend/CLAUDE.md` says "always use async/await", Claude Code will prefer async patterns when working in backend code.

## File Organization for This Project

```
claudia/
├── CLAUDE.md              # Project-level overview, core principles, status
├── CLAUDE_ABOUT.md        # This file - explains what CLAUDE.md files are
├── backend/CLAUDE.md      # Backend-specific conventions (logging, errors, DB)
├── frontend/CLAUDE.md     # Frontend-specific conventions (Vue, TypeScript, tokens)
└── hooks/CLAUDE.md        # Hook development conventions and workflows
```

## Important: These Files Can Be Wrong

**CLAUDE.md files reflect Claude Code's current understanding, which can be incorrect.**

Examples from this project:
- Initially documented that "each session has unique session_id"
- This was WRONG - session_id actually persists across `--continue`
- The file was updated when the mistake was discovered

**Therefore:**
- CLAUDE.md content should be validated against actual behavior
- When contradictions are found, investigate and update the files
- These files are living documentation that evolves with the project

## Maintenance

**Claude Code maintains these files by:**
- Updating them when directed by the user
- Correcting mistakes when discovered
- Adding new conventions as the project evolves
- Documenting current implementation status
- Removing outdated information

**User's role:**
- Guides the content and direction
- Points out errors or misunderstandings
- Requests updates when conventions change

## What to Include

- Clear, specific instructions (not vague guidance)
- Current project status and implementation state
- Conventions and patterns specific to this codebase
- Anti-patterns to avoid (what NOT to do)
- Known issues or areas of uncertainty

## What NOT to Include

- Setup instructions (those go in README.md)
- API documentation (those go in docs/)
- General programming knowledge
- Information that changes frequently (like current git commit)

## Best Practices

1. **Be Specific:** "Use `unknown` instead of `any`" is better than "Use good TypeScript practices"

2. **State Current Status:** Clearly indicate what's implemented vs. planned

3. **Include Examples:** Show concrete examples of patterns to follow or avoid

4. **Update When Wrong:** Don't perpetuate mistakes - fix them immediately

5. **Organize by Concern:** Keep project-level concerns in root CLAUDE.md, domain-specific concerns in subdirectory CLAUDE.md files

## Reference

For official Claude Code documentation, see:
- `reference/claude-code/` - Official docs mirror
- https://code.claude.com/docs - Official web documentation
